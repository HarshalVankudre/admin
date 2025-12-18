/**
 * Conversations page with filters and search
 */
import { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useQuery } from '@tanstack/react-query';
import {
    Search,
    Filter,
    X,
    ChevronDown,
    MessageSquare,
    AlertTriangle,
    Clock,
    User,
    Calendar
} from 'lucide-react';
import { DataTable } from '../components';
import { adminApi } from '../services';
import type { Conversation } from '../types';
import './Conversations.css';

type ErrorFilter = 'all' | 'with_errors' | 'without_errors';

export function Conversations() {
    const { t } = useTranslation();
    const navigate = useNavigate();

    // Pagination
    const [offset, setOffset] = useState(0);
    const limit = 20;

    // Filters
    const [search, setSearch] = useState('');
    const [searchInput, setSearchInput] = useState('');
    const [dateFrom, setDateFrom] = useState('');
    const [dateTo, setDateTo] = useState('');
    const [errorFilter, setErrorFilter] = useState<ErrorFilter>('all');
    const [showFilters, setShowFilters] = useState(false);

    // Build query params
    const queryParams = useMemo(() => {
        const params: Record<string, unknown> = { limit, offset };
        if (search) params.search = search;
        if (dateFrom) params.date_from = dateFrom;
        if (dateTo) params.date_to = dateTo;
        if (errorFilter === 'with_errors') params.has_error = true;
        if (errorFilter === 'without_errors') params.has_error = false;
        return params;
    }, [limit, offset, search, dateFrom, dateTo, errorFilter]);

    const { data, isLoading } = useQuery({
        queryKey: ['conversations', queryParams],
        queryFn: () => adminApi.getConversations(queryParams as Parameters<typeof adminApi.getConversations>[0]),
    });

    const handleSearch = (e: React.FormEvent) => {
        e.preventDefault();
        setSearch(searchInput);
        setOffset(0);
    };

    const clearSearch = () => {
        setSearchInput('');
        setSearch('');
        setOffset(0);
    };

    const clearFilters = () => {
        setDateFrom('');
        setDateTo('');
        setErrorFilter('all');
        setOffset(0);
    };

    const hasActiveFilters = dateFrom || dateTo || errorFilter !== 'all';

    const formatDuration = (startStr: string, endStr: string) => {
        const start = new Date(startStr);
        const end = new Date(endStr);
        const diffMs = end.getTime() - start.getTime();
        const diffMins = Math.floor(diffMs / 60000);
        if (diffMins < 1) return '< 1 min';
        if (diffMins < 60) return `${diffMins} min`;
        const hours = Math.floor(diffMins / 60);
        const mins = diffMins % 60;
        return `${hours}h ${mins}m`;
    };

    const formatRelativeTime = (dateStr: string) => {
        const date = new Date(dateStr);
        const now = new Date();
        const diffMs = now.getTime() - date.getTime();
        const diffMins = Math.floor(diffMs / 60000);

        if (diffMins < 1) return t('time.justNow');
        if (diffMins < 60) return t('time.minutesAgo', { count: diffMins });
        const diffHours = Math.floor(diffMins / 60);
        if (diffHours < 24) return t('time.hoursAgo', { count: diffHours });
        const diffDays = Math.floor(diffHours / 24);
        if (diffDays === 1) return t('time.yesterday');
        return t('time.daysAgo', { count: diffDays });
    };

    const columns = [
        {
            key: 'id',
            header: t('conversations.id'),
            className: 'numeric',
            render: (item: Conversation) => (
                <span className="conv-id">#{item.id}</span>
            ),
        },
        {
            key: 'user',
            header: t('conversations.user'),
            render: (item: Conversation) => (
                <div className="user-cell">
                    <div className="user-avatar">
                        <User size={16} />
                    </div>
                    <div className="user-info">
                        <span className="user-name">{item.display_name || 'Unknown'}</span>
                        {item.email && <span className="user-email">{item.email}</span>}
                    </div>
                </div>
            ),
        },
        {
            key: 'stats',
            header: t('conversations.messages'),
            render: (item: Conversation) => (
                <div className="stats-cell">
                    <span className="stat-item">
                        <MessageSquare size={14} />
                        {item.message_count}
                    </span>
                    {item.error_count > 0 && (
                        <span className="stat-item error">
                            <AlertTriangle size={14} />
                            {item.error_count}
                        </span>
                    )}
                </div>
            ),
        },
        {
            key: 'response',
            header: t('conversations.avgResponse'),
            className: 'numeric',
            render: (item: Conversation) => (
                <span className="response-time">
                    {item.avg_assistant_response_time_ms > 0 ? (
                        <>
                            <Clock size={14} />
                            {item.avg_assistant_response_time_ms}ms
                        </>
                    ) : (
                        '—'
                    )}
                </span>
            ),
        },
        {
            key: 'duration',
            header: t('conversations.duration'),
            render: (item: Conversation) => (
                <span className="duration">
                    {formatDuration(item.started_at, item.last_message_at)}
                </span>
            ),
        },
        {
            key: 'time',
            header: t('conversations.lastMessage'),
            render: (item: Conversation) => (
                <div className="time-cell">
                    <span className="time-relative">{formatRelativeTime(item.last_message_at)}</span>
                    <span className="time-absolute">
                        {new Date(item.last_message_at).toLocaleDateString()}
                    </span>
                </div>
            ),
        },
    ];

    return (
        <div className="page conversations-page">
            <header className="page-header">
                <div className="header-content">
                    <h1 className="page-title">{t('conversations.title')}</h1>
                    {data && (
                        <span className="total-count">
                            {data.total} {t('conversations.title').toLowerCase()}
                        </span>
                    )}
                </div>
            </header>

            {/* Search and Filter Bar */}
            <div className="toolbar">
                <form className="search-form" onSubmit={handleSearch}>
                    <div className="search-input-wrapper">
                        <Search size={18} className="search-icon" />
                        <input
                            type="text"
                            placeholder={t('common.search')}
                            value={searchInput}
                            onChange={(e) => setSearchInput(e.target.value)}
                            className="search-input"
                        />
                        {searchInput && (
                            <button type="button" onClick={clearSearch} className="clear-btn">
                                <X size={16} />
                            </button>
                        )}
                    </div>
                    <button type="submit" className="search-btn">
                        {t('common.search').replace('...', '')}
                    </button>
                </form>

                <button
                    className={`filter-toggle ${showFilters ? 'active' : ''} ${hasActiveFilters ? 'has-filters' : ''}`}
                    onClick={() => setShowFilters(!showFilters)}
                >
                    <Filter size={18} />
                    <span>Filters</span>
                    {hasActiveFilters && <span className="filter-badge">{[dateFrom, dateTo, errorFilter !== 'all'].filter(Boolean).length}</span>}
                    <ChevronDown size={16} className={showFilters ? 'rotated' : ''} />
                </button>
            </div>

            {/* Filters Panel */}
            {showFilters && (
                <div className="filters-panel">
                    <div className="filter-group">
                        <label className="filter-label">
                            <Calendar size={14} />
                            {t('filters.dateFrom')}
                        </label>
                        <input
                            type="date"
                            value={dateFrom}
                            onChange={(e) => { setDateFrom(e.target.value); setOffset(0); }}
                            className="filter-input"
                        />
                    </div>

                    <div className="filter-group">
                        <label className="filter-label">
                            <Calendar size={14} />
                            {t('filters.dateTo')}
                        </label>
                        <input
                            type="date"
                            value={dateTo}
                            onChange={(e) => { setDateTo(e.target.value); setOffset(0); }}
                            className="filter-input"
                        />
                    </div>

                    <div className="filter-group">
                        <label className="filter-label">
                            <AlertTriangle size={14} />
                            {t('filters.hasErrors')}
                        </label>
                        <select
                            value={errorFilter}
                            onChange={(e) => { setErrorFilter(e.target.value as ErrorFilter); setOffset(0); }}
                            className="filter-select"
                        >
                            <option value="all">{t('filters.all')}</option>
                            <option value="with_errors">{t('filters.withErrors')}</option>
                            <option value="without_errors">{t('filters.withoutErrors')}</option>
                        </select>
                    </div>

                    {hasActiveFilters && (
                        <button onClick={clearFilters} className="clear-filters-btn">
                            <X size={14} />
                            {t('filters.clear')}
                        </button>
                    )}
                </div>
            )}

            {/* Active Filters Display */}
            {(search || hasActiveFilters) && (
                <div className="active-filters">
                    {search && (
                        <span className="filter-tag">
                            Search: "{search}"
                            <button onClick={clearSearch}><X size={12} /></button>
                        </span>
                    )}
                    {dateFrom && (
                        <span className="filter-tag">
                            From: {dateFrom}
                            <button onClick={() => setDateFrom('')}><X size={12} /></button>
                        </span>
                    )}
                    {dateTo && (
                        <span className="filter-tag">
                            To: {dateTo}
                            <button onClick={() => setDateTo('')}><X size={12} /></button>
                        </span>
                    )}
                    {errorFilter !== 'all' && (
                        <span className="filter-tag">
                            {errorFilter === 'with_errors' ? t('filters.withErrors') : t('filters.withoutErrors')}
                            <button onClick={() => setErrorFilter('all')}><X size={12} /></button>
                        </span>
                    )}
                </div>
            )}

            {/* Data Table */}
            <DataTable
                data={data?.conversations || []}
                columns={columns}
                loading={isLoading}
                emptyMessage={search || hasActiveFilters ? t('conversations.noMatchingFilters') : t('conversations.noConversations')}
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
