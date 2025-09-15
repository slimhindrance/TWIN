/**
 * Settings modal for configuring the Digital Twin application
 */
import React, { useState, useEffect } from 'react';
import { X, Settings, FolderOpen, RefreshCw, CheckCircle, AlertCircle, Play, Square } from 'lucide-react';
import { ApiService, VaultSyncStatus, HealthCheck } from '../../services/api';

interface SettingsModalProps {
  onClose: () => void;
}

const SettingsModal: React.FC<SettingsModalProps> = ({ onClose }) => {
  const [activeTab, setActiveTab] = useState<'sync' | 'health' | 'about'>('sync');
  const [syncStatus, setSyncStatus] = useState<VaultSyncStatus | null>(null);
  const [health, setHealth] = useState<HealthCheck | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [vaultPath, setVaultPath] = useState('');
  const [isConfiguring, setIsConfiguring] = useState(false);
  const [message, setMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);

  useEffect(() => {
    loadStatus();
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
      if (syncResponse?.vault_path) {
        setVaultPath(syncResponse.vault_path);
      }
    } catch (error) {
      console.error('Failed to load status:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const showMessage = (text: string, type: 'success' | 'error') => {
    setMessage({ text, type });
    setTimeout(() => setMessage(null), 5000);
  };

  const handleConfigureVault = async () => {
    if (!vaultPath.trim()) {
      showMessage('Please enter a valid vault path', 'error');
      return;
    }

    try {
      setIsConfiguring(true);
      await ApiService.configureVault(vaultPath.trim());
      showMessage('Vault configured successfully', 'success');
      await loadStatus();
    } catch (error: any) {
      showMessage(error.response?.data?.detail || 'Failed to configure vault', 'error');
    } finally {
      setIsConfiguring(false);
    }
  };

  const handleFullSync = async () => {
    try {
      await ApiService.triggerFullSync();
      showMessage('Full sync started in background', 'success');
      setTimeout(loadStatus, 2000);
    } catch (error: any) {
      showMessage(error.response?.data?.detail || 'Failed to start sync', 'error');
    }
  };

  const handleToggleWatching = async () => {
    try {
      if (syncStatus?.is_watching) {
        await ApiService.stopVaultWatching();
        showMessage('Vault watching stopped', 'success');
      } else {
        await ApiService.startVaultWatching();
        showMessage('Vault watching started', 'success');
      }
      await loadStatus();
    } catch (error: any) {
      showMessage(error.response?.data?.detail || 'Failed to toggle watching', 'error');
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

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] flex flex-col">
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
                {activeTab === 'sync' && (
                  <div className="space-y-6">
                    <h3 className="text-lg font-semibold text-gray-900">Vault Synchronization</h3>

                    {/* Current Status */}
                    <div className="bg-gray-50 rounded-lg p-4">
                      <h4 className="font-medium text-gray-900 mb-3">Current Status</h4>
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <span className="text-gray-600">Vault Path:</span>
                          <p className="font-mono text-xs mt-1 break-all">
                            {syncStatus?.vault_path || 'Not configured'}
                          </p>
                        </div>
                        <div>
                          <span className="text-gray-600">Total Documents:</span>
                          <p className="font-medium">{syncStatus?.total_documents || 0}</p>
                        </div>
                        <div>
                          <span className="text-gray-600">Watching:</span>
                          <p className="font-medium">
                            {syncStatus?.is_watching ? 'Active' : 'Inactive'}
                          </p>
                        </div>
                        <div>
                          <span className="text-gray-600">Last Sync:</span>
                          <p className="font-medium">{formatDate(syncStatus?.last_sync)}</p>
                        </div>
                      </div>
                    </div>

                    {/* Configure Vault */}
                    <div className="space-y-3">
                      <h4 className="font-medium text-gray-900">Configure Vault Path</h4>
                      <div className="flex space-x-3">
                        <input
                          type="text"
                          value={vaultPath}
                          onChange={(e) => setVaultPath(e.target.value)}
                          placeholder="Enter path to your Obsidian vault..."
                          className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:border-digital-purple focus:ring-2 focus:ring-digital-purple focus:ring-opacity-20"
                        />
                        <button
                          onClick={handleConfigureVault}
                          disabled={isConfiguring}
                          className="flex items-center space-x-2 px-4 py-2 bg-digital-purple text-white rounded-lg hover:bg-indigo-700 disabled:bg-gray-300 transition-colors"
                        >
                          <FolderOpen className="w-4 h-4" />
                          <span>{isConfiguring ? 'Configuring...' : 'Configure'}</span>
                        </button>
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex space-x-3">
                      <button
                        onClick={handleFullSync}
                        className="flex items-center space-x-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                      >
                        <RefreshCw className="w-4 h-4" />
                        <span>Full Sync</span>
                      </button>
                      
                      <button
                        onClick={handleToggleWatching}
                        className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors ${
                          syncStatus?.is_watching
                            ? 'bg-red-600 text-white hover:bg-red-700'
                            : 'bg-blue-600 text-white hover:bg-blue-700'
                        }`}
                      >
                        {syncStatus?.is_watching ? (
                          <>
                            <Square className="w-4 h-4" />
                            <span>Stop Watching</span>
                          </>
                        ) : (
                          <>
                            <Play className="w-4 h-4" />
                            <span>Start Watching</span>
                          </>
                        )}
                      </button>
                    </div>
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
                        knowledge assistant from your Obsidian vault. It uses advanced natural language
                        processing to understand your notes and provide intelligent responses based on
                        your personal knowledge base.
                      </p>
                      
                      <h4>Features:</h4>
                      <ul>
                        <li>Real-time synchronization with your Obsidian vault</li>
                        <li>Intelligent search through your notes</li>
                        <li>Context-aware conversational AI</li>
                        <li>Source attribution for all responses</li>
                        <li>Modern, responsive web interface</li>
                      </ul>

                      <h4>Technology Stack:</h4>
                      <ul>
                        <li>Backend: FastAPI, Python</li>
                        <li>Frontend: React, TypeScript, Tailwind CSS</li>
                        <li>Vector Database: ChromaDB</li>
                        <li>AI: OpenAI GPT-4 and embeddings</li>
                      </ul>

                      <p className="text-sm text-gray-600 mt-6">
                        Version 0.1.0 • Built with ❤️ for knowledge workers
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
