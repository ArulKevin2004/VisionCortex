import React, { useState } from 'react';
import axios from 'axios';

const RecognitionTab = () => {
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);

  const handleRecognize = async () => {
    setLoading(true);
    setMessage('');
    try {
      console.log('Sending recognize request');
      const response = await axios.get('http://localhost:5001/api/recognize');
      setMessage(response.data.message);
    } catch (error) {
      console.error('Recognize error:', error);
      if (error.response) {
        setMessage(`Recognition failed: ${error.response.data.error || 'Unknown server error'}`);
      } else if (error.request) {
        setMessage('Backend server not responding. Is the Node.js server running on port 5001?');
      } else {
        setMessage(`Recognition failed: ${error.message}`);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-4 bg-gray-100 rounded shadow">
      <h2 className="text-xl font-semibold mb-4">Live Recognition</h2>
      <button
        onClick={handleRecognize}
        disabled={loading}
        className={`bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
      >
        {loading ? 'Starting...' : 'Start Recognition'}
      </button>
      {message && <p className={`mt-4 ${message.includes('failed') ? 'text-red-600' : 'text-green-600'}`}>{message}</p>}
    </div>
  );
};

export default RecognitionTab;