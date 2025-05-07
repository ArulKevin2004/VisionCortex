import React, { useState } from 'react';
import RegisterTab from './components/RegisterTab';
import RecognitionTab from './components/RecognitionTab';
import ChatTab from './components/ChatTab';
import './styles.css';

const TABS = ['register', 'recognition', 'chat'];

const App = () => {
  const [activeTab, setActiveTab] = useState('register');
  const activeIndex = TABS.indexOf(activeTab);

  return (
    <div className="min-h-screen bg-white flex flex-col items-center ">
      {/* Navbar */}
      <nav className="w-full shadow-md bg-blue-600 py-4 mb-6 fixed top-0 z-20">
        <div className="max-w-5xl mx-auto px-4 flex items-center justify-between">
          <h1 className="text-3xl text-white">Vision<span className='font-bold italic font-cursive'>Cortex</span></h1>
        </div>
      </nav>

      {/* Push content down to not go under navbar */}
      <div className="mt-24 w-full flex flex-col items-center px-4">
        {/* Tabs Section */}
        <div className="w-full max-w-md">
          <div className="relative flex bg-gray-200 rounded-lg overflow-hidden">
            {/* Blue sliding highlight */}
            <div
              className="absolute top-0 left-0 w-1/3 h-full bg-blue-500 transition-transform duration-300"
              style={{ transform: `translateX(${activeIndex * 100}%)` }}
            />
            {/* Tab buttons */}
            {TABS.map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`relative z-10 w-1/3 py-3 text-center font-semibold transition-colors ${
                  activeTab === tab ? 'text-white' : 'text-black'
                }`}
              >
                {tab.charAt(0).toUpperCase() + tab.slice(1)}
              </button>
            ))}
          </div>
        </div>

        {/* Tab Content */}
        <div className="mt-8 w-full max-w-4xl transition-opacity duration-300">
          {activeTab === 'register' && <RegisterTab />}
          {activeTab === 'recognition' && <RecognitionTab />}
          {activeTab === 'chat' && <ChatTab />}
        </div>
      </div>
    </div>
  );
};

export default App;
