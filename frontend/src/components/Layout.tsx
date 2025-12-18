/**
 * Main layout with sidebar navigation
 */
import { useState, useEffect } from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useTheme } from '../contexts';
import {
    LayoutDashboard,
    MessageSquare,
    Users,
    AlertTriangle,
    Sun,
    Moon,
    Languages,
    Activity,
    Database,
    Clock,
    Zap
} from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { adminApi } from '../services';
import './Layout.css';

export function Layout() {
    const { t, i18n } = useTranslation();
    const { theme, toggleTheme } = useTheme();
    const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

    const { data: dbHealth, dataUpdatedAt } = useQuery({
        queryKey: ['dbHealth'],
        queryFn: adminApi.getDbHealth,
        refetchInterval: 1000, // Update every 1 second for real-time latency
        retry: 1,
    });

    // Track when data was last updated
    useEffect(() => {
        if (dataUpdatedAt) {
            setLastUpdated(new Date(dataUpdatedAt));
        }
    }, [dataUpdatedAt]);

    const toggleLanguage = () => {
        const newLang = i18n.language === 'en' ? 'de' : 'en';
        i18n.changeLanguage(newLang);
        localStorage.setItem('language', newLang);
    };

    const isConnected = dbHealth?.status === 'ok';
    const stats = dbHealth?.stats;

    // Format time ago
    const getTimeAgo = () => {
        const seconds = Math.floor((Date.now() - lastUpdated.getTime()) / 1000);
        if (seconds < 5) return 'just now';
        if (seconds < 60) return `${seconds}s ago`;
        return `${Math.floor(seconds / 60)}m ago`;
    };

    return (
        <div className="layout">
            <aside className="sidebar">
                <div className="sidebar-header">
                    <div className="logo">
                        <Activity className="logo-icon" />
                        <span className="logo-text">RÜKO Admin</span>
                    </div>
                </div>

                <nav className="nav">
                    <NavLink to="/" end className="nav-item">
                        <LayoutDashboard size={20} />
                        <span>{t('nav.dashboard')}</span>
                    </NavLink>
                    <NavLink to="/conversations" className="nav-item">
                        <MessageSquare size={20} />
                        <span>{t('nav.conversations')}</span>
                    </NavLink>
                    <NavLink to="/users" className="nav-item">
                        <Users size={20} />
                        <span>{t('nav.users')}</span>
                    </NavLink>
                    <NavLink to="/errors" className="nav-item">
                        <AlertTriangle size={20} />
                        <span>{t('nav.errors')}</span>
                    </NavLink>
                </nav>

                <div className="sidebar-footer">
                    {/* Status Panel */}
                    <div className="status-panel">
                        <div className="status-header">
                            <Database size={14} />
                            <span>System Status</span>
                            <span className={`status-indicator ${isConnected ? 'online' : 'offline'}`} />
                        </div>

                        <div className="status-items">
                            <div className="status-item">
                                <span className="status-label">
                                    <Zap size={12} />
                                    Latency
                                </span>
                                <span className={`status-value ${dbHealth?.latency_ms && dbHealth.latency_ms < 200 ? 'good' : 'warn'}`}>
                                    {dbHealth?.latency_ms ?? '—'}ms
                                </span>
                            </div>

                            {stats && (
                                <>
                                    <div className="status-item">
                                        <span className="status-label">
                                            <Users size={12} />
                                            Users
                                        </span>
                                        <span className="status-value">{stats.users}</span>
                                    </div>

                                    <div className="status-item">
                                        <span className="status-label">
                                            <MessageSquare size={12} />
                                            Messages
                                        </span>
                                        <span className="status-value">{stats.messages.toLocaleString()}</span>
                                    </div>

                                    <div className="status-item">
                                        <span className="status-label">
                                            <Clock size={12} />
                                            Last Hour
                                        </span>
                                        <span className="status-value highlight">{stats.messages_last_hour}</span>
                                    </div>

                                    {stats.errors > 0 && (
                                        <div className="status-item">
                                            <span className="status-label error">
                                                <AlertTriangle size={12} />
                                                Errors
                                            </span>
                                            <span className="status-value error">{stats.errors}</span>
                                        </div>
                                    )}
                                </>
                            )}
                        </div>

                        <div className="status-footer">
                            Updated {getTimeAgo()}
                        </div>
                    </div>

                    <div className="controls">
                        <button
                            onClick={toggleLanguage}
                            className="control-btn"
                            title={i18n.language === 'en' ? 'Deutsch' : 'English'}
                        >
                            <Languages size={18} />
                            <span>{i18n.language.toUpperCase()}</span>
                        </button>

                        <button
                            onClick={toggleTheme}
                            className="control-btn"
                            title={theme === 'light' ? t('theme.dark') : t('theme.light')}
                        >
                            {theme === 'light' ? <Moon size={18} /> : <Sun size={18} />}
                        </button>
                    </div>
                </div>
            </aside>

            <main className="main-content">
                <Outlet />
            </main>
        </div>
    );
}
