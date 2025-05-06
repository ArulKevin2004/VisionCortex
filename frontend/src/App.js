import React, { useState } from 'react';
import RegisterTab from './components/RegisterTab';
import RecognitionTab from './components/RecognitionTab';
import './styles.css';

const App = () => {
  const [activeTab, setActiveTab] = useState('register');

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-3xl font-bold text-center mb-4">CogniVision</h1>
      <div className="tabs flex justify-center mb-4">
        <button
          className={`px-4 py-2 ${activeTab === 'register' ? 'bg-blue-500 text-white' : 'bg-gray-200'}`}
          onClick={() => setActiveTab('register')}
        >
          Register
        </button>
        <button
          className={`px-4 py-2 ${activeTab === 'recognition' ? 'bg-blue-500 text-white' : 'bg-gray-200'}`}
          onClick={() => setActiveTab('recognition')}
        >
          Recognition
        </button>
      </div>
      {activeTab === 'register' && <RegisterTab />}
      {activeTab === 'recognition' && <RecognitionTab />}
    </div>
  );
};

export default App;