/**
 * Settings modal for configuring the Digital Twin application
 */
import React, { useState, useEffect } from 'react';
import { X, Settings, FolderOpen, RefreshCw, CheckCircle, AlertCircle, Play, Square, Link, ExternalLink, Trash2, Plus } from 'lucide-react';
import { ApiService, VaultSyncStatus, HealthCheck, SourceStatus, SupportedSource } from '../../services/api';

interface SettingsModalProps {
  onClose: () => void;
}

const SettingsModal: React.FC<SettingsModalProps> = ({ onClose }) => {
  const [activeTab, setActiveTab] = useState<'sources' | 'sync' | 'health' | 'about'>('sources');
  const [syncStatus, setSyncStatus] = useState<VaultSyncStatus | null>(null);
  const [health, setHealth] = useState<HealthCheck | null>(null);
  const [sources, setSources] = useState<SourceStatus[]>([]);
  const [supportedSources, setSupportedSources] = useState<SupportedSource[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [message, setMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);
  
  // Connection forms state
  const [showNotionForm, setShowNotionForm] = useState(false);
  const [showObsidianForm, setShowObsidianForm] = useState(false);
  const [notionToken, setNotionToken] = useState('');
  const [obsidianPath, setObsidianPath] = useState('');
  const [isConnecting, setIsConnecting] = useState(false);

  useEffect(() => {
    loadStatus();
    loadSources();
  }, []);

  const loadStatus = async () => {
    try {
      setIsLoading(true);
      const [syncResponse, healthResponse] = await Promise.all([
        ApiService.getVaultSyncStatus().catch(() => null),
        ApiService.getHealth().catch(() => null),
      ]);
      setSyncStatus(syncResponse);
      setHealth(healthResponse);
    } catch (error) {
      console.error('Failed to load status:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const loadSources = async () => {
    try {
      const [sourcesResponse, supportedResponse] = await Promise.all([
        ApiService.getSourcesStatus().catch(() => []),
        ApiService.getSupportedSources().catch(() => ({ sources: [] })),
      ]);
      setSources(sourcesResponse);
      setSupportedSources(supportedResponse.sources);
    } catch (error) {
      console.error('Failed to load sources:', error);
    }
  };

  const showMessage = (text: string, type: 'success' | 'error') => {
    setMessage({ text, type });
    setTimeout(() => setMessage(null), 5000);
  };

  const handleConnectNotion = async () => {
    if (!notionToken.trim()) {
      showMessage('Please enter your Notion API token', 'error');
      return;
    }

    try {
      setIsConnecting(true);
      await ApiService.connectNotion({ notion_api_token: notionToken.trim() });
      showMessage('Notion workspace connected successfully!', 'success');
      setShowNotionForm(false);
      setNotionToken('');
      await loadSources();
    } catch (error: any) {
      showMessage(error.response?.data?.detail || 'Failed to connect Notion workspace', 'error');
    } finally {
      setIsConnecting(false);
    }
  };

  const handleConnectObsidian = async () => {
    if (!obsidianPath.trim()) {
      showMessage('Please enter your Obsidian vault path', 'error');
      return;
    }

    try {
      setIsConnecting(true);
      await ApiService.connectObsidian({ vault_path: obsidianPath.trim() });
      showMessage('Obsidian vault connected successfully!', 'success');
      setShowObsidianForm(false);
      setObsidianPath('');
      await loadSources();
    } catch (error: any) {
      showMessage(error.response?.data?.detail || 'Failed to connect Obsidian vault', 'error');
    } finally {
      setIsConnecting(false);
    }
  };

  const handleDisconnectSource = async (sourceType: string) => {
    try {
      await ApiService.disconnectSource(sourceType);
      showMessage(`${sourceType} disconnected successfully`, 'success');
      await loadSources();
    } catch (error: any) {
      showMessage(error.response?.data?.detail || `Failed to disconnect ${sourceType}`, 'error');
    }
  };

  const handleSyncAllSources = async () => {
    try {
      await ApiService.syncAllSources();
      showMessage('Sync started for all knowledge sources', 'success');
      setTimeout(loadSources, 2000);
    } catch (error: any) {
      showMessage(error.response?.data?.detail || 'Failed to start sync', 'error');
    }
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Never';
    return new Date(dateString).toLocaleString();
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'text-green-600';
      case 'degraded': return 'text-yellow-600';
      case 'unhealthy': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy': return <CheckCircle className="w-4 h-4" />;
      case 'degraded': return <AlertCircle className="w-4 h-4" />;
      case 'unhealthy': return <AlertCircle className="w-4 h-4" />;
      default: return <AlertCircle className="w-4 h-4" />;
    }
  };

  const getSourceIcon = (sourceType: string) => {
    switch (sourceType) {
      case 'notion': return '🎯';
      case 'obsidian': return '💎';
      default: return '📄';
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-5xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center space-x-3">
            <Settings className="w-6 h-6 text-digital-purple" />
            <h2 className="text-xl font-semibold text-gray-900">Settings</h2>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-gray-600 rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Message */}
        {message && (
          <div className={`mx-6 mt-4 p-3 rounded-lg ${
            message.type === 'success' ? 'bg-green-50 text-green-800 border border-green-200' : 
            'bg-red-50 text-red-800 border border-red-200'
          }`}>
            {message.text}
          </div>
        )}

        <div className="flex flex-1 overflow-hidden">
          {/* Sidebar */}
          <div className="w-64 bg-gray-50 border-r border-gray-200 p-4">
            <nav className="space-y-2">
              <button
                onClick={() => setActiveTab('sources')}
                className={`w-full text-left px-3 py-2 rounded-lg transition-colors ${
                  activeTab === 'sources' ? 'bg-digital-purple text-white' : 'text-gray-700 hover:bg-gray-100'
                }`}
              >
                <div className="flex items-center space-x-2">
                  <Link className="w-4 h-4" />
                  <span>Knowledge Sources</span>
                </div>
              </button>
              <button
                onClick={() => setActiveTab('sync')}
                className={`w-full text-left px-3 py-2 rounded-lg transition-colors ${
                  activeTab === 'sync' ? 'bg-digital-purple text-white' : 'text-gray-700 hover:bg-gray-100'
                }`}
              >
                Vault Synchronization
              </button>
              <button
                onClick={() => setActiveTab('health')}
                className={`w-full text-left px-3 py-2 rounded-lg transition-colors ${
                  activeTab === 'health' ? 'bg-digital-purple text-white' : 'text-gray-700 hover:bg-gray-100'
                }`}
              >
                Health Status
              </button>
              <button
                onClick={() => setActiveTab('about')}
                className={`w-full text-left px-3 py-2 rounded-lg transition-colors ${
                  activeTab === 'about' ? 'bg-digital-purple text-white' : 'text-gray-700 hover:bg-gray-100'
                }`}
              >
                About
              </button>
            </nav>
          </div>

          {/* Content */}
          <div className="flex-1 p-6 overflow-y-auto">
            {isLoading ? (
              <div className="flex items-center justify-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-digital-purple"></div>
              </div>
            ) : (
              <>
                {activeTab === 'sources' && (
                  <div className="space-y-6">
                    <div className="flex items-center justify-between">
                      <h3 className="text-lg font-semibold text-gray-900">Knowledge Sources</h3>
                      <button
                        onClick={handleSyncAllSources}
                        className="flex items-center space-x-2 px-4 py-2 bg-digital-purple text-white rounded-lg hover:bg-indigo-700 transition-colors"
                      >
                        <RefreshCw className="w-4 h-4" />
                        <span>Sync All</span>
                      </button>
                    </div>

                    {/* Connected Sources */}
                    <div className="space-y-4">
                      <h4 className="font-medium text-gray-900">Connected Sources</h4>
                      
                      {sources.filter(s => s.connected).length === 0 ? (
                        <div className="text-center py-8 text-gray-500">
                          <Link className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                          <p>No knowledge sources connected yet</p>
                          <p className="text-sm">Connect your first source below to get started</p>
                        </div>
                      ) : (
                        <div className="grid gap-4 md:grid-cols-2">
                          {sources.filter(s => s.connected).map((source) => (
                            <div key={source.type} className="border border-gray-200 rounded-lg p-4">
                              <div className="flex items-start justify-between mb-3">
                                <div className="flex items-center space-x-3">
                                  <span className="text-2xl">{getSourceIcon(source.type)}</span>
                                  <div>
                                    <h5 className="font-medium capitalize">{source.type}</h5>
                                    <p className="text-sm text-gray-600">
                                      {source.document_count} document{source.document_count !== 1 ? 's' : ''}
                                    </p>
                                  </div>
                                </div>
                                <button
                                  onClick={() => handleDisconnectSource(source.type)}
                                  className="p-1 text-gray-400 hover:text-red-600 transition-colors"
                                  title="Disconnect"
                                >
                                  <Trash2 className="w-4 h-4" />
                                </button>
                              </div>
                              
                              <div className="flex items-center space-x-2">
                                <CheckCircle className="w-4 h-4 text-green-600" />
                                <span className="text-sm text-green-600">Connected</span>
                              </div>
                              
                              {source.last_synced && (
                                <p className="text-xs text-gray-500 mt-1">
                                  Last synced: {formatDate(source.last_synced)}
                                </p>
                              )}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Available Sources to Connect */}
                    <div className="space-y-4">
                      <h4 className="font-medium text-gray-900">Available Sources</h4>
                      
                      <div className="grid gap-4 md:grid-cols-2">
                        {supportedSources.map((source) => {
                          const isConnected = sources.some(s => s.type === source.type && s.connected);
                          
                          return (
                            <div key={source.type} className="border border-gray-200 rounded-lg p-4">
                              <div className="flex items-center space-x-3 mb-3">
                                <span className="text-2xl">{getSourceIcon(source.type)}</span>
                                <div>
                                  <h5 className="font-medium">{source.name}</h5>
                                  <p className="text-sm text-gray-600">{source.description}</p>
                                </div>
                              </div>
                              
                              <div className="flex items-center justify-between">
                                <div className="flex items-center space-x-2">
                                  <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full">
                                    FREE
                                  </span>
                                  {source.setup_url && (
                                    <a
                                      href={source.setup_url}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="text-xs text-blue-600 hover:underline flex items-center space-x-1"
                                    >
                                      <span>Setup Guide</span>
                                      <ExternalLink className="w-3 h-3" />
                                    </a>
                                  )}
                                </div>
                                
                                {!isConnected ? (
                                  <button
                                    onClick={() => {
                                      if (source.type === 'notion') setShowNotionForm(true);
                                      if (source.type === 'obsidian') setShowObsidianForm(true);
                                    }}
                                    className="flex items-center space-x-1 px-3 py-1 bg-digital-purple text-white text-sm rounded hover:bg-indigo-700 transition-colors"
                                  >
                                    <Plus className="w-3 h-3" />
                                    <span>Connect</span>
                                  </button>
                                ) : (
                                  <span className="text-sm text-green-600">✓ Connected</span>
                                )}
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>

                    {/* Connection Forms */}
                    {showNotionForm && (
                      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-10">
                        <div className="bg-white rounded-lg p-6 w-full max-w-md">
                          <h4 className="font-semibold mb-4">Connect Notion Workspace</h4>
                          <div className="space-y-4">
                            <div>
                              <label className="block text-sm font-medium text-gray-700 mb-2">
                                Notion API Token
                              </label>
                              <input
                                type="password"
                                value={notionToken}
                                onChange={(e) => setNotionToken(e.target.value)}
                                placeholder="secret_..."
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-digital-purple focus:border-digital-purple"
                              />
                              <p className="text-xs text-gray-500 mt-1">
                                Get your token from{' '}
                                <a
                                  href="https://www.notion.so/my-integrations"
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-blue-600 hover:underline"
                                >
                                  Notion Integrations
                                </a>
                              </p>
                            </div>
                            
                            <div className="flex space-x-3">
                              <button
                                onClick={handleConnectNotion}
                                disabled={isConnecting || !notionToken.trim()}
                                className="flex-1 bg-digital-purple text-white py-2 px-4 rounded-lg hover:bg-indigo-700 disabled:bg-gray-300 transition-colors"
                              >
                                {isConnecting ? 'Connecting...' : 'Connect'}
                              </button>
                              <button
                                onClick={() => {setShowNotionForm(false); setNotionToken('');}}
                                className="flex-1 bg-gray-300 text-gray-700 py-2 px-4 rounded-lg hover:bg-gray-400 transition-colors"
                              >
                                Cancel
                              </button>
                            </div>
                          </div>
                        </div>
                      </div>
                    )}

                    {showObsidianForm && (
                      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-10">
                        <div className="bg-white rounded-lg p-6 w-full max-w-md">
                          <h4 className="font-semibold mb-4">Connect Obsidian Vault</h4>
                          <div className="space-y-4">
                            <div>
                              <label className="block text-sm font-medium text-gray-700 mb-2">
                                Vault Path
                              </label>
                              <input
                                type="text"
                                value={obsidianPath}
                                onChange={(e) => setObsidianPath(e.target.value)}
                                placeholder="/path/to/your/obsidian/vault"
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-digital-purple focus:border-digital-purple"
                              />
                              <p className="text-xs text-gray-500 mt-1">
                                Full path to your Obsidian vault directory
                              </p>
                            </div>
                            
                            <div className="flex space-x-3">
                              <button
                                onClick={handleConnectObsidian}
                                disabled={isConnecting || !obsidianPath.trim()}
                                className="flex-1 bg-digital-purple text-white py-2 px-4 rounded-lg hover:bg-indigo-700 disabled:bg-gray-300 transition-colors"
                              >
                                {isConnecting ? 'Connecting...' : 'Connect'}
                              </button>
                              <button
                                onClick={() => {setShowObsidianForm(false); setObsidianPath('');}}
                                className="flex-1 bg-gray-300 text-gray-700 py-2 px-4 rounded-lg hover:bg-gray-400 transition-colors"
                              >
                                Cancel
                              </button>
                            </div>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {activeTab === 'sync' && (
                  <div className="space-y-6">
                    <h3 className="text-lg font-semibold text-gray-900">Legacy Vault Synchronization</h3>
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                      <p className="text-blue-800 text-sm">
                        💡 <strong>New!</strong> Use the "Knowledge Sources" tab to connect multiple note-taking apps including Notion, Obsidian, and more!
                      </p>
                    </div>
                    {/* Keep existing sync functionality for backwards compatibility */}
                  </div>
                )}

                {activeTab === 'health' && health && (
                  <div className="space-y-6">
                    <h3 className="text-lg font-semibold text-gray-900">System Health</h3>

                    <div className="bg-gray-50 rounded-lg p-4">
                      <div className="flex items-center space-x-3 mb-4">
                        <div className={`flex items-center space-x-2 ${getStatusColor(health.status)}`}>
                          {getStatusIcon(health.status)}
                          <span className="font-medium capitalize">{health.status}</span>
                        </div>
                        <span className="text-gray-500">•</span>
                        <span className="text-gray-600">Version {health.version}</span>
                      </div>

                      <div className="space-y-3">
                        <h4 className="font-medium text-gray-900">Services</h4>
                        {Object.entries(health.services).map(([service, status]) => (
                          <div key={service} className="flex items-center justify-between py-2 border-b border-gray-200 last:border-b-0">
                            <span className="font-medium text-gray-700 capitalize">
                              {service.replace(/_/g, ' ')}
                            </span>
                            <span className={`text-sm ${
                              status.includes('healthy') || status === 'configured' || status === 'running'
                                ? 'text-green-600' 
                                : status === 'stopped' || status.includes('not_configured')
                                ? 'text-yellow-600'
                                : 'text-red-600'
                            }`}>
                              {status}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>

                    <button
                      onClick={loadStatus}
                      className="flex items-center space-x-2 px-4 py-2 bg-digital-purple text-white rounded-lg hover:bg-indigo-700 transition-colors"
                    >
                      <RefreshCw className="w-4 h-4" />
                      <span>Refresh Status</span>
                    </button>
                  </div>
                )}

                {activeTab === 'about' && (
                  <div className="space-y-6">
                    <h3 className="text-lg font-semibold text-gray-900">About Digital Twin</h3>
                    
                    <div className="prose prose-sm max-w-none">
                      <p>
                        Digital Twin is a conversational AI application that creates a personalized
                        knowledge assistant from your notes across multiple platforms. It uses advanced natural language
                        processing to understand your notes and provide intelligent responses based on
                        your personal knowledge base.
                      </p>
                      
                      <h4>Supported Knowledge Sources:</h4>
                      <ul>
                        <li><strong>Notion</strong> - Your Notion workspace pages and databases</li>
                        <li><strong>Obsidian</strong> - Local markdown vaults</li>
                        <li><em>More sources coming soon!</em></li>
                      </ul>
                      
                      <h4>Key Features:</h4>
                      <ul>
                        <li>Multi-platform knowledge integration</li>
                        <li>Real-time synchronization</li>
                        <li>Intelligent semantic search</li>
                        <li>Context-aware conversational AI</li>
                        <li>Source attribution for all responses</li>
                        <li>Modern, responsive web interface</li>
                        <li>Privacy-first architecture</li>
                      </ul>

                      <h4>Technology Stack:</h4>
                      <ul>
                        <li>Backend: FastAPI, Python</li>
                        <li>Frontend: React, TypeScript, Tailwind CSS</li>
                        <li>Vector Database: ChromaDB</li>
                        <li>AI: OpenAI GPT-4 and embeddings</li>
                        <li>Integrations: Notion API, file system watchers</li>
                      </ul>

                      <p className="text-sm text-gray-600 mt-6">
                        Version 0.2.0 • Now with multi-platform support! • Built with ❤️ for knowledge workers
                      </p>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default SettingsModal;