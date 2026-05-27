import React from 'react';
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, Tooltip } from 'recharts';
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
                        tick={(props) => {
                            const { payload, x, y, textAnchor, stroke, radius, ...rest } = props;
                            let color = 'var(--color-text-secondary)';
                            if (payload.value === t(language, 'chartAccuracy')) {
                                color = 'var(--color-expert-academic)';
                            } else if (payload.value === t(language, 'chartPracticality')) {
                                color = 'var(--color-expert-market)';
                            } else if (payload.value === t(language, 'chartInsight')) {
                                color = 'var(--color-expert-macro)';
                            }
                            return (
                                <text 
                                    {...rest} 
                                    x={x} 
                                    y={y + (y > 150 ? 5 : -5)} 
                                    fill={color} 
                                    fontSize={isSidebar ? 10 : 12} 
                                    fontWeight={800} 
                                    textAnchor={textAnchor}
                                >
                                    {payload.value}
                                </text>
                            );
                        }}
                    />
                    <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />
                    <Tooltip 
                        content={({ active, payload, label }) => {
                            if (active && payload && payload.length) {
                                return (
                                    <div style={{
                                        background: 'rgba(255, 255, 255, 0.95)',
                                        backdropFilter: 'blur(8px)',
                                        border: '1px solid rgba(226, 232, 240, 0.8)',
                                        borderRadius: '16px',
                                        padding: '6px 12px',
                                        boxShadow: '0 4px 15px rgba(0, 0, 0, 0.08)',
                                        fontSize: '0.85rem',
                                        fontWeight: '600',
                                        color: '#1e293b',
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '6px'
                                    }}>
                                        <div style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: '#3b82f6' }}></div>
                                        <span>{label}: </span>
                                        <span style={{ color: '#3b82f6', fontWeight: '800' }}>{payload[0].value}</span>
                                    </div>
                                );
                            }
                            return null;
                        }} 
                        cursor={false}
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