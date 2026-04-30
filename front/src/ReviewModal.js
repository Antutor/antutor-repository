import React, { useEffect, useState } from 'react';
import { X, BookOpen, Check } from 'lucide-react';
import './ReviewModal.css';

const ReviewModal = ({ isOpen, onClose, node }) => {
  const [shouldRender, setShouldRender] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setShouldRender(true);
    } else {
      setTimeout(() => setShouldRender(false), 300);
    }
  }, [isOpen]);

  if (!shouldRender || !node) return null;

  return (
    <div className={`review-overlay ${isOpen ? 'active' : ''}`} onClick={onClose}>
      <div className="review-modal-card" onClick={(e) => e.stopPropagation()}>
        <div className="review-modal-header">
          <h2 style={{margin: 0, fontSize: '1.25rem', color: 'var(--color-text-primary)'}}>개념 복습: {node.title}</h2>
          <button className="close-btn" onClick={onClose}><X size={20} /></button>
        </div>
        
        <div className="review-modal-body">
          {/* Character visual injection */}
          <div className="review-character-container">
            <img src="/images/antutor%20standup.png" alt="Ant-y Book Review" className="review-character" />
          </div>

          <div className="review-text-content">
            <div style={{marginBottom: '15px'}}>
              <h4 style={{margin: '0 0 8px 0', color: 'var(--color-soft-blue)'}}>핵심 요약</h4>
              <p style={{margin: 0, color: 'var(--color-text-secondary)', lineHeight: 1.6}}>
                 {node.summary || "경제학의 기본 원칙은 수요와 공급에 대해 다루며, 인간의 동기에 따라 자원이 어떻게 동적으로 할당되는지를 설명합니다."}
              </p>
            </div>
            
            <p className="insight" style={{margin: 0, fontStyle: 'italic', fontWeight: 'bold', color: 'var(--color-text-primary)'}}>
               채팅으로 돌아가기 전에 이 메모를 주의 깊게 읽어보세요.
            </p>
          </div>
        </div>

        <div className="review-modal-footer" style={{padding: '20px', borderTop: '1px solid var(--color-border)', textAlign: 'right'}}>
          <button 
            className="send-btn" 
            style={{width: 'auto', padding: '12px 24px', borderRadius: '12px', gap: '8px', fontSize: '1rem', fontWeight: 700}} 
            onClick={onClose}
          >
             <Check size={18} /> 확인했어요!
          </button>
        </div>
      </div>
    </div>
  );
};

export default ReviewModal;
