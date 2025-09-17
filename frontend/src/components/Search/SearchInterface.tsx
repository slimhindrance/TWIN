/**
 * Search interface for querying the knowledge base
 */
import React, { useState } from 'react';
import { Search, X, FileText, ExternalLink } from 'lucide-react';
import { ApiService, SearchResult } from '../../services/api';

interface SearchInterfaceProps {
  onClose: () => void;
}

const SearchInterface: React.FC<SearchInterfaceProps> = ({ onClose }) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [similarity, setSimilarity] = useState(0.7);
  const [limit, setLimit] = useState(10);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setIsLoading(true);
    setHasSearched(true);

    try {
      const response = await ApiService.searchKnowledgeBase({
        query: query.trim(),
        limit,
        similarity_threshold: similarity,
      });
      setResults(response.results);
    } catch (error) {
      if (process.env.NODE_ENV === 'development') {
        console.error('Search error:', error);
      }
      setResults([]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleResultClick = (result: SearchResult) => {
    // In a more complete implementation, this could open a detailed view
    // or insert the content into the chat
    if (process.env.NODE_ENV === 'development') {
      console.log('Result clicked:', result);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center space-x-3">
            <Search className="w-6 h-6 text-digital-purple" />
            <h2 className="text-xl font-semibold text-gray-900">Search Knowledge Base</h2>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-gray-600 rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Search Form */}
        <div className="p-6 border-b border-gray-200">
          <form onSubmit={handleSearch} className="space-y-4">
            <div className="flex space-x-3">
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search your knowledge base..."
                className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:border-digital-purple focus:ring-2 focus:ring-digital-purple focus:ring-opacity-20"
                autoFocus
              />
              <button
                type="submit"
                disabled={!query.trim() || isLoading}
                className="px-6 py-3 bg-digital-purple text-white rounded-lg hover:bg-indigo-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
              >
                {isLoading ? 'Searching...' : 'Search'}
              </button>
            </div>

            {/* Advanced Options */}
            <div className="flex space-x-6 text-sm">
              <div className="flex items-center space-x-2">
                <label htmlFor="similarity" className="text-gray-700">
                  Similarity Threshold:
                </label>
                <input
                  id="similarity"
                  type="range"
                  min="0.1"
                  max="1.0"
                  step="0.1"
                  value={similarity}
                  onChange={(e) => setSimilarity(parseFloat(e.target.value))}
                  className="w-20"
                />
                <span className="text-gray-600 w-10">{similarity}</span>
              </div>

              <div className="flex items-center space-x-2">
                <label htmlFor="limit" className="text-gray-700">
                  Max Results:
                </label>
                <select
                  id="limit"
                  value={limit}
                  onChange={(e) => setLimit(parseInt(e.target.value))}
                  className="px-2 py-1 border border-gray-300 rounded"
                >
                  <option value={5}>5</option>
                  <option value={10}>10</option>
                  <option value={20}>20</option>
                  <option value={50}>50</option>
                </select>
              </div>
            </div>
          </form>
        </div>

        {/* Results */}
        <div className="flex-1 overflow-y-auto p-6">
          {isLoading && (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-digital-purple"></div>
            </div>
          )}

          {!isLoading && hasSearched && results.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              <Search className="w-12 h-12 mx-auto mb-3 text-gray-300" />
              <p>No results found for "{query}"</p>
              <p className="text-sm mt-1">Try adjusting your search terms or similarity threshold</p>
            </div>
          )}

          {!isLoading && results.length > 0 && (
            <div className="space-y-4">
              <div className="flex items-center justify-between mb-4">
                <p className="text-gray-600">
                  Found {results.length} result{results.length !== 1 ? 's' : ''} for "{query}"
                </p>
              </div>

              {results.map((result, index) => (
                <div
                  key={result.id}
                  className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 cursor-pointer transition-colors"
                  onClick={() => handleResultClick(result)}
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex items-center space-x-2">
                      <FileText className="w-4 h-4 text-gray-500 mt-1" />
                      <h3 className="font-medium text-gray-900">{result.title}</h3>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className="text-sm text-gray-500">
                        {Math.round(result.similarity_score * 100)}% match
                      </span>
                      <ExternalLink className="w-4 h-4 text-gray-400" />
                    </div>
                  </div>

                  <p className="text-gray-700 text-sm leading-relaxed mb-2">
                    {result.content}
                  </p>

                  <div className="flex items-center justify-between text-xs text-gray-500">
                    <span>Source: {result.metadata.source || 'Unknown'}</span>
                    {result.metadata.tags && result.metadata.tags.length > 0 && (
                      <div className="flex space-x-1">
                        {result.metadata.tags.slice(0, 3).map((tag: string, tagIndex: number) => (
                          <span
                            key={tagIndex}
                            className="bg-gray-200 text-gray-700 px-2 py-1 rounded-full text-xs"
                          >
                            #{tag}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}

          {!hasSearched && (
            <div className="text-center py-8 text-gray-500">
              <Search className="w-12 h-12 mx-auto mb-3 text-gray-300" />
              <p>Enter a search query to explore your knowledge base</p>
              <p className="text-sm mt-1">Use natural language or specific keywords</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SearchInterface;
