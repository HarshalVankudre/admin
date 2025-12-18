/**
 * Conversation detail page with message search and filters
 */
import { useState, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useQuery } from '@tanstack/react-query';
import {
    ArrowLeft,
    User,
    Bot,
    AlertTriangle,
    Clock,
    Wrench,
    Search,
    Filter,
    X,
    ChevronDown
} from 'lucide-react';
import Markdown from 'react-markdown';
import { adminApi } from '../services';
import type { Message } from '../types';
import './ConversationDetail.css';

type RoleFilter = 'all' | 'user' | 'assistant';

export function ConversationDetail() {
    const { id } = useParams<{ id: string }>();
    const { t } = useTranslation();
    const navigate = useNavigate();

    // Search and filters
    const [searchQuery, setSearchQuery] = useState('');
    const [roleFilter, setRoleFilter] = useState<RoleFilter>('all');
    const [showErrorsOnly, setShowErrorsOnly] = useState(false);
    const [showFilters, setShowFilters] = useState(false);

    const { data, isLoading } = useQuery({
        queryKey: ['conversation', id],
        queryFn: () => adminApi.getConversation(Number(id)),
        enabled: !!id,
    });

    // Filter messages based on search and filters
    const filteredMessages = useMemo(() => {
        if (!data?.messages) return [];

        return data.messages.filter((msg) => {
            // Search filter
            if (searchQuery) {
                const query = searchQuery.toLowerCase();
                const matchesContent = msg.content.toLowerCase().includes(query);
                const matchesTools = msg.tools_used?.some(t => t.toLowerCase().includes(query));
                const matchesError = msg.error?.toLowerCase().includes(query);
                if (!matchesContent && !matchesTools && !matchesError) return false;
            }

            // Role filter
            if (roleFilter !== 'all' && msg.role !== roleFilter) return false;

            // Errors only filter
            if (showErrorsOnly && !msg.error) return false;

            return true;
        });
    }, [data?.messages, searchQuery, roleFilter, showErrorsOnly]);

    const hasActiveFilters = roleFilter !== 'all' || showErrorsOnly;
    const errorCount = data?.messages.filter(m => m.error).length || 0;

    const clearFilters = () => {
        setSearchQuery('');
        setRoleFilter('all');
        setShowErrorsOnly(false);
    };

    if (isLoading) {
        return (
            <div className="page">
                <div className="loading-state">{t('common.loading')}</div>
            </div>
        );
    }

    if (!data) {
        return (
            <div className="page">
                <div className="error-state">{t('common.error')}</div>
            </div>
        );
    }

    const { conversation } = data;

    return (
        <div className="page conversation-detail">
            <header className="detail-header">
                <button className="back-btn" onClick={() => navigate(-1)}>
                    <ArrowLeft size={20} />
                    <span>{t('common.back')}</span>
                </button>

                <div className="detail-info">
                    <h1 className="detail-title">
                        {t('conversations.title')} #{conversation.id}
                    </h1>
                    <div className="detail-meta">
                        <span>{conversation.display_name || conversation.email || 'Unknown User'}</span>
                        <span className="separator">•</span>
                        <span>{conversation.total_messages} {t('conversations.messages').toLowerCase()}</span>
                        {errorCount > 0 && (
                            <>
                                <span className="separator">•</span>
                                <span className="error-count">
                                    <AlertTriangle size={14} />
                                    {errorCount} {t('conversations.errors').toLowerCase()}
                                </span>
                            </>
                        )}
                    </div>
                </div>
            </header>

            {/* Search and Filter Bar */}
            <div className="message-toolbar">
                <div className="search-wrapper">
                    <Search size={18} className="search-icon" />
                    <input
                        type="text"
                        placeholder={t('common.search')}
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="search-input"
                    />
                    {searchQuery && (
                        <button onClick={() => setSearchQuery('')} className="clear-btn">
                            <X size={16} />
                        </button>
                    )}
                </div>

                <button
                    className={`filter-toggle ${showFilters ? 'active' : ''} ${hasActiveFilters ? 'has-filters' : ''}`}
                    onClick={() => setShowFilters(!showFilters)}
                >
                    <Filter size={18} />
                    <span>Filters</span>
                    {hasActiveFilters && <span className="filter-badge">!</span>}
                    <ChevronDown size={16} className={showFilters ? 'rotated' : ''} />
                </button>
            </div>

            {/* Filters Panel */}
            {showFilters && (
                <div className="message-filters">
                    <div className="filter-group">
                        <label className="filter-label">{t('messages.role')}</label>
                        <div className="filter-buttons">
                            <button
                                className={`filter-btn ${roleFilter === 'all' ? 'active' : ''}`}
                                onClick={() => setRoleFilter('all')}
                            >
                                {t('filters.all')}
                            </button>
                            <button
                                className={`filter-btn ${roleFilter === 'user' ? 'active' : ''}`}
                                onClick={() => setRoleFilter('user')}
                            >
                                <User size={14} /> User
                            </button>
                            <button
                                className={`filter-btn ${roleFilter === 'assistant' ? 'active' : ''}`}
                                onClick={() => setRoleFilter('assistant')}
                            >
                                <Bot size={14} /> Assistant
                            </button>
                        </div>
                    </div>

                    <div className="filter-group">
                        <label className="filter-label">{t('filters.hasErrors')}</label>
                        <button
                            className={`filter-btn error-btn ${showErrorsOnly ? 'active' : ''}`}
                            onClick={() => setShowErrorsOnly(!showErrorsOnly)}
                        >
                            <AlertTriangle size={14} />
                            {showErrorsOnly ? t('filters.withErrors') : t('filters.all')}
                        </button>
                    </div>

                    {hasActiveFilters && (
                        <button onClick={clearFilters} className="clear-filters-btn">
                            <X size={14} />
                            {t('filters.clear')}
                        </button>
                    )}
                </div>
            )}

            {/* Results count */}
            {(searchQuery || hasActiveFilters) && (
                <div className="results-count">
                    {filteredMessages.length} of {data.messages.length} messages
                    {searchQuery && <span> matching "{searchQuery}"</span>}
                </div>
            )}

            {/* Messages */}
            <div className="messages-container">
                {filteredMessages.length === 0 ? (
                    <div className="no-messages">
                        {t('messages.noMessages')}
                    </div>
                ) : (
                    filteredMessages.map((msg) => (
                        <MessageCard key={msg.id} message={msg} searchQuery={searchQuery} />
                    ))
                )}
            </div>
        </div>
    );
}

