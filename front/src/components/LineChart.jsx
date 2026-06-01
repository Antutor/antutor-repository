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

    const baseData = history.length > 0 ? history : [{ turn: 0, Academic: 0, Market: 0, Macro: 0 }];

    // 겹치는 선이 보일 수 있도록 시각적인 오프셋(Jitter) 적용
    const chartData = baseData.map(point => {
        const newPoint = { ...point, AcademicLine: point.Academic, MarketLine: point.Market, MacroLine: point.Macro };
        
        const groups = {};
        [
            { key: 'AcademicLine', val: point.Academic },
            { key: 'MarketLine', val: point.Market },
            { key: 'MacroLine', val: point.Macro }
        ].forEach(v => {
            if (!groups[v.val]) groups[v.val] = [];
            groups[v.val].push(v.key);
        });

        Object.keys(groups).forEach(valStr => {
            const keys = groups[valStr];
            if (keys.length === 3) {
                newPoint[keys[0]] += 1.5;
                newPoint[keys[2]] -= 1.5;
            } else if (keys.length === 2) {
                newPoint[keys[0]] += 1.0;
                newPoint[keys[1]] -= 1.0;
            }
        });

        return newPoint;
    });

    // 1. Y축 최댓값 고정 (턴별 점수는 100점 만점)
    const yAxisMax = 100;

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
                            formatter={(value, name, props) => {
                                let originalValue = value;
                                if (name === t(language, 'chartAccuracy')) originalValue = props.payload.Academic;
                                if (name === t(language, 'chartPracticality')) originalValue = props.payload.Market;
                                if (name === t(language, 'chartInsight')) originalValue = props.payload.Macro;
                                return [originalValue, name];
                            }}
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
                            type="linear" 
                            dataKey="AcademicLine" 
                            name={t(language, 'chartAccuracy')}
                            stroke="var(--color-expert-academic)" 
                            strokeWidth={3} 
                            dot={{ r: 4, fill: 'var(--color-expert-academic)', strokeWidth: 2, stroke: '#fff' }} 
                            activeDot={{ r: 6, strokeWidth: 0 }} 
                            isAnimationActive={true} 
                            animationDuration={1000}
                        />
                        <Line 
                            type="linear" 
                            dataKey="MarketLine" 
                            name={t(language, 'chartPracticality')}
                            stroke="var(--color-expert-market)" 
                            strokeWidth={3} 
                            dot={{ r: 4, fill: 'var(--color-expert-market)', strokeWidth: 2, stroke: '#fff' }} 
                            activeDot={{ r: 6, strokeWidth: 0 }} 
                            isAnimationActive={true} 
                            animationDuration={1000}
                        />
                        <Line 
                            type="linear" 
                            dataKey="MacroLine" 
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
