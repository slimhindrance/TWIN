/**
 * API service for communicating with the Digital Twin backend.
 */
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for debugging
api.interceptors.request.use((config) => {
  console.log('API Request:', config.method?.toUpperCase(), config.url, config.data);
  return config;
});

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
}

export interface ChatRequest {
  message: string;
  conversation_id?: string;
  max_tokens?: number;
  temperature?: number;
}

export interface ChatResponse {
  message: string;
  conversation_id: string;
  sources: string[];
  metadata: {
    context_documents_used: number;
    total_conversation_length: number;
  };
}

export interface SearchQuery {
  query: string;
  limit?: number;
  similarity_threshold?: number;
}

export interface SearchResult {
  id: string;
  title: string;
  content: string;
  similarity_score: number;
  metadata: Record<string, any>;
}

export interface SearchResponse {
  results: SearchResult[];
  total_results: number;
  query: string;
}

export interface VaultSyncStatus {
  vault_path: string | null;
  is_watching: boolean;
  last_sync: string | null;
  total_documents: number;
  sync_errors: string[];
}

export interface HealthCheck {
  status: string;
  version: string;
  timestamp: string;
  services: Record<string, string>;
}

export class ApiService {
  /**
   * Send a chat message to the digital twin
   */
  static async sendChatMessage(request: ChatRequest): Promise<ChatResponse> {
    const response = await api.post<ChatResponse>('/chat', request);
    return response.data;
  }

  /**
   * Get conversation history
   */
  static async getConversation(conversationId: string): Promise<{
    conversation_id: string;
    messages: ChatMessage[];
    message_count: number;
  }> {
    const response = await api.get(`/chat/conversations/${conversationId}`);
    return response.data;
  }

  /**
   * List all conversations
   */
  static async listConversations(): Promise<{
    conversations: Array<{
      conversation_id: string;
      message_count: number;
      last_message_time: string;
      last_message_preview: string;
    }>;
    total_conversations: number;
  }> {
    const response = await api.get('/chat/conversations');
    return response.data;
  }

  /**
   * Delete a conversation
   */
  static async deleteConversation(conversationId: string): Promise<{ message: string }> {
    const response = await api.delete(`/chat/conversations/${conversationId}`);
    return response.data;
  }

  /**
   * Search the knowledge base
   */
  static async searchKnowledgeBase(query: SearchQuery): Promise<SearchResponse> {
    const response = await api.post<SearchResponse>('/search', query);
    return response.data;
  }

  /**
   * Get vault sync status
   */
  static async getVaultSyncStatus(): Promise<VaultSyncStatus> {
    const response = await api.get<VaultSyncStatus>('/sync/status');
    return response.data;
  }

  /**
   * Trigger full vault sync
   */
  static async triggerFullSync(): Promise<{ message: string; status: string }> {
    const response = await api.post('/sync/full-sync');
    return response.data;
  }

  /**
   * Start vault watching
   */
  static async startVaultWatching(): Promise<{ message: string; status: string }> {
    const response = await api.post('/sync/start-watching');
    return response.data;
  }

  /**
   * Stop vault watching
   */
  static async stopVaultWatching(): Promise<{ message: string; status: string }> {
    const response = await api.post('/sync/stop-watching');
    return response.data;
  }

  /**
   * Configure vault path
   */
  static async configureVault(vaultPath: string): Promise<{
    message: string;
    status: string;
    vault_path: string;
  }> {
    const response = await api.post('/sync/configure', { vault_path: vaultPath });
    return response.data;
  }

  /**
   * Get health status
   */
  static async getHealth(): Promise<HealthCheck> {
    const response = await api.get<HealthCheck>('/health');
    return response.data;
  }

  /**
   * Get readiness status
   */
  static async getReadiness(): Promise<{ status: string; reason?: string }> {
    const response = await api.get('/health/ready');
    return response.data;
  }
}

export default ApiService;
