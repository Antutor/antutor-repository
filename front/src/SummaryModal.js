import React, { useEffect, useState } from 'react';
import { 
  Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer 
} from 'recharts';
import { X, Award, AlertCircle, ArrowRight } from 'lucide-react';
import './SummaryModal.css';

const SummaryModal = ({ isOpen, onClose, helpCountLevel1, helpCountLevel2, reportData }) => {
  const [shouldRender, setShouldRender] = useState(false);
  const [isActive, setIsActive] = useState(false);

  let radarData = [
    { subject: '정확성', value: 0, fullMark: 100 },
    { subject: '현실성', value: 0, fullMark: 100 },
    { subject: '통찰력', value: 0, fullMark: 100 },
  ];
  let insightText = "아직 평가 데이터가 없습니다.";

  if (reportData && reportData.growth_visualization) {
      const gv = reportData.growth_visualization;
      radarData = [
        { subject: '정확성', value: gv.Academic ? gv.Academic[gv.Academic.length - 1] : 0, fullMark: 100 },
        { subject: '현실성', value: gv.Market ? gv.Market[gv.Market.length - 1] : 0, fullMark: 100 },
        { subject: '통찰력', value: gv.Macro ? gv.Macro[gv.Macro.length - 1] : 0, fullMark: 100 },
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
          <h2>학습 요약</h2>
          <p>학습 성취도 및 스타일 분석</p>
        </div>

        <div className="summary-grid">
          {/* Radar Chart Section */}
          <div className="summary-section radar-section">
            <h3>지식 수준 지표</h3>
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
                  <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />
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
          </div>

          <div className="summary-details">
            {/* Scaffolding Metrics */}
            <div className="summary-section metric-cards">
              <h3>학습 지원 요약</h3>
              
              <div className="support-counters">
                <div className="counter-box">
                  <span className="counter-label">1단계 힌트</span>
                  <span className="counter-value">{helpCountLevel1}</span>
                </div>
                <div className="counter-box">
                  <span className="counter-label">2단계 힌트</span>
                  <span className="counter-value">{helpCountLevel2}</span>
                </div>
              </div>

              <div className="bonus-score-section">
                <h3>자기 주도 보너스</h3>
                <div className={`bonus-card ${(helpCountLevel1 + helpCountLevel2) === 0 ? 'earned' : 'missed'}`}>
                  <div className="bonus-points">+{(helpCountLevel1 + helpCountLevel2) === 0 ? 50 : 0}</div>
                  <div className="bonus-caption">도움 없이 세션을 완료하면 50점을 추가로 획득할 수 있습니다!</div>
                </div>
              </div>
            </div>

            {/* Educational Insights */}
            <div className="summary-section">
              <h3>학습 인사이트</h3>
              
              <div className="insight-badge">
                <div className="badge-icon">
                  <Award size={24} color="#f59e0b" />
                </div>
                <div className="badge-text" style={{ flex: 1 }}>
                  <h4>평가 결과</h4>
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
