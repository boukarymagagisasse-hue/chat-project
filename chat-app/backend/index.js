const express = require('express');
const http = require('http');
const { Server } = require('socket.io');
const cors = require('cors');
const fs = require('fs');
let Pool;
try { Pool = require('pg').Pool } catch(e) {}

const app = express();
app.use(cors());
app.use(express.json());

const server = http.createServer(app);
const io = new Server(server, { cors: { origin: "*" } });

// --- DB CONFIG (pour le prof) ---
let pool = null;
let usePG = false;
if (Pool) {
  try {
    pool = new Pool({
      connectionString: process.env.DATABASE_URL || 'postgresql://postgres:postgres@localhost:5432/xacan',
    });
    pool.query('SELECT 1').then(()=>{ usePG=true; console.log('PostgreSQL connecté'); initPG(); }).catch(()=> console.log('PostgreSQL pas trouvé, mode JSON'));
  } catch(e) {}
}

async function initPG(){
  await pool.query(`CREATE TABLE IF NOT EXISTS messages (id SERIAL PRIMARY KEY, channel TEXT, username TEXT, text TEXT, created_at TIMESTAMP DEFAULT NOW())`);
  await pool.query(`CREATE TABLE IF NOT EXISTS channels (name TEXT PRIMARY KEY)`);
}

const CHANNELS_FILE = './data.json';
function loadData(){
  try { return JSON.parse(fs.readFileSync(CHANNELS_FILE)); } 
  catch { return { channels: ['general','random'], messages: {} } }
}
function saveData(data){ 
  if(!fs.existsSync('./')) fs.mkdirSync('./');
  fs.writeFileSync(CHANNELS_FILE, JSON.stringify(data)); 
}

let store = loadData();

app.get('/channels', async (req,res)=>{
  if(usePG){ const r = await pool.query('SELECT name FROM channels'); res.json(r.rows.map(x=>x.name)); }
  else res.json(store.channels);
});

app.get('/messages/:channel', async (req,res)=>{
  const ch = req.params.channel;
  if(usePG){ const r = await pool.query('SELECT * FROM messages WHERE channel=$1 ORDER BY id ASC', [ch]); res.json(r.rows); }
  else res.json(store.messages[ch] || []);
});

io.on('connection', socket=>{
  console.log('user connected');
  socket.on('joinChannel', ch=> socket.join(ch));
  socket.on('sendMessage', async (data)=>{
    const msg = { channel: data.channel, username: data.username||'Anon', text: data.text, created_at: new Date() };
    if(usePG){ await pool.query('INSERT INTO messages(channel,username,text) VALUES($1,$2,$3)', [msg.channel, msg.username, msg.text]); }
    else { 
      if(!store.messages[msg.channel]) store.messages[msg.channel]=[];
      store.messages[msg.channel].push(msg);
      saveData(store);
    }
    io.to(data.channel).emit('newMessage', msg);
  });
});

const PORT = process.env.PORT || 3000;
server.listen(PORT, '0.0.0.0', ()=> console.log(`Backend XACAN sur port ${PORT}`));