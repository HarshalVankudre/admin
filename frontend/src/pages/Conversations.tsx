/**
 * Conversations page
 */
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useQuery } from '@tanstack/react-query';
import { DataTable } from '../components';
import { adminApi } from '../services';
import type { Conversation } from '../types';
import './Pages.css';

export function Conversations() {
    const { t } = useTranslation();
    const navigate = useNavigate();
    const [offset, setOffset] = useState(0);
    const limit = 20;

    const { data, isLoading } = useQuery({
        queryKey: ['conversations', offset],
        queryFn: () => adminApi.getConversations({ limit, offset }),
    });

    const columns = [
        {
            key: 'id',
            header: t('conversations.id'),
            className: 'numeric',
            render: (item: Conversation) => `#${item.id}`,
        },
        {
            key: 'display_name',
            header: t('conversations.user'),
            render: (item: Conversation) => item.display_name || item.email || '—',
        },
        {
            key: 'message_count',
            header: t('conversations.messages'),
            className: 'numeric',
        },
        {
            key: 'error_count',
            header: t('conversations.errors'),
            className: 'numeric',
            render: (item: Conversation) => (
                <span className={item.error_count > 0 ? 'badge error' : ''}>
                    {item.error_count}
                </span>
            ),
        },
        {
            key: 'avg_assistant_response_time_ms',
            header: t('conversations.avgResponse'),
            className: 'numeric',
            render: (item: Conversation) =>
                item.avg_assistant_response_time_ms > 0
                    ? `${item.avg_assistant_response_time_ms}ms`
                    : '—',
        },
        {
            key: 'last_message_at',
            header: t('conversations.lastMessage'),
            render: (item: Conversation) =>
                new Date(item.last_message_at).toLocaleString(),
        },
    ];

    return (
        <div className="page">
            <header className="page-header">
                <h1 className="page-title">{t('conversations.title')}</h1>
            </header>

            <DataTable
                data={data?.conversations || []}
                columns={columns}
                loading={isLoading}
                emptyMessage={t('conversations.noConversations')}
                onRowClick={(item) => navigate(`/conversations/${item.id}`)}
                pagination={
                    data
                        ? {
                            total: data.total,
                            limit: data.limit,
                            offset: data.offset,
                            onPageChange: setOffset,
                        }
                        : undefined
                }
            />
        </div>
    );
}
