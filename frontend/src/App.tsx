import React, { useState } from 'react';
import './App.css';
import { AuthProvider, useAuth } from './context/AuthContext';
import { LoginForm } from './components/Auth/LoginForm';
import { RegisterForm } from './components/Auth/RegisterForm';
import ChatInterface from './components/Chat/ChatInterface';
import SearchInterface from './components/Search/SearchInterface';
import SettingsModal from './components/Settings/SettingsModal';
import SourcesManager from './components/Sources/SourcesManager';
import { MessageSquare, Search, Settings, LogOut, User, Database } from 'lucide-react';

// Main App Content (requires auth)
const AppContent: React.FC = () => {
  const { user, logout } = useAuth();
  const [currentView, setCurrentView] = useState<'chat' | 'search' | 'sources'>('chat');
  const [showSettings, setShowSettings] = useState(false);

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Logo */}
            <div className="flex items-center">
              <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg mr-3"></div>
              <h1 className="text-xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                Total Life AI
              </h1>
            </div>

            {/* Navigation */}
            <nav className="flex items-center space-x-4">
              <button
                onClick={() => setCurrentView('chat')}
                className={`flex items-center px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  currentView === 'chat'
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
                }`}
              >
                <MessageSquare className="w-4 h-4 mr-2" />
                Chat
              </button>
              <button
                onClick={() => setCurrentView('search')}
                className={`flex items-center px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  currentView === 'search'
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
                }`}
              >
                <Search className="w-4 h-4 mr-2" />
                Search
              </button>
              <button
                onClick={() => setCurrentView('sources')}
                className={`flex items-center px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  currentView === 'sources'
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
                }`}
              >
                <Database className="w-4 h-4 mr-2" />
                Data Sources
              </button>
            </nav>

            {/* User Menu */}
            <div className="flex items-center space-x-4">
              <div className="flex items-center text-sm text-gray-700">
                <User className="w-4 h-4 mr-2" />
                {user?.username}
              </div>
              <button
                onClick={() => setShowSettings(true)}
                className="p-2 rounded-md text-gray-500 hover:text-gray-700 hover:bg-gray-100"
              >
                <Settings className="w-5 h-5" />
              </button>
              <button
                onClick={logout}
                className="p-2 rounded-md text-gray-500 hover:text-gray-700 hover:bg-gray-100"
              >
                <LogOut className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 overflow-hidden">
        {currentView === 'chat' && <ChatInterface />}
        {currentView === 'search' && (
          <SearchInterface onClose={() => setCurrentView('chat')} />
        )}
        {currentView === 'sources' && <SourcesManager />}
      </main>

      {/* Settings Modal */}
      {showSettings && (
        <SettingsModal onClose={() => setShowSettings(false)} />
      )}
    </div>
  );
};

// Auth wrapper component
const AuthenticatedApp: React.FC = () => {
  const { isAuthenticated, loading, login, register } = useAuth();
  const [authMode, setAuthMode] = useState<'login' | 'register'>('login');

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-600 to-purple-600 flex items-center justify-center">
        <div className="text-white text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto mb-4"></div>
          <p>Loading Digital Twin...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    if (authMode === 'login') {
      return (
        <LoginForm
          onLogin={login}
          onSwitchToRegister={() => setAuthMode('register')}
          loading={loading}
        />
      );
    } else {
      return (
        <RegisterForm
          onRegister={register}
          onSwitchToLogin={() => setAuthMode('login')}
          loading={loading}
        />
      );
    }
  }

  return <AppContent />;
};

// Root App component
const App: React.FC = () => {
  return (
    <AuthProvider>
      <AuthenticatedApp />
    </AuthProvider>
  );
};

export default App;
