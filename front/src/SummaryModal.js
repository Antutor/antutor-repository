import React, { useEffect, useState } from 'react';
import { 
  Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer 
} from 'recharts';
import { X, Award, AlertCircle, ArrowRight } from 'lucide-react';
import './SummaryModal.css';

const radarData = [
  { subject: 'Accuracy', value: 85, fullMark: 100 },
  { subject: 'Reality', value: 70, fullMark: 100 },
  { subject: 'Insight', value: 90, fullMark: 100 },
];

const SummaryModal = ({ isOpen, onClose, helpCountLevel1, helpCountLevel2 }) => {
  const [shouldRender, setShouldRender] = useState(false);
  const [isActive, setIsActive] = useState(false);

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
          <h2>Learning Summary</h2>
          <p>Your progress and learning style analysis</p>
        </div>

        <div className="summary-grid">
          {/* Radar Chart Section */}
          <div className="summary-section radar-section">
            <h3>Knowledge Dimensions</h3>
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
              <h3>Learning Support</h3>
              
              <div className="support-counters">
                <div className="counter-box">
                  <span className="counter-label">Level 1 Help</span>
                  <span className="counter-value">{helpCountLevel1}</span>
                </div>
                <div className="counter-box">
                  <span className="counter-label">Level 2 Help</span>
                  <span className="counter-value">{helpCountLevel2}</span>
                </div>
              </div>

              <div className="bonus-score-section">
                <h3>Self-Directed Bonus</h3>
                <div className={`bonus-card ${(helpCountLevel1 + helpCountLevel2) === 0 ? 'earned' : 'missed'}`}>
                  <div className="bonus-points">+{(helpCountLevel1 + helpCountLevel2) === 0 ? 50 : 0}</div>
                  <div className="bonus-caption">Complete the session without help to earn +50 points!</div>
                </div>
              </div>
            </div>

            {/* Educational Insights */}
            <div className="summary-section">
              <h3>Educational Insights</h3>
              
              <div className="insight-badge">
                <div className="badge-icon">
                  <Award size={24} color="#f59e0b" />
                </div>
                <div className="badge-text">
                  <h4>Cautious Analyst</h4>
                  <p>High theoretical accuracy, but relies heavily on moderator guidance.</p>
                </div>
              </div>

              <div className="reverse-learning-guide">
                <div className="guide-header">
                  <AlertCircle size={18} color="var(--color-expert-market)" />
                  <h4>Reverse Learning Guide</h4>
                </div>
                <p>Your Practical (Reality) score is slightly behind. To balance your knowledge, we recommend reviewing these foundational areas:</p>
                <div className="node-suggestions">
                  <button className="suggestion-btn">
                    <span>Market Dynamics</span>
                    <ArrowRight size={14} />
                  </button>
                  <button className="suggestion-btn">
                    <span>Real-world Case Studies</span>
                    <ArrowRight size={14} />
                  </button>
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
