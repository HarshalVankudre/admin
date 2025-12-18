/**
 * Stat card component for dashboard KPIs
 */
import type { ReactNode } from 'react';
import './StatCard.css';

interface StatCardProps {
    title: string;
    value: string | number;
    subtitle?: string;
    icon: ReactNode;
    trend?: 'up' | 'down' | 'neutral';
    variant?: 'default' | 'success' | 'warning' | 'error';
}

export function StatCard({
    title,
    value,
    subtitle,
    icon,
    variant = 'default'
}: StatCardProps) {
    return (
        <div className={`stat-card ${variant}`}>
            <div className="stat-header">
                <span className="stat-title">{title}</span>
                <div className="stat-icon">{icon}</div>
            </div>
            <div className="stat-value">{value}</div>
            {subtitle && <div className="stat-subtitle">{subtitle}</div>}
        </div>
    );
}
