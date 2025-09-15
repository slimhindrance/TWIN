import React, { useState, useEffect } from 'react';
import { Plus, Database, Zap, TrendingUp } from 'lucide-react';
import YNABConnection from './YNABConnection';

interface DataSource {
  type: string;
  name: string;
  category: string;
  connected: boolean;
  connected_at?: string;
  last_sync?: string;
  summary?: any;
}

interface SupportedSource {
  type: string;
  name: string;
  category: string;
  description: string;
  requires_credentials: string[];
  permissions: string[];
  sync_frequency: string;
}

const SourcesManager: React.FC = () => {
  const [connectedSources, setConnectedSources] = useState<DataSource[]>([]);
  const [supportedSources, setSupportedSources] = useState<SupportedSource[]>([]);
  const [showConnectModal, setShowConnectModal] = useState(false);
  const [selectedSource, setSelectedSource] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadSources();
    loadSupportedSources();
  }, []);

  const loadSources = async () => {
    try {
      const response = await fetch('/api/v1/sources/', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        const sources = await response.json();
        setConnectedSources(sources);
      }
    } catch (error) {
      console.error('Failed to load sources:', error);
    }
  };

  const loadSupportedSources = async () => {
    try {
      const response = await fetch('/api/v1/sources/supported');
      if (response.ok) {
        const supported = await response.json();
        setSupportedSources(supported);
      }
    } catch (error) {
      console.error('Failed to load supported sources:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSourceConnection = () => {
    loadSources();
    setShowConnectModal(false);
    setSelectedSource(null);
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'financial':
        return <TrendingUp className="h-5 w-5" />;
      case 'health_fitness':
        return <Zap className="h-5 w-5" />;
      default:
        return <Database className="h-5 w-5" />;
    }
  };

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'financial':
        return 'text-green-600 bg-green-100';
      case 'health_fitness':
        return 'text-blue-600 bg-blue-100';
      case 'productivity':
        return 'text-purple-600 bg-purple-100';
      case 'knowledge':
        return 'text-orange-600 bg-orange-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Data Sources</h1>
        <p className="text-gray-600">Connect your life data sources to build your Total Life AI knowledge base</p>
      </div>

      {/* Connected Sources */}
      {connectedSources.length > 0 && (
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Connected Sources</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {connectedSources.map((source) => (
              <div key={source.type} className="bg-white border border-gray-200 rounded-lg p-4">
                <div className="flex items-center mb-3">
                  <div className={`p-2 rounded-lg mr-3 ${getCategoryColor(source.category)}`}>
                    {getCategoryIcon(source.category)}
                  </div>
                  <div>
                    <h3 className="font-medium text-gray-900">{source.name}</h3>
                    <p className="text-sm text-gray-500 capitalize">{source.category.replace('_', ' ')}</p>
                  </div>
                </div>

                <div className="flex items-center justify-between text-sm">
                  <span className={`px-2 py-1 rounded-full text-xs ${source.connected ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                    {source.connected ? 'Connected' : 'Disconnected'}
                  </span>
                  {source.last_sync && (
                    <span className="text-gray-500">
                      Last sync: {new Date(source.last_sync).toLocaleDateString()}
                    </span>
                  )}
                </div>

                {source.summary && (
                  <div className="mt-3 pt-3 border-t border-gray-100">
                    <p className="text-xs text-gray-600">
                      {source.summary.total_transactions ? `${source.summary.total_transactions} transactions` : ''}
                      {source.summary.primary_budget ? `Budget: ${source.summary.primary_budget}` : ''}
                    </p>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Available Sources */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900">Available Sources</h2>
          <div className="text-sm text-gray-600">
            {supportedSources.length} integrations available
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {supportedSources.map((source) => {
            const isConnected = connectedSources.some(cs => cs.type === source.type);
            
            return (
              <div key={source.type} className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                <div className="flex items-center mb-3">
                  <div className={`p-2 rounded-lg mr-3 ${getCategoryColor(source.category)}`}>
                    {getCategoryIcon(source.category)}
                  </div>
                  <div>
                    <h3 className="font-medium text-gray-900">{source.name}</h3>
                    <p className="text-sm text-gray-500 capitalize">{source.category.replace('_', ' ')}</p>
                  </div>
                </div>

                <p className="text-sm text-gray-600 mb-4">{source.description}</p>

                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-500">
                    Sync: {source.sync_frequency}
                  </span>
                  
                  <button
                    onClick={() => {
                      setSelectedSource(source.type);
                      setShowConnectModal(true);
                    }}
                    disabled={isConnected}
                    className={`px-3 py-1 rounded-md text-sm font-medium ${
                      isConnected 
                        ? 'bg-gray-100 text-gray-500 cursor-not-allowed'
                        : 'bg-blue-600 hover:bg-blue-700 text-white'
                    }`}
                  >
                    {isConnected ? 'Connected' : 'Connect'}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Coming Soon Banner */}
      <div className="bg-gradient-to-r from-purple-600 to-blue-600 rounded-lg p-6 text-white">
        <h3 className="text-lg font-semibold mb-2">🚀 Total Life AI Platform</h3>
        <p className="mb-4">You're building the world's first comprehensive personal AI that understands every aspect of your life!</p>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <div className="font-medium">Financial Intelligence</div>
            <div className="text-purple-100">YNAB, Mint, Monarch</div>
          </div>
          <div>
            <div className="font-medium">Health & Fitness</div>
            <div className="text-purple-100">Apple Health, Strava, Garmin</div>
          </div>
          <div>
            <div className="font-medium">Productivity</div>
            <div className="text-purple-100">Todoist, Asana, ClickUp</div>
          </div>
          <div>
            <div className="font-medium">Media & More</div>
            <div className="text-purple-100">Google Photos, Gmail</div>
          </div>
        </div>
      </div>

      {/* Connection Modal */}
      {showConnectModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold">Connect Data Source</h2>
                <button
                  onClick={() => setShowConnectModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ×
                </button>
              </div>

              {selectedSource === 'ynab' && (
                <YNABConnection onConnectionSuccess={handleSourceConnection} />
              )}

              {selectedSource !== 'ynab' && (
                <div className="text-center py-8">
                  <p className="text-gray-600 mb-4">Integration for {selectedSource} is coming soon!</p>
                  <p className="text-sm text-gray-500">We're working on bringing you the ultimate life data platform.</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SourcesManager;
