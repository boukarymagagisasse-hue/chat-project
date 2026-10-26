import { useState, useEffect } from 'react';
import io from 'socket.io-client';
import './App.css';

const socket = io('http://localhost:3000');
const CHANNELS = ['#general', '#dev', '#random', '#xacan-project'];

function App() {
  const [currentChannel, setCurrentChannel] = useState('#general');
  const [messages, setMessages] = useState({});
  const [input, setInput] = useState('');

  useEffect(() => {
    socket.emit('join', currentChannel);
    const handleMessage = (msg) => {
      setMessages(prev => ({
        ...prev,
        [msg.channel]: [...(prev[msg.channel] || []), msg]
      }));
    };
    socket.on('chat message', handleMessage);
    return () => socket.off('chat message', handleMessage);
  }, [currentChannel]);

  const changeChannel = (ch) => {
    socket.emit('join', ch);
    setCurrentChannel(ch);
  };

  const sendMessage = (e) => {
    e.preventDefault();
    if(input.trim()){
      socket.emit('chat message', { text: input, channel: currentChannel, user: 'Hassan' });
      setInput('');
    }
  };

  return (
    <div className="app">
      <div className="sidebar">
        <h2>XACAN Chat</h2>
        {CHANNELS.map(ch => (
          <div key={ch} className={currentChannel === ch ? 'channel active' : 'channel'} onClick={() => changeChannel(ch)}>
            {ch}
          </div>
        ))}
      </div>
      <div className="chat">
        <div className="header">{currentChannel}</div>
        <div className="messages">
          {(messages[currentChannel] || []).map((m,i) => <div key={i} className="msg"><b>{m.user}: </b>{m.text}</div>)}
        </div>
        <form onSubmit={sendMessage} className="input-area">
          <input value={input} onChange={e=>setInput(e.target.value)} placeholder={`Message ${currentChannel}`} />
          <button>Envoyer</button>
        </form>
      </div>
    </div>
  );
}
export default App;