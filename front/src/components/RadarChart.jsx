import React from 'react';
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, ResponsiveContainer } from 'recharts';
import { t } from '../locales';

function RadarScoreChart({ scores, isSidebar = false, language = 'ko' }) {
    if (!scores) return <div className="chart-placeholder">{t(language, 'radarNoData')}</div>;

    const labelMap = {
        Academic: t(language, 'chartAccuracy'),
        Market: t(language, 'chartPracticality'),
        Macro: t(language, 'chartInsight')
    };

    const data = Object.keys(scores)
        .filter(key => key !== 'Independence')
        .map(key => ({
            subject: labelMap[key] || key,
            A: scores[key],
            fullMark: 100,
        }));

    const height = isSidebar ? 220 : 350;
    const outerRadius = isSidebar ? "60%" : "80%";

    return (
        <div className={`radar-chart-container ${isSidebar ? 'sidebar-chart' : ''}`} style={{ width: '100%', height: `${height}px` }}>
            <ResponsiveContainer width="100%" height="100%">
                <RadarChart cx="50%" cy="50%" outerRadius={outerRadius} data={data}>
                    <defs>
                        <linearGradient id="sidebarRadarGradient" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.7}/>
                            <stop offset="95%" stopColor="#10b981" stopOpacity={0.4}/>
                        </linearGradient>
                    </defs>
                    <PolarGrid stroke="#e2e8f0" />
                    <PolarAngleAxis 
                        dataKey="subject" 
                        tick={{ fill: 'var(--color-text-secondary)', fontSize: isSidebar ? 10 : 12, fontWeight: 600 }}
                    />
                    <Radar
                        name="Score"
                        dataKey="A"
                        stroke="var(--color-expert-academic)"
                        strokeWidth={2}
                        fill="url(#sidebarRadarGradient)"
                        fillOpacity={0.7}
                        isAnimationActive={true}
                    />
                </RadarChart>
            </ResponsiveContainer>
        </div>
    );
}

export default RadarScoreChart;