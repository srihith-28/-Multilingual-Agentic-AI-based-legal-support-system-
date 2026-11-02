import React from 'react';
import { AlertCircle, X, PhoneCall, ShieldAlert } from 'lucide-react';

export default function EmergencyModal({ isOpen, onClose }) {
  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="emergency-modal" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close-btn" onClick={onClose}>
          <X size={20} />
        </button>

        <div className="emergency-header">
          <ShieldAlert size={28} />
          <span>Emergency Legal Assistance</span>
        </div>

        <p style={{ fontSize: '0.88rem', color: '#cbd5e1' }}>
          If you or someone you know is in immediate danger or facing domestic abuse, please contact these 24/7 verified government emergency services immediately:
        </p>

        <div className="helpline-grid">
          <div className="helpline-card">
            <div className="helpline-number">7827170170</div>
            <div className="helpline-label">NCW 24/7 Women Helpline</div>
          </div>
          <div className="helpline-card">
            <div className="helpline-number">112</div>
            <div className="helpline-label">National Emergency (Police)</div>
          </div>
          <div className="helpline-card">
            <div className="helpline-number">181</div>
            <div className="helpline-label">Women in Distress (State)</div>
          </div>
          <div className="helpline-card">
            <div className="helpline-number">15100</div>
            <div className="helpline-label">NALSA Free Legal Aid</div>
          </div>
        </div>

        <div className="relief-info">
          <strong>Immediate Legal Protections:</strong>
          <ul style={{ paddingLeft: '1.2rem', marginTop: '0.4rem' }}>
            <li><strong>Section 17 PWDVA:</strong> Inherent right to reside in the shared household without unlawful eviction.</li>
            <li><strong>Section 18 PWDVA:</strong> Injunction restraining the perpetrator from committing or threatening acts of violence.</li>
            <li><strong>Section 23 PWDVA:</strong> Magistrate's power to issue immediate <em>ex-parte</em> interim protection orders on day one.</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
