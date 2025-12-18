/**
 * Main layout with sidebar navigation
 */
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
    Activity
} from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { adminApi } from '../services';
import './Layout.css';

export function Layout() {
    const { t, i18n } = useTranslation();
    const { theme, toggleTheme } = useTheme();

    const { data: dbHealth } = useQuery({
        queryKey: ['dbHealth'],
        queryFn: adminApi.getDbHealth,
        refetchInterval: 30000,
        retry: 1,
    });

    const toggleLanguage = () => {
        const newLang = i18n.language === 'en' ? 'de' : 'en';
        i18n.changeLanguage(newLang);
        localStorage.setItem('language', newLang);
    };

    const isConnected = dbHealth?.status === 'ok';

    return (
        <div className="layout">
            <aside className="sidebar">
                <div className="sidebar-header">
                    <div className="logo">
                        <Activity className="logo-icon" />
                        <span className="logo-text">Ruko Admin</span>
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
                    <div className={`db-status ${isConnected ? 'connected' : 'disconnected'}`}>
                        <span className="status-dot" />
                        <span className="status-text">
                            {isConnected ? t('dashboard.connected') : t('dashboard.disconnected')}
                        </span>
                        {dbHealth?.latency_ms && (
                            <span className="latency">{dbHealth.latency_ms}ms</span>
                        )}
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
