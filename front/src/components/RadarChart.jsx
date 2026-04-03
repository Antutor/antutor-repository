import React from 'react';
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, ResponsiveContainer } from 'recharts';

function RadarScoreChart({ scores }) {
    // Return a message if no data is provided
    if (!scores) return <div>No data available.</div>;

    // Convert backend data into chart format, filtering out 'Independence'
    const data = Object.keys(scores)
        .filter(key => key !== 'Independence')
        .map(key => ({
            subject: key,
            A: scores[key],
            fullMark: 100,
        }));

    return (
        <div style={{ width: '100%', height: '350px' }}>
            <ResponsiveContainer width="100%" height="100%">
                <RadarChart cx="50%" cy="50%" outerRadius="80%" data={data}>
                    <PolarGrid />
                    <PolarAngleAxis dataKey="subject" />
                    <Radar
                        name="Score"
                        dataKey="A"
                        stroke="#8884d8"
                        fill="#8884d8"
                        fillOpacity={0.6}
                    />
                </RadarChart>
            </ResponsiveContainer>
        </div>
    );
}

export default RadarScoreChart;