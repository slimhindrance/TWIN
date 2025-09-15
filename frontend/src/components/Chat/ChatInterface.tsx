/**
 * Main chat interface component
 */
import React, { useState, useEffect, useRef } from 'react';
import { Send, Settings, Search, RefreshCw, Brain } from 'lucide-react';
import { ApiService, ChatMessage, ChatResponse } from '../../services/api';
import MessageBubble from './MessageBubble';
import SourcesList from './SourcesList';

interface ChatInterfaceProps {
  onOpenSettings?: () => void;
  onOpenSearch?: () => void;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ onOpenSettings, onOpenSearch }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [sources, setSources] = useState<string[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Add welcome message
    const welcomeMessage: ChatMessage = {
      role: 'assistant',
      content: `Hello! I'm your digital twin - a conversational AI that has access to your personal knowledge base from your Obsidian vault. I can help you:

• Recall information from your notes
• Make connections between different ideas
• Discuss your previous work and thoughts
• Search through your knowledge base

What would you like to explore today?`,
      timestamp: new Date().toISOString(),
    };
    setMessages([welcomeMessage]);
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      role: 'user',
      content: inputValue.trim(),
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      const response: ChatResponse = await ApiService.sendChatMessage({
        message: userMessage.content,
        conversation_id: conversationId || undefined,
      });

      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: response.message,
        timestamp: new Date().toISOString(),
      };

      setMessages(prev => [...prev, assistantMessage]);
      setConversationId(response.conversation_id);
      setSources(response.sources);

    } catch (error) {
      console.error('Chat error:', error);
      const errorMessage: ChatMessage = {
        role: 'assistant',
        content: 'I apologize, but I encountered an error while processing your message. Please check that the backend is running and try again.',
        timestamp: new Date().toISOString(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const clearConversation = () => {
    setMessages([]);
    setConversationId(null);
    setSources([]);
    // Re-add welcome message
    const welcomeMessage: ChatMessage = {
      role: 'assistant',
      content: "I'm ready for a new conversation. What would you like to explore?",
      timestamp: new Date().toISOString(),
    };
    setMessages([welcomeMessage]);
  };

  return (
    <div className="flex flex-col h-full bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200 p-4">
        <div className="flex justify-between items-center">
          <div className="flex items-center space-x-3">
            <Brain className="w-8 h-8 text-digital-purple" />
            <div>
              <h1 className="text-xl font-bold text-gray-900">Digital Twin</h1>
              <p className="text-sm text-gray-600">Your personal knowledge assistant</p>
            </div>
          </div>
          
          <div className="flex space-x-2">
            <button
              onClick={onOpenSearch}
              className="p-2 text-gray-600 hover:text-digital-purple hover:bg-gray-100 rounded-lg transition-colors"
              title="Search Knowledge Base"
            >
              <Search className="w-5 h-5" />
            </button>
            
            <button
              onClick={clearConversation}
              className="p-2 text-gray-600 hover:text-digital-purple hover:bg-gray-100 rounded-lg transition-colors"
              title="New Conversation"
            >
              <RefreshCw className="w-5 h-5" />
            </button>
            
            <button
              onClick={onOpenSettings}
              className="p-2 text-gray-600 hover:text-digital-purple hover:bg-gray-100 rounded-lg transition-colors"
              title="Settings"
            >
              <Settings className="w-5 h-5" />
            </button>
          </div>
        </div>
      </header>

      {/* Chat Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message, index) => (
          <MessageBubble
            key={index}
            message={message}
            isLatest={index === messages.length - 1}
          />
        ))}
        
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-white rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm max-w-xs">
              <div className="flex space-x-1">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Sources */}
      {sources.length > 0 && (
        <div className="px-4 pb-2">
          <SourcesList sources={sources} />
        </div>
      )}

      {/* Input Area */}
      <div className="p-4 bg-white border-t border-gray-200">
        <form onSubmit={handleSubmit} className="flex space-x-3">
          <div className="flex-1 relative">
            <textarea
              ref={inputRef}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask me anything about your knowledge base..."
              disabled={isLoading}
              rows={1}
              className="w-full resize-none rounded-xl border border-gray-300 px-4 py-3 pr-12 focus:border-digital-purple focus:ring-2 focus:ring-digital-purple focus:ring-opacity-20 disabled:bg-gray-50 disabled:text-gray-500"
              style={{ minHeight: '3rem', maxHeight: '8rem' }}
            />
          </div>
          
          <button
            type="submit"
            disabled={!inputValue.trim() || isLoading}
            className="flex-shrink-0 bg-digital-purple text-white p-3 rounded-xl hover:bg-indigo-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
          >
            <Send className="w-5 h-5" />
          </button>
        </form>
        
        <p className="text-xs text-gray-500 mt-2 text-center">
          Press Enter to send, Shift+Enter for new line
        </p>
      </div>
    </div>
  );
};

export default ChatInterface;
