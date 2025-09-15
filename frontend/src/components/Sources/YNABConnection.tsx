import React, { useState } from 'react';
import { AlertCircle, DollarSign, TrendingUp, PieChart, CheckCircle, ExternalLink } from 'lucide-react';

interface YNABConnectionProps {
  onConnectionSuccess?: () => void;
}

interface YNABData {
  budgets: any[];
  transactions: any[];
  insights: any;
}

const YNABConnection: React.FC<YNABConnectionProps> = ({ onConnectionSuccess }) => {
  const [accessToken, setAccessToken] = useState('');
  const [isConnecting, setIsConnecting] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [connectionData, setConnectionData] = useState<YNABData | null>(null);
  const [error, setError] = useState('');
  const [showInstructions, setShowInstructions] = useState(false);

  const handleConnect = async () => {
    if (!accessToken.trim()) {
      setError('Please enter your YNAB access token');
      return;
    }

    setIsConnecting(true);
    setError('');

    try {
      const response = await fetch('/api/v1/sources/ynab/connect', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          access_token: accessToken
        })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to connect YNAB');
      }

      setIsConnected(true);
      setConnectionData(data.sync_result?.data?.ynab || null);
      
      if (onConnectionSuccess) {
        onConnectionSuccess();
      }

      // Clear the token from display for security
      setAccessToken('');

    } catch (error) {
      setError(error instanceof Error ? error.message : 'Connection failed');
    } finally {
      setIsConnecting(false);
    }
  };

  const fetchInsights = async () => {
    try {
      const response = await fetch('/api/v1/sources/ynab/insights', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        const insights = await response.json();
        setConnectionData(prev => prev ? { ...prev, insights } : { budgets: [], transactions: [], insights });
      }
    } catch (error) {
      console.error('Failed to fetch insights:', error);
    }
  };

  if (isConnected) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-center mb-6">
          <div className="bg-green-100 p-2 rounded-lg mr-4">
            <DollarSign className="h-6 w-6 text-green-600" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">YNAB Connected</h3>
            <p className="text-sm text-gray-600">Your financial intelligence is now active!</p>
          </div>
          <CheckCircle className="h-5 w-5 text-green-500 ml-auto" />
        </div>

        {connectionData?.insights && (
          <div className="space-y-4">
            <h4 className="font-medium text-gray-900">Financial Insights</h4>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-blue-50 p-4 rounded-lg">
                <div className="flex items-center">
                  <TrendingUp className="h-5 w-5 text-blue-600 mr-2" />
                  <div>
                    <p className="text-sm text-blue-600">Total Spending</p>
                    <p className="text-xl font-bold text-blue-900">
                      ${connectionData.insights.insights?.total_spending?.toFixed(2) || '0.00'}
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-green-50 p-4 rounded-lg">
                <div className="flex items-center">
                  <PieChart className="h-5 w-5 text-green-600 mr-2" />
                  <div>
                    <p className="text-sm text-green-600">Transactions</p>
                    <p className="text-xl font-bold text-green-900">
                      {connectionData.insights.insights?.transaction_count || 0}
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-purple-50 p-4 rounded-lg">
                <div className="flex items-center">
                  <DollarSign className="h-5 w-5 text-purple-600 mr-2" />
                  <div>
                    <p className="text-sm text-purple-600">Cash Flow</p>
                    <p className="text-xl font-bold text-purple-900">
                      ${connectionData.insights.insights?.net_cash_flow?.toFixed(2) || '0.00'}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {connectionData.insights.insights?.top_spending_categories && (
              <div>
                <h5 className="font-medium text-gray-900 mb-2">Top Spending Categories</h5>
                <div className="space-y-2">
                  {connectionData.insights.insights.top_spending_categories.map((category: any, index: number) => (
                    <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                      <span className="text-sm font-medium">{category.category}</span>
                      <div className="text-right">
                        <span className="text-sm font-bold">${category.amount.toFixed(2)}</span>
                        <span className="text-xs text-gray-500 ml-2">({category.percentage}%)</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="bg-yellow-50 p-4 rounded-lg">
              <h5 className="font-medium text-yellow-800 mb-2">🚀 Next Level Insights Coming Soon!</h5>
              <ul className="text-sm text-yellow-700 space-y-1">
                <li>• Cross-correlate spending with your health data</li>
                <li>• Find patterns between purchases and productivity</li>
                <li>• AI-powered budget optimization recommendations</li>
                <li>• Connect more life data sources for deeper insights!</li>
              </ul>
            </div>
          </div>
        )}

        <div className="mt-6 pt-6 border-t border-gray-200">
          <button
            onClick={fetchInsights}
            className="text-blue-600 hover:text-blue-700 text-sm font-medium"
          >
            Refresh Insights
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <div className="flex items-center mb-6">
        <div className="bg-blue-100 p-2 rounded-lg mr-4">
          <DollarSign className="h-6 w-6 text-blue-600" />
        </div>
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Connect YNAB</h3>
          <p className="text-sm text-gray-600">Import your budget and spending data for financial intelligence</p>
        </div>
      </div>

      {!showInstructions ? (
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              YNAB Personal Access Token
            </label>
            <input
              type="password"
              value={accessToken}
              onChange={(e) => setAccessToken(e.target.value)}
              placeholder="Enter your YNAB access token"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          {error && (
            <div className="flex items-center p-3 bg-red-50 border border-red-200 rounded-md">
              <AlertCircle className="h-5 w-5 text-red-500 mr-2" />
              <span className="text-sm text-red-700">{error}</span>
            </div>
          )}

          <div className="flex items-center justify-between">
            <button
              type="button"
              onClick={() => setShowInstructions(true)}
              className="text-blue-600 hover:text-blue-700 text-sm font-medium flex items-center"
            >
              How to get my access token?
              <ExternalLink className="h-4 w-4 ml-1" />
            </button>

            <button
              onClick={handleConnect}
              disabled={isConnecting || !accessToken.trim()}
              className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-white px-6 py-2 rounded-md font-medium transition-colors"
            >
              {isConnecting ? 'Connecting...' : 'Connect YNAB'}
            </button>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="bg-blue-50 p-4 rounded-lg">
            <h4 className="font-medium text-blue-900 mb-3">How to Get Your YNAB Access Token</h4>
            <ol className="text-sm text-blue-800 space-y-2 list-decimal list-inside">
              <li>Log in to your YNAB account at <strong>app.youneedabudget.com</strong></li>
              <li>Go to <strong>Account Settings</strong> (click your email in the top right)</li>
              <li>Click on <strong>Developer Settings</strong></li>
              <li>Click <strong>New Token</strong></li>
              <li>Give your token a name (e.g., "Total Life AI")</li>
              <li>Copy the generated token and paste it above</li>
            </ol>
          </div>

          <div className="bg-yellow-50 p-4 rounded-lg">
            <div className="flex items-center">
              <AlertCircle className="h-5 w-5 text-yellow-600 mr-2" />
              <div>
                <h5 className="font-medium text-yellow-800">Security Note</h5>
                <p className="text-sm text-yellow-700">Your token is encrypted and stored securely. We only request read-only access to your YNAB data.</p>
              </div>
            </div>
          </div>

          <button
            onClick={() => setShowInstructions(false)}
            className="text-blue-600 hover:text-blue-700 text-sm font-medium"
          >
            ← Back to Connection
          </button>
        </div>
      )}
    </div>
  );
};

export default YNABConnection;
