/**
 * Activity chart component using Recharts
 */
import { useTranslation } from 'react-i18next';
import {
    AreaChart,
    Area,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Legend,
} from 'recharts';
import type { ActivityBucket } from '../types';
import './ActivityChart.css';

interface ActivityChartProps {
    data: ActivityBucket[];
    title: string;
}

export function ActivityChart({ data, title }: ActivityChartProps) {
    const { t } = useTranslation();

    const formattedData = data.map((item) => ({
        ...item,
        time: new Date(item.bucket).toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit'
        }),
    }));

    return (
        <div className="chart-card">
            <h3 className="chart-title">{title}</h3>
            <div className="chart-container">
                <ResponsiveContainer width="100%" height={280}>
                    <AreaChart data={formattedData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                        <defs>
                            <linearGradient id="colorMessages" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="var(--accent)" stopOpacity={0.3} />
                                <stop offset="95%" stopColor="var(--accent)" stopOpacity={0} />
                            </linearGradient>
                            <linearGradient id="colorErrors" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="var(--error)" stopOpacity={0.3} />
                                <stop offset="95%" stopColor="var(--error)" stopOpacity={0} />
                            </linearGradient>
                        </defs>
                        <CartesianGrid
                            strokeDasharray="3 3"
                            stroke="var(--border)"
                            vertical={false}
                        />
                        <XAxis
                            dataKey="time"
                            stroke="var(--text-muted)"
                            fontSize={12}
                            tickLine={false}
                            axisLine={false}
                        />
                        <YAxis
                            stroke="var(--text-muted)"
                            fontSize={12}
                            tickLine={false}
                            axisLine={false}
                            width={40}
                        />
                        <Tooltip
                            contentStyle={{
                                background: 'var(--card-bg)',
                                border: '1px solid var(--border)',
                                borderRadius: '8px',
                                boxShadow: '0 4px 12px var(--shadow)',
                            }}
                            labelStyle={{ color: 'var(--text)' }}
                        />
                        <Legend
                            wrapperStyle={{ paddingTop: '16px' }}
                        />
                        <Area
                            type="monotone"
                            dataKey="messages"
                            stroke="var(--accent)"
                            fillOpacity={1}
                            fill="url(#colorMessages)"
                            strokeWidth={2}
                            name={t('charts.messagesPerHour')}
                        />
                        <Area
                            type="monotone"
                            dataKey="errors"
                            stroke="var(--error)"
                            fillOpacity={1}
                            fill="url(#colorErrors)"
                            strokeWidth={2}
                            name={t('charts.errorsPerHour')}
                        />
                    </AreaChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
}
