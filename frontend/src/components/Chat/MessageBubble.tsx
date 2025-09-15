/**
 * Individual message bubble component
 */
import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { User, Brain } from 'lucide-react';
import { ChatMessage } from '../../services/api';

interface MessageBubbleProps {
  message: ChatMessage;
  isLatest?: boolean;
}

const MessageBubble: React.FC<MessageBubbleProps> = ({ message, isLatest = false }) => {
  const isUser = message.role === 'user';
  const timestamp = new Date(message.timestamp).toLocaleTimeString([], { 
    hour: '2-digit', 
    minute: '2-digit' 
  });

  return (
    <div 
      className={`flex ${isUser ? 'justify-end' : 'justify-start'} animate-slide-up`}
    >
      <div className={`flex space-x-3 max-w-4xl ${isUser ? 'flex-row-reverse space-x-reverse' : 'flex-row'}`}>
        {/* Avatar */}
        <div className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center ${
          isUser ? 'bg-user-blue' : 'bg-assistant-green'
        }`}>
          {isUser ? (
            <User className="w-5 h-5 text-white" />
          ) : (
            <Brain className="w-5 h-5 text-white" />
          )}
        </div>

        {/* Message Content */}
        <div className={`flex flex-col space-y-1 ${isUser ? 'items-end' : 'items-start'}`}>
          <div
            className={`px-4 py-3 rounded-2xl shadow-sm ${
              isUser
                ? 'bg-user-blue text-white rounded-tr-sm'
                : 'bg-white text-gray-900 rounded-tl-sm border border-gray-200'
            }`}
            style={{ minWidth: '100px', maxWidth: '100%' }}
          >
            {isUser ? (
              <p className="whitespace-pre-wrap break-words">{message.content}</p>
            ) : (
              <div className="prose prose-sm max-w-none">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  className="text-gray-900"
                  components={{
                    // Customize markdown rendering
                    h1: ({ children }) => <h1 className="text-xl font-bold mb-2">{children}</h1>,
                    h2: ({ children }) => <h2 className="text-lg font-semibold mb-2">{children}</h2>,
                    h3: ({ children }) => <h3 className="text-base font-medium mb-1">{children}</h3>,
                    p: ({ children }) => <p className="mb-2 last:mb-0 leading-relaxed">{children}</p>,
                    ul: ({ children }) => <ul className="list-disc list-inside mb-2 space-y-1">{children}</ul>,
                    ol: ({ children }) => <ol className="list-decimal list-inside mb-2 space-y-1">{children}</ol>,
                    li: ({ children }) => <li className="leading-relaxed">{children}</li>,
                    code: ({ inline, children }) => 
                      inline ? (
                        <code className="bg-gray-100 text-gray-800 px-1.5 py-0.5 rounded text-sm font-mono">
                          {children}
                        </code>
                      ) : (
                        <code className="block bg-gray-100 text-gray-800 p-3 rounded-lg text-sm font-mono overflow-x-auto">
                          {children}
                        </code>
                      ),
                    blockquote: ({ children }) => (
                      <blockquote className="border-l-4 border-gray-300 pl-4 italic text-gray-700 mb-2">
                        {children}
                      </blockquote>
                    ),
                    a: ({ href, children }) => (
                      <a 
                        href={href} 
                        className="text-digital-purple hover:underline" 
                        target="_blank" 
                        rel="noopener noreferrer"
                      >
                        {children}
                      </a>
                    ),
                  }}
                >
                  {message.content}
                </ReactMarkdown>
              </div>
            )}
          </div>
          
          {/* Timestamp */}
          <span className={`text-xs text-gray-500 ${isUser ? 'text-right' : 'text-left'}`}>
            {timestamp}
          </span>
        </div>
      </div>
    </div>
  );
};

export default MessageBubble;
