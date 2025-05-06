import React, { useState, useEffect } from 'react';

// Module-level variable to store chat history until browser refresh
let chatHistoryStorage = [];

const ChatTab = () => {
  const [ws, setWs] = useState(null);
  const [message, setMessage] = useState('');
  const [chatHistory, setChatHistory] = useState(chatHistoryStorage); // Initialize with persisted history
  const [error, setError] = useState('');

  // Initialize WebSocket connection
  useEffect(() => {
    const websocket = new WebSocket('ws://localhost:5001');
    
    websocket.onopen = () => {
      console.log('WebSocket connected');
      setWs(websocket);
    };

    websocket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      chatHistoryStorage = [...chatHistoryStorage, { type: 'response', text: data.message }];
      setChatHistory(chatHistoryStorage);
    };

    websocket.onerror = (error) => {
      console.error('WebSocket error:', error);
      setError('Failed to connect to the chat server.');
    };

    websocket.onclose = () => {
      console.log('WebSocket disconnected');
      setWs(null);
    };

    return () => {
      websocket.close();
    };
  }, []);

  const handleSendMessage = () => {
    if (!ws) {
      setError('Not connected to the chat server.');
      return;
    }
    if (!message.trim()) {
      setError('Please enter a message.');
      return;
    }
    ws.send(message);
    chatHistoryStorage = [...chatHistoryStorage, { type: 'sent', text: message }];
    setChatHistory(chatHistoryStorage);
    setMessage('');
    setError('');
  };

  return (
    <div className="p-4 bg-gray-100 rounded shadow">
      <h2 className="text-xl font-semibold mb-4">Chat with AI</h2>
      <div className="chat-box border p-4 h-64 overflow-y-auto mb-4 bg-white rounded">
        {chatHistory.map((chat, index) => (
          <div
            key={index}
            className={`mb-2 ${chat.type === 'sent' ? 'text-right' : 'text-left'}`}
          >
            <span
              className={`inline-block p-2 rounded ${
                chat.type === 'sent' ? 'bg-blue-500 text-white' : 'bg-gray-300'
              }`}
            >
              {chat.text}
            </span>
          </div>
        ))}
      </div>
      {error && <p className="text-red-600 mb-4">{error}</p>}
      <div className="flex gap-2">
        <input
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Ask a question (e.g., How many people are registered?)"
          className="border p-2 flex-1 rounded"
          onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
        />
        <button
          onClick={handleSendMessage}
          className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
        >
          Send
        </button>
      </div>
    </div>
  );
};

export default ChatTab;