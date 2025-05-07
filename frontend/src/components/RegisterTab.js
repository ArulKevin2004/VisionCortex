import React, { useState } from 'react';
import axios from 'axios';

const RegisterTab = () => {
  const [name, setName] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);

  const handleRegister = async () => {
    if (!name) {
      setMessage('Please enter a name');
      return;
    }
    setLoading(true);
    setMessage('');
    try {
      console.log('Sending register request for:', name);
      const response = await axios.post('http://localhost:5001/api/register', { name });
      setMessage(response.data.message);
    } catch (error) {
      console.error('Register error:', error);
      if (error.response) {
        setMessage(`Registration failed: ${error.response.data.error || 'Unknown server error'}`);
      } else if (error.request) {
        setMessage('Backend server not responding. Is the Node.js server running on port 5001?');
      } else {
        setMessage(`Registration failed: ${error.message}`);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-4 bg-gray-100 rounded-xl shadow">
      <h2 className="text-xl font-semibold mb-4">Register Face</h2>
      <input
        type="text"
        value={name}
        onChange={(e) => setName(e.target.value)}
        placeholder="Enter name"
        className="border p-2 mb-4 w-full rounded-lg"
      />
      <button
        onClick={handleRegister}
        disabled={loading}
        className={`bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
      >
        {loading ? 'Registering...' : 'Register'}
      </button>
      {message && <p className={`mt-4 ${message.includes('failed') ? 'text-red-600' : 'text-green-600'}`}>{message}</p>}
    </div>
  );
};

export default RegisterTab;