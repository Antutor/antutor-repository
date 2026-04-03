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
          <h2 style={{margin: 0, fontSize: '1.25rem', color: 'var(--color-text-primary)'}}>Concept Review: {node.title}</h2>
          <button className="close-btn" onClick={onClose}><X size={20} /></button>
        </div>
        
        <div className="review-modal-body">
          {/* Character visual injection */}
          <div className="review-character-container">
            <img src="/images/ant.jpg" alt="Ant-y Book Review" className="review-character" />
          </div>

          <div className="review-text-content">
            <div style={{marginBottom: '15px'}}>
              <h4 style={{margin: '0 0 8px 0', color: 'var(--color-soft-blue)'}}>Quick Refresher</h4>
              <p style={{margin: 0, color: 'var(--color-text-secondary)', lineHeight: 1.6}}>
                 {node.summary || "The fundamental principles of economics cover supply and demand, explaining how resources are allocated dynamically based on human incentives."}
              </p>
            </div>
            
            <p className="insight" style={{margin: 0, fontStyle: 'italic', fontWeight: 'bold', color: 'var(--color-text-primary)'}}>
               Take a moment to carefully read over these notes before jumping back into the conversation.
            </p>
          </div>
        </div>

        <div className="review-modal-footer" style={{padding: '20px', borderTop: '1px solid var(--color-border)', textAlign: 'right'}}>
          <button 
            className="send-btn" 
            style={{width: 'auto', padding: '12px 24px', borderRadius: '12px', gap: '8px', fontSize: '1rem', fontWeight: 700}} 
            onClick={onClose}
          >
             <Check size={18} /> Got it!
          </button>
        </div>
      </div>
    </div>
  );
};

export default ReviewModal;
