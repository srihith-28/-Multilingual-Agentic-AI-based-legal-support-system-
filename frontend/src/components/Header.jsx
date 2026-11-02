import React from 'react';
import { Scale, AlertTriangle } from 'lucide-react';
import LanguageSelector from './LanguageSelector';

export default function Header({ language, setLanguage, onOpenEmergency }) {
  return (
    <header className="app-header">
      <div className="brand-wrapper">
        <div className="brand-icon">
          <Scale size={24} />
        </div>
        <div>
          <div className="brand-title">Agent Forge Legal AI</div>
          <div className="brand-subtitle">Multilingual Family Law Decision Support</div>
        </div>
      </div>

      <div className="header-actions">
        {/* Emergency SOS Button */}
        <button
          id="emergency-sos-btn"
          className="emergency-sos-btn"
          onClick={onOpenEmergency}
          title="Instant Emergency & Domestic Violence Helplines"
        >
          <AlertTriangle size={16} />
          <span>Emergency SOS</span>
        </button>

        {/* 10 Indian Languages Selector */}
        <LanguageSelector language={language} setLanguage={setLanguage} />
      </div>
    </header>
  );
}
