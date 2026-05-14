import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { t } from '../locales';

function LineScoreChart({ history, language = 'ko' }) {
    if (!history || history.length === 0) {
        return (
            <div style={{ 
                height: '220px', 
                display: 'flex', 
                flexDirection: 'column',
                alignItems: 'center', 
                justifyContent: 'center', 
                color: 'var(--color-text-secondary)', 
                fontSize: '0.85rem',
                textAlign: 'center',
                padding: '0 20px',
                opacity: 0.7
            }}>
                <div style={{ marginBottom: '10px', fontSize: '1.2rem' }}>📈</div>
                {t(language, 'chartEmptyMsg').split('\\n').map((line, i) => (
                    <span key={i}>{line}{i === 0 && <br />}</span>
                ))}
            </div>
        );
    }

    const chartData = history.length > 0 ? history : [{ turn: 0, Academic: 0, Market: 0, Macro: 0 }];

    // 1. Y축 최댓값 동적 계산 (누적 점수에 따라 100 단위로 올림)
    const maxScore = Math.max(
        ...chartData.map(d => Math.max(d.Academic || 0, d.Market || 0, d.Macro || 0)),
        100
    );
    const yAxisMax = Math.ceil((maxScore + 50) / 100) * 100;

    // 2. 가로 스크롤을 위한 너비 계산 (한 턴당 최소 60px 확보)
    const minChartWidth = Math.max(260, chartData.length * 60);

    return (
        <div className="line-chart-wrapper" style={{ 
            width: '100%', 
            overflowX: 'auto', 
            overflowY: 'hidden',
            marginTop: '10px',
            backgroundColor: 'rgba(255,255,255,0.3)',
            borderRadius: '16px',
            padding: '10px 0',
            scrollbarWidth: 'thin',
            scrollbarColor: 'var(--color-expert-academic) transparent'
        }}>
            <div style={{ width: `${minChartWidth}px`, height: '220px' }}>
                <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={chartData} margin={{ top: 10, right: 30, left: -20, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                        <XAxis 
                            dataKey="turn" 
                            tick={{ fontSize: 10, fill: 'var(--color-text-secondary)', fontWeight: 500 }}
                            axisLine={false}
                            tickLine={false}
                            label={{ value: t(language, 'chartTurn'), position: 'insideBottomRight', offset: -5, fontSize: 10 }}
                        />
                        <YAxis 
                            domain={[0, yAxisMax]} 
                            tick={{ fontSize: 10, fill: 'var(--color-text-secondary)', fontWeight: 500 }}
                            axisLine={false}
                            tickLine={false}
                        />
                        <Tooltip 
                            contentStyle={{ 
                                borderRadius: '16px', 
                                border: 'none', 
                                boxShadow: '0 10px 25px rgba(0,0,0,0.1)', 
                                fontSize: '11px',
                                padding: '12px',
                                backgroundColor: 'rgba(255, 255, 255, 0.95)',
                                backdropFilter: 'blur(5px)'
                            }}
                        />
                        <Legend 
                            iconType="circle" 
                            wrapperStyle={{ fontSize: '10px', paddingTop: '10px', fontWeight: 600 }}
                        />
                        <Line 
                            type="monotone" 
                            dataKey="Academic" 
                            name={t(language, 'chartAccuracy')}
                            stroke="var(--color-expert-academic)" 
                            strokeWidth={3} 
                            dot={{ r: 4, fill: 'var(--color-expert-academic)', strokeWidth: 2, stroke: '#fff' }} 
                            activeDot={{ r: 6, strokeWidth: 0 }} 
                            isAnimationActive={true} 
                            animationDuration={1000}
                        />
                        <Line 
                            type="monotone" 
                            dataKey="Market" 
                            name={t(language, 'chartPracticality')}
                            stroke="var(--color-expert-market)" 
                            strokeWidth={3} 
                            dot={{ r: 4, fill: 'var(--color-expert-market)', strokeWidth: 2, stroke: '#fff' }} 
                            activeDot={{ r: 6, strokeWidth: 0 }} 
                            isAnimationActive={true} 
                            animationDuration={1000}
                        />
                        <Line 
                            type="monotone" 
                            dataKey="Macro" 
                            name={t(language, 'chartInsight')}
                            stroke="var(--color-expert-macro)" 
                            strokeWidth={3} 
                            dot={{ r: 4, fill: 'var(--color-expert-macro)', strokeWidth: 2, stroke: '#fff' }} 
                            activeDot={{ r: 6, strokeWidth: 0 }} 
                            isAnimationActive={true} 
                            animationDuration={1000}
                        />
                    </LineChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
}

export default LineScoreChart;
