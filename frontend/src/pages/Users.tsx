/**
 * Users page
 */
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useQuery } from '@tanstack/react-query';
import { DataTable } from '../components';
import { adminApi } from '../services';
import type { User } from '../types';
import './Pages.css';

export function UsersPage() {
    const { t } = useTranslation();
    const [offset, setOffset] = useState(0);
    const limit = 20;

    const { data, isLoading } = useQuery({
        queryKey: ['users', offset],
        queryFn: () => adminApi.getUsers({ limit, offset }),
    });

    const columns = [
        {
            key: 'id',
            header: t('users.id'),
            className: 'numeric',
            render: (item: User) => `#${item.id}`,
        },
        {
            key: 'display_name',
            header: t('users.name'),
            render: (item: User) => item.display_name || '—',
        },
        {
            key: 'email',
            header: t('users.email'),
            className: 'truncate',
            render: (item: User) => item.email || '—',
        },
        {
            key: 'conversation_count',
            header: t('users.conversations'),
            className: 'numeric',
        },
        {
            key: 'message_count',
            header: t('users.messages'),
            className: 'numeric',
        },
        {
            key: 'error_count',
            header: t('users.errors'),
            className: 'numeric',
            render: (item: User) => (
                <span className={item.error_count > 0 ? 'badge error' : ''}>
                    {item.error_count}
                </span>
            ),
        },
        {
            key: 'last_active',
            header: t('users.lastActive'),
            render: (item: User) =>
                new Date(item.last_active).toLocaleString(),
        },
    ];

    return (
        <div className="page">
            <header className="page-header">
                <h1 className="page-title">{t('users.title')}</h1>
            </header>

            <DataTable
                data={data?.users || []}
                columns={columns}
                loading={isLoading}
                emptyMessage={t('users.noUsers')}
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
