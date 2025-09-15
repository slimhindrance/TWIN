/**
 * Component to display sources used in the response
 */
import React, { useState } from 'react';
import { FileText, ChevronDown, ChevronUp } from 'lucide-react';

interface SourcesListProps {
  sources: string[];
}

const SourcesList: React.FC<SourcesListProps> = ({ sources }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  if (!sources || sources.length === 0) {
    return null;
  }

  const displaySources = isExpanded ? sources : sources.slice(0, 3);
  const hasMoreSources = sources.length > 3;

  return (
    <div className="bg-white/80 backdrop-blur-sm rounded-lg border border-gray-200 p-3">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center space-x-2">
          <FileText className="w-4 h-4 text-gray-600" />
          <span className="text-sm font-medium text-gray-700">
            Sources ({sources.length})
          </span>
        </div>
        
        {hasMoreSources && (
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="flex items-center space-x-1 text-sm text-digital-purple hover:text-indigo-700 transition-colors"
          >
            <span>{isExpanded ? 'Show Less' : 'Show All'}</span>
            {isExpanded ? (
              <ChevronUp className="w-4 h-4" />
            ) : (
              <ChevronDown className="w-4 h-4" />
            )}
          </button>
        )}
      </div>
      
      <div className="space-y-1">
        {displaySources.map((source, index) => (
          <div
            key={index}
            className="flex items-center space-x-2 text-sm text-gray-600 bg-gray-50 rounded px-2 py-1"
          >
            <FileText className="w-3 h-3 flex-shrink-0" />
            <span className="truncate" title={source}>
              {source}
            </span>
          </div>
        ))}
      </div>
      
      {!isExpanded && hasMoreSources && (
        <div className="text-xs text-gray-500 mt-1">
          and {sources.length - 3} more sources...
        </div>
      )}
    </div>
  );
};

export default SourcesList;
