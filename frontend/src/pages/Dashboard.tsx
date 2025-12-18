/**
 * Dashboard page - main overview
 */
import { useTranslation } from 'react-i18next';
import { useQuery } from '@tanstack/react-query';
import {
    Users,
    MessageSquare,
    Mail,
    AlertTriangle,
    Clock,
    UserCheck
} from 'lucide-react';
import { StatCard, ActivityChart, ToolsList } from '../components';
import { adminApi } from '../services';
import './Dashboard.css';

export function Dashboard() {
    const { t } = useTranslation();

    const { data: stats, isLoading: statsLoading } = useQuery({
        queryKey: ['stats'],
        queryFn: adminApi.getStats,
        refetchInterval: 30000,
    });

    const { data: activity } = useQuery({
        queryKey: ['activity'],
        queryFn: adminApi.getActivity,
        refetchInterval: 30000,
    });

    const { data: tools } = useQuery({
        queryKey: ['tools'],
        queryFn: () => adminApi.getTools(8),
        refetchInterval: 60000,
    });

    const formatMs = (ms: number) => {
        if (ms < 1000) return `${ms}ms`;
        return `${(ms / 1000).toFixed(1)}s`;
    };

    const formatRelativeTime = (dateStr: string | null) => {
        if (!dateStr) return '—';
        const date = new Date(dateStr);
        const now = new Date();
        const diffMs = now.getTime() - date.getTime();
        const diffMins = Math.floor(diffMs / 60000);

        if (diffMins < 1) return t('time.justNow');
        if (diffMins < 60) return t('time.minutesAgo', { count: diffMins });
        const diffHours = Math.floor(diffMins / 60);
        if (diffHours < 24) return t('time.hoursAgo', { count: diffHours });
        const diffDays = Math.floor(diffHours / 24);
        return t('time.daysAgo', { count: diffDays });
    };

    return (
        <div className="dashboard">
            <header className="page-header">
                <div>
                    <h1 className="page-title">{t('dashboard.title')}</h1>
                    <p className="page-subtitle">{t('dashboard.subtitle')}</p>
                </div>
            </header>

            <div className="stats-grid">
                <StatCard
                    title={t('stats.totalUsers')}
                    value={statsLoading ? '—' : stats?.total_users.toLocaleString() ?? '0'}
                    subtitle={`${stats?.active_users_today ?? 0} ${t('stats.activeToday').toLowerCase()}`}
                    icon={<Users size={20} />}
                />
                <StatCard
                    title={t('stats.conversations')}
                    value={statsLoading ? '—' : stats?.total_conversations.toLocaleString() ?? '0'}
                    icon={<MessageSquare size={20} />}
                />
                <StatCard
                    title={t('stats.messages24h')}
                    value={statsLoading ? '—' : stats?.messages_24h.toLocaleString() ?? '0'}
                    subtitle={`${stats?.assistant_messages_24h ?? 0} assistant`}
                    icon={<Mail size={20} />}
                />
                <StatCard
                    title={t('stats.errors24h')}
                    value={statsLoading ? '—' : stats?.errors_24h.toLocaleString() ?? '0'}
                    variant={stats?.errors_24h && stats.errors_24h > 0 ? 'error' : 'success'}
                    icon={<AlertTriangle size={20} />}
                />
                <StatCard
                    title={t('stats.avgResponseTime')}
                    value={statsLoading ? '—' : formatMs(stats?.avg_response_time_ms_7d ?? 0)}
                    subtitle={`${t('stats.p95')}: ${formatMs(stats?.p95_response_time_ms_7d ?? 0)}`}
                    icon={<Clock size={20} />}
                />
                <StatCard
                    title={t('stats.activeToday')}
                    value={statsLoading ? '—' : stats?.active_users_today.toLocaleString() ?? '0'}
                    subtitle={`${t('stats.lastActivity')}: ${formatRelativeTime(stats?.last_message_at ?? null)}`}
                    icon={<UserCheck size={20} />}
                    variant="success"
                />
            </div>

            <div className="charts-row">
                <div className="chart-col chart-col-lg">
                    {activity && (
                        <ActivityChart
                            data={activity.hourly}
                            title={t('charts.messageVolume')}
                        />
                    )}
                </div>
                <div className="chart-col chart-col-sm">
                    {tools && (
                        <ToolsList
                            tools={tools.tools}
                            title={t('charts.topTools')}
                        />
                    )}
                </div>
            </div>
        </div>
    );
}
