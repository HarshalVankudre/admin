/**
 * Conversation detail page
 */
import { useParams, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useQuery } from '@tanstack/react-query';
import { ArrowLeft, User, Bot, AlertTriangle, Clock, Wrench } from 'lucide-react';
import { adminApi } from '../services';
import './ConversationDetail.css';

export function ConversationDetail() {
    const { id } = useParams<{ id: string }>();
    const { t } = useTranslation();
    const navigate = useNavigate();

    const { data, isLoading } = useQuery({
        queryKey: ['conversation', id],
        queryFn: () => adminApi.getConversation(Number(id)),
        enabled: !!id,
    });

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

    const { conversation, messages } = data;

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
                        {conversation.error_count > 0 && (
                            <>
                                <span className="separator">•</span>
                                <span className="error-count">
                                    <AlertTriangle size={14} />
                                    {conversation.error_count} {t('conversations.errors').toLowerCase()}
                                </span>
                            </>
                        )}
                    </div>
                </div>
            </header>

            <div className="messages-container">
                {messages.map((msg) => (
                    <div
                        key={msg.id}
                        className={`message ${msg.role} ${msg.error ? 'has-error' : ''}`}
                    >
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

                            <div className="message-text">{msg.content}</div>

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
                ))}
            </div>
        </div>
    );
}
