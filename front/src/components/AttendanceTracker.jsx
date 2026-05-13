import React, { useState, useEffect } from 'react';
import { Calendar, CheckCircle2, Flame } from 'lucide-react';
import { t } from '../locales';

const AttendanceTracker = ({ language = 'ko' }) => {
    const [attendance, setAttendance] = useState([]);
    const [streak, setStreak] = useState(0);

    useEffect(() => {
        // Load attendance from localStorage
        const saved = localStorage.getItem('antutor_attendance');
        if (saved) {
            const dates = JSON.parse(saved);
            setAttendance(dates);
            calculateStreak(dates);
        } else {
            // First time: mark today as attended for demo
            const today = new Date().toISOString().split('T')[0];
            const initial = [today];
            localStorage.setItem('antutor_attendance', JSON.stringify(initial));
            setAttendance(initial);
            setStreak(1);
        }
    }, []);

    const calculateStreak = (dates) => {
        if (dates.length === 0) return 0;
        
        const sortedDates = [...dates].sort().reverse();
        let currentStreak = 0;
        let today = new Date();
        today.setHours(0, 0, 0, 0);

        let lastDate = new Date(sortedDates[0]);
        lastDate.setHours(0, 0, 0, 0);

        // If last attendance was not today or yesterday, streak is broken
        const diffDays = Math.floor((today - lastDate) / (1000 * 60 * 60 * 24));
        if (diffDays > 1) {
            setStreak(0);
            return;
        }

        // Count consecutive days
        for (let i = 0; i < sortedDates.length; i++) {
            const d1 = new Date(sortedDates[i]);
            d1.setHours(0, 0, 0, 0);
            
            if (i === 0) {
                currentStreak = 1;
            } else {
                const d2 = new Date(sortedDates[i-1]);
                d2.setHours(0, 0, 0, 0);
                const diff = (d2 - d1) / (1000 * 60 * 60 * 24);
                if (diff === 1) {
                    currentStreak++;
                } else if (diff > 1) {
                    break;
                }
            }
        }
        setStreak(currentStreak);
    };

    // Simple grid for the last 14 days
    const getCalendarDays = () => {
        const days = [];
        const today = new Date();
        for (let i = 13; i >= 0; i--) {
            const date = new Date();
            date.setDate(today.getDate() - i);
            const dateStr = date.toISOString().split('T')[0];
            days.push({
                dateStr,
                dayNum: date.getDate(),
                isAttended: attendance.includes(dateStr),
                isToday: dateStr === today.toISOString().split('T')[0]
            });
        }
        return days;
    };

    const calendarDays = getCalendarDays();

    return (
        <div className="attendance-tracker" style={{ 
            width: '100%', 
            marginTop: '20px',
            padding: '16px',
            backgroundColor: 'rgba(255, 255, 255, 0.4)',
            borderRadius: '24px',
            border: '1px solid rgba(255, 255, 255, 0.6)',
            boxShadow: '0 4px 15px rgba(0, 0, 0, 0.02)'
        }}>
            <div className="streak-card" style={{ 
                display: 'flex', 
                alignItems: 'center', 
                gap: '10px',
                marginBottom: '16px'
            }}>
                <div style={{ 
                    backgroundColor: 'rgba(255, 237, 213, 0.8)', 
                    padding: '8px', 
                    borderRadius: '12px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                }}>
                    <Flame size={20} color="#f97316" fill="#f97316" />
                </div>
                <div style={{ textAlign: 'left' }}>
                    <div style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)', fontWeight: '600' }}>
                        {t(language, 'attendance')}
                    </div>
                    <div style={{ fontSize: '1rem', fontWeight: '800', color: 'var(--color-deep-navy)' }}>
                        {t(language, 'studyStreak').replace('{n}', streak)}
                    </div>
                </div>
            </div>

            <div className="attendance-month" style={{ 
                fontSize: '0.8rem', 
                fontWeight: '700', 
                color: 'var(--color-text-secondary)',
                marginBottom: '10px',
                textAlign: 'left',
                paddingLeft: '2px'
            }}>
                {language === 'ko' ? `${new Date().getMonth() + 1}월` : new Date().toLocaleString('en-US', { month: 'long' })}
            </div>

            <div className="attendance-calendar-grid" style={{ 
                display: 'grid', 
                gridTemplateColumns: 'repeat(7, 1fr)', 
                gap: '6px' 
            }}>
                {calendarDays.map((day, idx) => (
                    <div key={idx} style={{ 
                        display: 'flex', 
                        flexDirection: 'column', 
                        alignItems: 'center', 
                        gap: '4px' 
                    }}>
                        <div style={{ 
                            width: '26px', 
                            height: '26px', 
                            borderRadius: '8px', 
                            display: 'flex', 
                            alignItems: 'center', 
                            justifyContent: 'center',
                            backgroundColor: day.isAttended ? 'var(--color-expert-market)' : 'rgba(255, 255, 255, 0.5)',
                            border: day.isToday ? '1.5px solid var(--color-expert-market)' : 'none',
                            transition: 'all 0.3s'
                        }}>
                            {day.isAttended ? (
                                <CheckCircle2 size={14} color="white" />
                            ) : (
                                <span style={{ fontSize: '0.6rem', color: 'var(--color-text-secondary)', fontWeight: '700' }}>
                                    {day.dayNum}
                                </span>
                            )}
                        </div>
                    </div>
                ))}
            </div>
            
            <div style={{ 
                marginTop: '15px', 
                fontSize: '0.75rem', 
                color: 'var(--color-expert-market)', 
                fontWeight: '700',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '5px'
            }}>
                <CheckCircle2 size={14} />
                {t(language, 'todayAttendance')}
            </div>
        </div>
    );
};

export default AttendanceTracker;
