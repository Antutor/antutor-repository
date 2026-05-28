/* eslint-disable no-unused-vars */
import React, { useEffect, useState } from 'react';
import { 
  Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, Tooltip
} from 'recharts';
import { X, Award, AlertCircle, ArrowRight } from 'lucide-react';
import './SummaryModal.css';
import { t } from './locales';

const SummaryModal = ({ isOpen, onClose, helpCountLevel1, helpCountLevel2, helpCountLevel3, reportData, language }) => {
  const [shouldRender, setShouldRender] = useState(false);
  const [isActive, setIsActive] = useState(false);

  let radarData = [
    { subject: t(language, 'accuracy'), value: 0, fullMark: 100 },
    { subject: t(language, 'practicality'), value: 0, fullMark: 100 },
    { subject: t(language, 'insight'), value: 0, fullMark: 100 },
  ];
  let insightText = t(language, 'noEvalData');
  let maxScore = 100;

  if (reportData && reportData.growth_visualization) {
      const gv = reportData.growth_visualization;
      const calcAverage = (arr) => arr && arr.length > 0 ? Math.round(arr.reduce((sum, val) => sum + val, 0) / arr.length * 10) / 10 : 0;
      
      maxScore = 100;

      radarData = [
        { subject: t(language, 'accuracy'), value: calcAverage(gv.Academic), fullMark: maxScore },
        { subject: t(language, 'practicality'), value: calcAverage(gv.Market), fullMark: maxScore },
        { subject: t(language, 'insight'), value: calcAverage(gv.Macro), fullMark: maxScore },
      ];
      insightText = reportData.educational_insights || insightText;
  }

  // Handle animation mounting/unmounting
  useEffect(() => {
    if (isOpen) {
      setShouldRender(true);
      setTimeout(() => setIsActive(true), 10);
    } else {
      setIsActive(false);
      setTimeout(() => setShouldRender(false), 400); // Wait for fade out
    }
  }, [isOpen]);

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div style={{
          background: 'rgba(255, 255, 255, 0.95)',
          border: '1px solid #e2e8f0',
          borderRadius: '16px',
          padding: '8px 14px',
          boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
          textAlign: 'center'
        }}>
          <p style={{ margin: '0 0 4px 0', fontSize: '0.85rem', color: 'var(--color-text-secondary)', fontWeight: '600' }}>{label}</p>
          <p style={{ margin: 0, fontSize: '1.1rem', color: 'var(--color-expert-academic)', fontWeight: '800' }}>
            {payload[0].value} <span style={{ fontSize: '0.75rem', fontWeight: '500', color: '#94a3b8' }}>pts</span>
          </p>
        </div>
      );
    }
    return null;
  };

  if (!shouldRender) return null;

  return (
    <div className={`summary-overlay ${isActive ? 'active' : ''}`} onClick={onClose}>
      <div 
        className={`summary-modal ${isActive ? 'active' : ''}`} 
        onClick={(e) => e.stopPropagation()}
      >
        <button className="summary-close-btn" onClick={onClose}>
          <X size={24} />
        </button>

        <div className="summary-header">
          <h2>{t(language, 'sessionSummary')}</h2>
          <p>{t(language, 'achievementAnalysis')}</p>
        </div>

        <div className="summary-grid">
          {/* Radar Chart Section */}
          <div className="summary-section radar-section">
            <h3>{t(language, 'knowledgeLevel')}</h3>
            <div style={{ color: 'black', fontWeight: '800', fontSize: '1rem', marginBottom: '5px' }}>
              {language === 'ko' ? '평균 점수' : 'Average Score'}
            </div>
            <div className="chart-container">
              <ResponsiveContainer width="100%" height={260}>
                <RadarChart cx="50%" cy="50%" outerRadius="70%" data={radarData}>
                  <defs>
                    <linearGradient id="colorRadar" x1="0" y1="0" x2="1" y2="1">
                      <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.6}/>
                      <stop offset="50%" stopColor="#60a5fa" stopOpacity={0.4}/>
                      <stop offset="95%" stopColor="#34d399" stopOpacity={0.3}/>
                    </linearGradient>
                  </defs>
                  <PolarGrid stroke="#e2e8f0" />
                  <PolarAngleAxis dataKey="subject" tick={{ fill: 'var(--color-text-secondary)', fontSize: 12, fontWeight: 500 }} />
                  <PolarRadiusAxis angle={30} domain={[0, maxScore]} tick={false} axisLine={false} />
                  <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(241, 245, 249, 0.4)' }} />
                  <Radar
                    name="Student"
                    dataKey="value"
                    stroke="var(--color-expert-academic)"
                    strokeWidth={2}
                    fill="url(#colorRadar)"
                    fillOpacity={1}
                    isAnimationActive={true}
                    animationBegin={isOpen ? 300 : 0}
                    animationDuration={1500}
                    animationEasing="ease-out"
                  />
                </RadarChart>
              </ResponsiveContainer>
            </div>
            
            <div style={{ textAlign: 'center', marginTop: '-35px', marginBottom: '20px', fontSize: '0.75rem', color: '#94a3b8', fontStyle: 'italic', wordBreak: 'keep-all', padding: '0 10px' }}>
                {language === 'ko' ? '*참고 : 본 그래프는 전체 학습 과정에서 획득한 각 영역별 점수의 평균을 시각화한 것입니다*' : '*Note: This graph visualizes the average score for each area obtained throughout the entire learning session.*'}
            </div>

            <div style={{ textAlign: 'center', marginTop: '45px' }}>
              <p style={{ color: 'var(--color-text-secondary)', fontSize: '1rem', margin: '0 0 5px 0', fontWeight: '500' }}>
                {language === 'ko' ? '기본 점수' : 'Base Score'}
              </p>
              <p style={{ color: 'var(--color-expert-academic)', fontSize: '2.5rem', fontWeight: '800', margin: 0 }}>
                {reportData?.base_score !== undefined ? reportData.base_score.toFixed(1) : '0.0'}
                <span style={{ fontSize: '1.2rem', color: '#cbd5e1', fontWeight: '400', marginLeft: '8px' }}>/ 100</span>
              </p>
              <p style={{ marginTop: '8px', marginBottom: 0, fontSize: '0.75rem', color: '#94a3b8', fontStyle: 'italic', wordBreak: 'keep-all', padding: '0 10px' }}>
                {language === 'ko' ? '*기본 점수는 지금까지 진행한 모든 유효 턴 점수들의 누적 평균값입니다 (유효 턴은 힌트를 제외한 답변 횟수입니다)*' : '*The base score is the cumulative average of all valid turns (valid turns exclude hint usage).*'}
              </p>
              
              {reportData?.final_score !== undefined && reportData.final_score > (reportData?.base_score || 0) && (
                <div style={{ marginTop: '20px', padding: '12px 25px', backgroundColor: 'rgba(52, 211, 153, 0.1)', border: '2px solid #6ee7b7', borderRadius: '12px', display: 'inline-block' }}>
                  <p style={{ color: '#047857', fontSize: '0.95rem', margin: '0 0 4px 0', fontWeight: '700' }}>
                    {language === 'ko' ? '최종 점수 (1.5배 보너스 적용)' : 'Final Score (1.5x Bonus)'}
                  </p>
                  <p style={{ color: '#059669', fontSize: '2.2rem', fontWeight: '800', margin: 0 }}>
                    {reportData.final_score.toFixed(1)}
                  </p>
                </div>
              )}
            </div>
          </div>

          <div className="summary-details">
            {/* Scaffolding Metrics */}
            <div className="summary-section metric-cards">
              <h3>{t(language, 'scaffoldingSummary')}</h3>
              
              <div className="support-counters">
                <div className="counter-box">
                  <span className="counter-label">{t(language, 'level1Hint')}</span>
                  <span className="counter-value">{reportData?.scaffolding_summary?.nudge ?? helpCountLevel1}</span>
                </div>
                <div className="counter-box">
                  <span className="counter-label">{t(language, 'level2Hint')}</span>
                  <span className="counter-value">{reportData?.scaffolding_summary?.concept ?? helpCountLevel2}</span>
                </div>
                <div className="counter-box">
                  <span className="counter-label">{t(language, 'level3Hint')}</span>
                  <span className="counter-value">{reportData?.scaffolding_summary?.fill_blank ?? helpCountLevel3}</span>
                </div>
              </div>

              <div className="bonus-score-section">
                <h3>{t(language, 'selfDirectedBonus')}</h3>
                <div className={`bonus-card ${(reportData?.scaffolding_summary?.total ?? (helpCountLevel1 + helpCountLevel2 + helpCountLevel3)) === 0 ? 'earned' : 'missed'}`}>
                  <div className="bonus-points">+{(reportData?.scaffolding_summary?.total ?? (helpCountLevel1 + helpCountLevel2 + helpCountLevel3)) === 0 ? ((reportData?.base_score || 0) * 0.5).toFixed(1) : 0}</div>
                  <div className="bonus-caption" style={{ whiteSpace: 'pre-line' }}>
                    {t(language, (reportData?.scaffolding_summary?.total ?? (helpCountLevel1 + helpCountLevel2 + helpCountLevel3)) === 0 ? 'bonusEarned' : 'bonusMissed')
                      .replace('{points}', ((reportData?.base_score || 0) * 0.5).toFixed(1).replace(/\.0$/, ''))}
                  </div>
                </div>
              </div>
            </div>

            {/* Educational Insights */}
            <div className="summary-section">
              <h3>{t(language, 'eduInsights')}</h3>
              
              <div className="insight-badge">
                <div className="badge-icon">
                  <Award size={24} color="#f59e0b" />
                </div>
                <div className="badge-text" style={{ flex: 1 }}>
                  <h4>{t(language, 'evalResult')}</h4>
                  <p style={{ whiteSpace: 'pre-line' }}>{insightText}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SummaryModal;