// Separate component for message card
interface MessageCardProps {
    message: Message;
    searchQuery: string;
}

function MessageCard({ message: msg, searchQuery }: MessageCardProps) {
    // Highlight search matches in content
    const getHighlightedContent = () => {
        if (!searchQuery) return msg.content;

        // Escape special regex characters in search query
        const escaped = searchQuery.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        const regex = new RegExp(`(${escaped})`, 'gi');

        // Replace matches with markdown bold + highlight span
        return msg.content.replace(regex, '==$1==');
    };

    return (
        <div className={`message ${msg.role} ${msg.error ? 'has-error' : ''}`}>
            <div className="message-avatar">
                {msg.role === 'user' ? <User size={20} /> : <Bot size={20} />}
            </div>

            <div className="message-content">
                <div className="message-header">
                    <span className="message-role">{msg.role}</span>
                    <span className="message-time">
                        {new Date(msg.timestamp).toLocaleString()}
                    </span>
                    {msg.response_time_ms && (
                        <span className="message-response-time">
                            <Clock size={12} />
                            {msg.response_time_ms}ms
                        </span>
                    )}
                </div>

                <div className="message-text markdown-content">
                    <Markdown
                        components={{
                            // Style links
                            a: ({ children, href }) => (
                                <a href={href} target="_blank" rel="noopener noreferrer">
                                    {children}
                                </a>
                            ),
                            // Highlight search matches (using == syntax)
                            p: ({ children }) => {
                                if (typeof children === 'string' && children.includes('==')) {
                                    const parts = children.split(/==(.*?)==/g);
                                    return (
                                        <p>
                                            {parts.map((part, i) =>
                                                i % 2 === 1 ? <mark key={i} className="highlight">{part}</mark> : part
                                            )}
                                        </p>
                                    );
                                }
                                return <p>{children}</p>;
                            }
                        }}
                    >
                        {getHighlightedContent()}
                    </Markdown>
                </div>

                {msg.tools_used && msg.tools_used.length > 0 && (
                    <div className="message-tools">
                        <Wrench size={14} />
                        <span>{msg.tools_used.join(', ')}</span>
                    </div>
                )}

                {msg.error && (
                    <div className="message-error">
                        <AlertTriangle size={14} />
                        <span>{msg.error}</span>
                    </div>
                )}
            </div>
        </div>
    );
}

