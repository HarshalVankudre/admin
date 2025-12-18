/**
 * Tools list component
 */
import { useTranslation } from 'react-i18next';
import type { Tool } from '../types';
import './ToolsList.css';

interface ToolsListProps {
    tools: Tool[];
    title: string;
}

export function ToolsList({ tools, title }: ToolsListProps) {
    const { t } = useTranslation();

    const maxCount = Math.max(...tools.map((t) => t.count), 1);

    return (
        <div className="tools-card">
            <h3 className="tools-title">{title}</h3>
            {tools.length === 0 ? (
                <div className="tools-empty">{t('common.noData')}</div>
            ) : (
                <div className="tools-list">
                    {tools.map((tool, index) => (
                        <div key={tool.tool} className="tool-item">
                            <div className="tool-rank">{index + 1}</div>
                            <div className="tool-info">
                                <div className="tool-name">{tool.tool}</div>
                                <div className="tool-bar-container">
                                    <div
                                        className="tool-bar"
                                        style={{ width: `${(tool.count / maxCount) * 100}%` }}
                                    />
                                </div>
                            </div>
                            <div className="tool-count">{tool.count.toLocaleString()}</div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
