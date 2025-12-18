/**
 * API service for communicating with the backend
 */
import axios from 'axios';
import type {
    Stats,
    Activity,
    ToolsResponse,
    UsersResponse,
    ConversationsResponse,
    ConversationDetail,
    DbHealth
} from '../types';

const API_BASE = import.meta.env.VITE_API_URL || '';

const api = axios.create({
    baseURL: API_BASE,
    timeout: 10000,
});

export const adminApi = {
    // Health
    getHealth: async (): Promise<{ status: string; service: string }> => {
        const { data } = await api.get('/health');
        return data;
    },

    getDbHealth: async (): Promise<DbHealth> => {
        const { data } = await api.get('/admin/db-health');
        return data;
    },

    // Stats
    getStats: async (): Promise<Stats> => {
        const { data } = await api.get('/admin/stats');
        return data;
    },

    getActivity: async (): Promise<Activity> => {
        const { data } = await api.get('/admin/activity');
        return data;
    },

    getTools: async (limit = 8): Promise<ToolsResponse> => {
        const { data } = await api.get('/admin/tools', { params: { limit } });
        return data;
    },

    // Users
    getUsers: async (params?: {
        limit?: number;
        offset?: number;
        search?: string
    }): Promise<UsersResponse> => {
        const { data } = await api.get('/admin/users', { params });
        return data;
    },

    getUser: async (userId: number): Promise<UsersResponse> => {
        const { data } = await api.get(`/admin/users/${userId}`);
        return data;
    },

    // Conversations
    getConversations: async (params?: {
        limit?: number;
        offset?: number;
        search?: string;
        user_id?: number;
        date_from?: string;
        date_to?: string;
        has_error?: boolean;
    }): Promise<ConversationsResponse> => {
        const { data } = await api.get('/admin/conversations', { params });
        return data;
    },

    getConversation: async (conversationId: number): Promise<ConversationDetail> => {
        const { data } = await api.get(`/admin/conversations/${conversationId}`);
        return data;
    },

    // Errors
    getErrors: async (params?: {
        limit?: number;
        offset?: number;
        date_from?: string;
        date_to?: string;
        search?: string;
    }): Promise<ConversationsResponse> => {
        const { data } = await api.get('/admin/errors', { params });
        return data;
    },
};

export default adminApi;
