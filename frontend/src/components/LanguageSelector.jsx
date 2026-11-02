import React, { useState, useRef, useEffect } from 'react';
import { Globe, ChevronDown, Check } from 'lucide-react';

const INDIAN_LANGUAGES = [
  { code: 'en', name: 'English', nativeName: 'English', region: 'Pan-India' },
  { code: 'hi', name: 'Hindi', nativeName: 'हिन्दी', region: 'North / Central India' },
  { code: 'kn', name: 'Kannada', nativeName: 'ಕನ್ನಡ', region: 'Karnataka' },
  { code: 'te', name: 'Telugu', nativeName: 'తెలుగు', region: 'Andhra Pradesh & Telangana' },
  { code: 'ta', name: 'Tamil', nativeName: 'தமிழ்', region: 'Tamil Nadu & Puducherry' },
  { code: 'bn', name: 'Bengali', nativeName: 'বাংলা', region: 'West Bengal & Tripura' },
  { code: 'mr', name: 'Marathi', nativeName: 'मराठी', region: 'Maharashtra' },
  { code: 'gu', name: 'Gujarati', nativeName: 'ગુજરાતી', region: 'Gujarat' },
  { code: 'ml', name: 'Malayalam', nativeName: 'മലയാളം', region: 'Kerala & Lakshadweep' },
  { code: 'ur', name: 'Urdu', nativeName: 'اردو', region: 'Pan-India' },
];

export default function LanguageSelector({ language, setLanguage }) {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);

  const currentLang = INDIAN_LANGUAGES.find((l) => l.code === language) || INDIAN_LANGUAGES[0];

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };
    const handleEscape = (event) => {
      if (event.key === 'Escape') setIsOpen(false);
    };

    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleEscape);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleEscape);
    };
  }, []);

  return (
    <div className="language-selector-wrapper" ref={dropdownRef}>
      <button
        id="lang-selector-trigger"
        type="button"
        className={`lang-dropdown-trigger ${isOpen ? 'active' : ''}`}
        onClick={() => setIsOpen((prev) => !prev)}
        aria-haspopup="listbox"
        aria-expanded={isOpen}
        title="Select from 10 Indian Languages"
      >
        <Globe size={15} className="lang-globe-icon" />
        <span className="lang-trigger-label">
          <strong className="native-text">{currentLang.nativeName}</strong>
          {currentLang.name !== currentLang.nativeName && (
            <span className="lang-en-sub">({currentLang.name})</span>
          )}
        </span>
        <ChevronDown size={14} className={`chevron-icon ${isOpen ? 'rotated' : ''}`} />
      </button>

      {isOpen && (
        <div className="lang-dropdown-menu" role="listbox" aria-label="Select Indian Language">
          <div className="lang-dropdown-header">
            <span>Supported Indian Languages (10)</span>
          </div>

          <div className="lang-dropdown-grid">
            {INDIAN_LANGUAGES.map((lang) => {
              const isSelected = lang.code === language;
              return (
                <button
                  key={lang.code}
                  id={`lang-opt-${lang.code}`}
                  type="button"
                  role="option"
                  aria-selected={isSelected}
                  className={`lang-option-card ${isSelected ? 'selected' : ''}`}
                  onClick={() => {
                    setLanguage(lang.code);
                    setIsOpen(false);
                  }}
                >
                  <div className="lang-card-main">
                    <span className="lang-native-bold">{lang.nativeName}</span>
                    <span className="lang-english-title">{lang.name}</span>
                  </div>
                  <div className="lang-card-footer">
                    <span className="lang-region">{lang.region}</span>
                    {isSelected && <Check size={14} className="check-icon" />}
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
