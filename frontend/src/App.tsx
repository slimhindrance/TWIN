/**
 * Main App component
 */
import React, { useState } from 'react';
import ChatInterface from './components/Chat/ChatInterface';
import SearchInterface from './components/Search/SearchInterface';
import SettingsModal from './components/Settings/SettingsModal';

function App() {
  const [showSearch, setShowSearch] = useState(false);
  const [showSettings, setShowSettings] = useState(false);

  return (
    <div className="h-screen flex flex-col bg-gray-100">
      <main className="flex-1 overflow-hidden">
        <ChatInterface
          onOpenSettings={() => setShowSettings(true)}
          onOpenSearch={() => setShowSearch(true)}
        />
      </main>

      {showSearch && (
        <SearchInterface onClose={() => setShowSearch(false)} />
      )}

      {showSettings && (
        <SettingsModal onClose={() => setShowSettings(false)} />
      )}
    </div>
  );
}

export default App;