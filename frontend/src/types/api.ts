/**
 * API response types for the admin dashboard.
 */

export interface Stats {
    generated_at: string;
    total_users: number;
    total_conversations: number;
    total_messages: number;
    messages_today: number;
    messages_24h: number;
    errors_24h: number;
    assistant_messages_24h: number;
    active_users_today: number;
    last_message_at: string | null;
    avg_response_time_ms_7d: number;
    p50_response_time_ms_7d: number;
    p95_response_time_ms_7d: number;
}

export interface ActivityBucket {
    bucket: string;
    messages: number;
    errors: number;
}

export interface Activity {
    generated_at: string;
    hourly: ActivityBucket[];
    daily: ActivityBucket[];
}

export interface Tool {
    tool: string;
    count: number;
}

export interface ToolsResponse {
    generated_at: string;
    tools: Tool[];
}

export interface User {
    id: number;
    ms_user_id: string;
    display_name: string | null;
    email: string | null;
    first_seen: string;
    last_active: string;
    conversation_count: number;
    message_count: number;
    error_count: number;
}

export interface UsersResponse {
    users: User[];
    total: number;
    limit: number;
    offset: number;
}

export interface Conversation {
    id: number;
    thread_id: string;
    user_id: number;
    started_at: string;
    last_message_at: string;
    message_count: number;
    display_name?: string;
    email?: string;
    error_count: number;
    avg_assistant_response_time_ms: number;
}

export interface ConversationsResponse {
    conversations: Conversation[];
    total: number;
    limit: number;
    offset: number;
}

export interface Message {
    id: number;
    conversation_id: number;
    role: 'user' | 'assistant';
    content: string;
    timestamp: string;
    response_time_ms: number | null;
    tools_used: string[] | null;
    sql_query: string | null;
    sql_results_count: number | null;
    error: string | null;
}

export interface ConversationDetail {
    conversation: Conversation & {
        total_messages: number;
        user_messages: number;
        assistant_messages: number;
        first_message_at: string;
    };
    messages: Message[];
}

export interface DbHealth {
    status: string;
    latency_ms: number;
    server_time: string;
}
