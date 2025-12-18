/**
 * Reusable data table component
 */
import type { ReactNode } from 'react';
import { useTranslation } from 'react-i18next';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import './DataTable.css';

interface Column<T> {
    key: string;
    header: string;
    render?: (item: T) => ReactNode;
    className?: string;
}

interface DataTableProps<T> {
    data: T[];
    columns: Column<T>[];
    onRowClick?: (item: T) => void;
    emptyMessage?: string;
    loading?: boolean;
    pagination?: {
        total: number;
        limit: number;
        offset: number;
        onPageChange: (offset: number) => void;
    };
}

export function DataTable<T extends { id: number | string }>({
    data,
    columns,
    onRowClick,
    emptyMessage,
    loading,
    pagination,
}: DataTableProps<T>) {
    const { t } = useTranslation();

    if (loading) {
        return (
            <div className="table-loading">
                <div className="spinner" />
                <span>{t('common.loading')}</span>
            </div>
        );
    }

    if (data.length === 0) {
        return (
            <div className="table-empty">
                {emptyMessage || t('common.noData')}
            </div>
        );
    }

    const currentPage = pagination ? Math.floor(pagination.offset / pagination.limit) + 1 : 1;
    const totalPages = pagination ? Math.ceil(pagination.total / pagination.limit) : 1;

    return (
        <div className="table-wrapper">
            <div className="table-scroll">
                <table className="data-table">
                    <thead>
                        <tr>
                            {columns.map((col) => (
                                <th key={col.key} className={col.className}>
                                    {col.header}
                                </th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {data.map((item) => (
                            <tr
                                key={item.id}
                                onClick={() => onRowClick?.(item)}
                                className={onRowClick ? 'clickable' : ''}
                            >
                                {columns.map((col) => (
                                    <td key={col.key} className={col.className}>
                                        {col.render
                                            ? col.render(item)
                                            : String((item as Record<string, unknown>)[col.key] ?? '')}
                                    </td>
                                ))}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {pagination && totalPages > 1 && (
                <div className="table-pagination">
                    <span className="pagination-info">
                        {pagination.offset + 1} - {Math.min(pagination.offset + pagination.limit, pagination.total)} of {pagination.total}
                    </span>
                    <div className="pagination-controls">
                        <button
                            className="pagination-btn"
                            onClick={() => pagination.onPageChange(Math.max(0, pagination.offset - pagination.limit))}
                            disabled={pagination.offset === 0}
                        >
                            <ChevronLeft size={18} />
                        </button>
                        <span className="pagination-page">
                            {currentPage} / {totalPages}
                        </span>
                        <button
                            className="pagination-btn"
                            onClick={() => pagination.onPageChange(pagination.offset + pagination.limit)}
                            disabled={pagination.offset + pagination.limit >= pagination.total}
                        >
                            <ChevronRight size={18} />
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}
