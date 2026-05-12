import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

function LineScoreChart({ history }) {
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
                학습을 진행하면<br/>점수 변화가 기록됩니다.
            </div>
        );
    }

    // Ensure turn 0 is included if not present (baseline)
    const chartData = history.length > 0 ? history : [{ turn: 0, Academic: 0, Market: 0, Macro: 0 }];

    return (
        <div className="line-chart-container" style={{ width: '100%', height: '220px', marginTop: '10px' }}>
            <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                    <XAxis 
                        dataKey="turn" 
                        tick={{ fontSize: 10, fill: 'var(--color-text-secondary)', fontWeight: 500 }}
                        axisLine={false}
                        tickLine={false}
                        label={{ value: '턴', position: 'insideBottomRight', offset: -5, fontSize: 10 }}
                    />
                    <YAxis 
                        domain={[0, 100]} 
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
                        name="정확성" 
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
                        name="현실성" 
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
                        name="통찰력" 
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
    );
}

export default LineScoreChart;
