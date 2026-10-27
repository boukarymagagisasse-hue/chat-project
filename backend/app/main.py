from __future__ import annotations

import asyncio
import json
import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent.parent
STATIC_DIR = ROOT / "static"
DB_PATH = ROOT / "chat.db"


def connect_db() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_db() -> None:
    with connect_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id INTEGER NOT NULL,
                username TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(channel_id) REFERENCES channels(id) ON DELETE CASCADE
            )
        """)
        for name in ("Général", "Annonces", "Questions"):
            db.execute("INSERT OR IGNORE INTO channels(name) VALUES (?)", (name,))
        db.commit()


class ChannelCreate(BaseModel):
    name: str = Field(min_length=2, max_length=40)


class MessageCreate(BaseModel):
    username: str = Field(min_length=1, max_length=24)
    content: str = Field(min_length=1, max_length=2000)


class ConnectionManager:
    def __init__(self) -> None:
        self.connections: dict[int, set[WebSocket]] = {}
        self.lock = asyncio.Lock()

    async def connect(self, channel_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self.lock:
            self.connections.setdefault(channel_id, set()).add(websocket)

    async def disconnect(self, channel_id: int, websocket: WebSocket) -> None:
        async with self.lock:
            sockets = self.connections.get(channel_id)
            if sockets:
                sockets.discard(websocket)
                if not sockets:
                    self.connections.pop(channel_id, None)

    async def broadcast(self, channel_id: int, payload: dict[str, Any]) -> None:
        async with self.lock:
            sockets = list(self.connections.get(channel_id, set()))
        stale: list[WebSocket] = []
        for socket in sockets:
            try:
                await socket.send_json(payload)
            except Exception:
                stale.append(socket)
        for socket in stale:
            await self.disconnect(channel_id, socket)


manager = ConnectionManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_db()
    yield


app = FastAPI(title="Chat Project API", version="1.0.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return dict(row)


def get_channel(channel_id: int) -> dict[str, Any]:
    with connect_db() as db:
        row = db.execute("SELECT * FROM channels WHERE id = ?", (channel_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Canal introuvable")
    return row_to_dict(row)


@app.get("/", include_in_schema=False)
def home():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
def health():
    return {"status": "ok", "message": "Le serveur de chat fonctionne."}


@app.get("/api/channels")
def list_channels():
    with connect_db() as db:
        rows = db.execute("""
            SELECT c.id, c.name, c.created_at,
                   (SELECT COUNT(*) FROM messages m WHERE m.channel_id = c.id) AS message_count
            FROM channels c ORDER BY c.id
        """).fetchall()
    return [row_to_dict(row) for row in rows]


@app.post("/api/channels", status_code=201)
def create_channel(payload: ChannelCreate):
    name = payload.name.strip()
    if len(name) < 2:
        raise HTTPException(status_code=400, detail="Le nom doit contenir au moins 2 caractères.")
    try:
        with connect_db() as db:
            cursor = db.execute("INSERT INTO channels(name) VALUES (?)", (name,))
            db.commit()
            row = db.execute("SELECT * FROM channels WHERE id = ?", (cursor.lastrowid,)).fetchone()
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="Ce canal existe déjà.")
    return row_to_dict(row)


@app.get("/api/channels/{channel_id}/messages")
def list_messages(channel_id: int, limit: int = 100):
    get_channel(channel_id)
    limit = max(1, min(limit, 200))
    with connect_db() as db:
        rows = db.execute("""
            SELECT id, channel_id, username, content, created_at
            FROM messages WHERE channel_id = ?
            ORDER BY id DESC LIMIT ?
        """, (channel_id, limit)).fetchall()
    return [row_to_dict(row) for row in reversed(rows)]


@app.post("/api/channels/{channel_id}/messages", status_code=201)
async def create_message(channel_id: int, payload: MessageCreate):
    get_channel(channel_id)
    username = payload.username.strip()[:24] or "Invité"
    content = payload.content.strip()
    if not content:
        raise HTTPException(status_code=400, detail="Le message ne peut pas être vide.")
    with connect_db() as db:
        cursor = db.execute(
            "INSERT INTO messages(channel_id, username, content) VALUES (?, ?, ?)",
            (channel_id, username, content),
        )
        db.commit()
        row = db.execute("""
            SELECT id, channel_id, username, content, created_at
            FROM messages WHERE id = ?
        """, (cursor.lastrowid,)).fetchone()
    message = row_to_dict(row)
    await manager.broadcast(channel_id, {"type": "message", "message": message})
    return message


@app.websocket("/ws/channels/{channel_id}")
async def channel_socket(websocket: WebSocket, channel_id: int):
    try:
        get_channel(channel_id)
    except HTTPException:
        await websocket.close(code=1008, reason="Canal introuvable")
        return
    await manager.connect(channel_id, websocket)
    try:
        while True:
            # Keep the connection open; messages are sent through the REST endpoint.
            await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(channel_id, websocket)
    except Exception:
        await manager.disconnect(channel_id, websocket)
