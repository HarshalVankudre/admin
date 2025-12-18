/**
 * Errors page - messages with errors
 */
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useQuery } from '@tanstack/react-query';
import { DataTable } from '../components';
import { adminApi } from '../services';
import './Pages.css';

interface ErrorMessage {
    id: number;
    conversation_id: number;
    role: string;
    content: string;
    timestamp: string;
    error: string;
    display_name?: string;
}

export function Errors() {
    const { t } = useTranslation();
    const [offset, setOffset] = useState(0);
    const limit = 20;

    const { data, isLoading } = useQuery({
        queryKey: ['errors', offset],
        queryFn: () => adminApi.getErrors({ limit, offset }),
    });

    const columns = [
        {
            key: 'id',
            header: t('messages.title'),
            className: 'numeric',
            render: (item: ErrorMessage) => `#${item.id}`,
        },
        {
            key: 'display_name',
            header: t('conversations.user'),
            render: (item: ErrorMessage) => item.display_name || '—',
        },
        {
            key: 'content',
            header: t('messages.content'),
            className: 'truncate',
            render: (item: ErrorMessage) => item.content.slice(0, 100) + '...',
        },
        {
            key: 'error',
            header: t('messages.error'),
            className: 'truncate',
            render: (item: ErrorMessage) => (
                <span className="badge error">{item.error}</span>
            ),
        },
        {
            key: 'timestamp',
            header: t('messages.timestamp'),
            render: (item: ErrorMessage) =>
                new Date(item.timestamp).toLocaleString(),
        },
    ];

    return (
        <div className="page">
            <header className="page-header">
                <h1 className="page-title">{t('nav.errors')}</h1>
            </header>

            <DataTable
                data={(data as unknown as { messages: ErrorMessage[] })?.messages || []}
                columns={columns}
                loading={isLoading}
                emptyMessage={t('messages.noMessages')}
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
