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

// Request interceptor to add auth headers
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Request interceptor for debugging (development only)
api.interceptors.request.use((config) => {
  if (process.env.NODE_ENV === 'development') {
    console.log('API Request:', config.method?.toUpperCase(), config.url, config.data);
  }
  return config;
});

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (process.env.NODE_ENV === 'development') {
      console.error('API Error:', error.response?.data || error.message);
    }
    
    // Handle 401 Unauthorized errors
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token');
      localStorage.removeItem('auth_user');
      window.location.reload();
    }
    
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

// Knowledge Sources Types
export interface SourceStatus {
  type: string;
  connected: boolean;
  document_count: number;
  configured: boolean;
  last_synced?: string;
  error?: string;
}

export interface SupportedSource {
  type: string;
  name: string;
  description: string;
  requires_credentials: string[];
  free: boolean;
  setup_url?: string;
}

export interface NotionCredentials {
  notion_api_token: string;
}

export interface ObsidianCredentials {
  vault_path: string;
}

export interface SourceSyncResult {
  total_documents: number;
  sources_synced: number;
  errors: string[];
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
   * Get vault sync status (legacy - for backwards compatibility)
   */
  static async getVaultSyncStatus(): Promise<VaultSyncStatus> {
    const response = await api.get<VaultSyncStatus>('/sync/status');
    return response.data;
  }

  /**
   * Trigger full vault sync (legacy)
   */
  static async triggerFullSync(): Promise<{ message: string; status: string }> {
    const response = await api.post('/sync/full-sync');
    return response.data;
  }

  /**
   * Start vault watching (legacy)
   */
  static async startVaultWatching(): Promise<{ message: string; status: string }> {
    const response = await api.post('/sync/start-watching');
    return response.data;
  }

  /**
   * Stop vault watching (legacy)
   */
  static async stopVaultWatching(): Promise<{ message: string; status: string }> {
    const response = await api.post('/sync/stop-watching');
    return response.data;
  }

  /**
   * Configure vault path (legacy)
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

  // === NEW KNOWLEDGE SOURCES API ===

  /**
   * Get supported knowledge source types
   */
  static async getSupportedSources(): Promise<{ sources: SupportedSource[] }> {
    const response = await api.get('/sources/supported');
    return response.data;
  }

  /**
   * Get status of all knowledge sources
   */
  static async getSourcesStatus(): Promise<SourceStatus[]> {
    const response = await api.get<SourceStatus[]>('/sources/status');
    return response.data;
  }

  /**
   * Connect Notion workspace
   */
  static async connectNotion(credentials: NotionCredentials): Promise<{
    message: string;
    status: string;
    source_type: string;
  }> {
    const response = await api.post('/sources/notion/connect', credentials);
    return response.data;
  }

  /**
   * Connect Obsidian vault  
   */
  static async connectObsidian(credentials: ObsidianCredentials): Promise<{
    message: string;
    status: string;
    source_type: string;
  }> {
    const response = await api.post('/sources/obsidian/connect', credentials);
    return response.data;
  }

  /**
   * Disconnect a knowledge source
   */
  static async disconnectSource(sourceType: string): Promise<{
    message: string;
    status: string;
    source_type: string;
  }> {
    const response = await api.delete(`/sources/${sourceType}/disconnect`);
    return response.data;
  }

  /**
   * Test connection to a knowledge source
   */
  static async testSourceConnection(sourceType: string): Promise<{
    source_type: string;
    connected: boolean;
    document_count: number;
    message: string;
  }> {
    const response = await api.get(`/sources/${sourceType}/test`);
    return response.data;
  }

  /**
   * Sync all knowledge sources
   */
  static async syncAllSources(): Promise<SourceSyncResult> {
    const response = await api.post<SourceSyncResult>('/sources/sync');
    return response.data;
  }
}

export default ApiService;