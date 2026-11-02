import React, { useState, useEffect } from 'react';
import {
  BookOpen,
  ExternalLink,
  CheckCircle2,
  Copy,
  Check,
  X,
  Scale,
  MessageSquare,
} from 'lucide-react';

export default function CitationDrawer({ citations = [], onAskAboutSection }) {
  const [selectedCitation, setSelectedCitation] = useState(null);
  const [copiedId, setCopiedId]                 = useState(null);
  const [copiedAll, setCopiedAll]               = useState(false);

  // Close modal on Escape key
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        setSelectedCitation(null);
      }
    };
    if (selectedCitation) {
      window.addEventListener('keydown', handleKeyDown);
    }
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [selectedCitation]);

  const handleCopyAll = () => {
    if (citations.length === 0) return;
    const allText = citations
      .map(
        (c, i) =>
          `[${i + 1}] ${c.act_name} - Section ${c.section_number}: ${c.section_title}\n${c.full_text || c.content_excerpt}`
      )
      .join('\n\n────────────────────────────────\n\n');
    navigator.clipboard.writeText(allText);
    setCopiedAll(true);
    setTimeout(() => setCopiedAll(false), 2000);
  };

  const getIndiaCodeUrl = (item) => {
    if (item.source_url && item.source_url.includes('indiacode.nic.in')) {
      return item.source_url;
    }
    return `https://www.indiacode.nic.in/handle/123456789/1362/simple-search?query=${encodeURIComponent(
      `${item.act_name} Section ${item.section_number}`
    )}`;
  };

  const getKanoonUrl = (item) => {
    return `https://indiankanoon.org/search/?formInput=${encodeURIComponent(
      `${item.act_name} Section ${item.section_number}`
    )}`;
  };

  return (
    <>
      <aside className="citations-panel" aria-label="Statutory Citations Panel">
        {/* Panel Header */}
        <div className="panel-header">
          <div className="panel-title">
            <BookOpen size={18} color="#818cf8" />
            <span>Statutory Citations</span>
          </div>
          <div className="header-badges">
            <span className="panel-badge">{citations.length} Verified</span>
            {citations.length > 0 && (
              <button
                className="citation-action-icon-btn"
                onClick={handleCopyAll}
                title="Copy all citations to clipboard"
              >
                {copiedAll ? <Check size={14} color="#34d399" /> : <Copy size={14} />}
              </button>
            )}
          </div>
        </div>

        {/* Citations List */}
        <div className="citations-list">
          {citations.length === 0 ? (
            <div className="empty-state">
              <BookOpen size={48} className="empty-icon" />
              <p style={{ fontWeight: 600, color: '#94a3b8', marginBottom: '0.25rem' }}>
                No Citations Yet
              </p>
              <p style={{ fontSize: '0.78rem' }}>
                Ask a question about divorce, maintenance, custody, or domestic violence to view grounded statutory sections.
              </p>
            </div>
          ) : (
            citations.map((item, idx) => (
              <div
                key={idx}
                className="citation-card"
                onClick={() => setSelectedCitation(item)}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    setSelectedCitation(item);
                  }
                }}
                title="Click to view full statutory details"
              >
                {/* Act Name */}
                <div className="citation-act">{item.act_name}</div>

                {/* Section Title */}
                <div className="citation-section">
                  Section {item.section_number}: {item.section_title}
                </div>

                {/* Footer preview */}
                <div className="citation-footer">
                  <span className="score-badge">
                    <CheckCircle2 size={12} style={{ display: 'inline', marginRight: '4px' }} />
                    {item.relevance_score
                      ? `${Math.round(item.relevance_score * 100)}% match`
                      : 'Verified Grounding'}
                  </span>
                  <span className="section-number-pill">Sec {item.section_number}</span>
                </div>
              </div>
            ))
          )}
        </div>
      </aside>

      {/* Centered Modal Dialog in Middle of Page */}
      {selectedCitation && (
        <div
          className="modal-overlay citation-modal-overlay"
          onClick={() => setSelectedCitation(null)}
          role="dialog"
          aria-modal="true"
        >
          <div
            className="citation-modal-content"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="citation-modal-header">
              <div>
                <span className="citation-modal-act">{selectedCitation.act_name}</span>
                <h3 className="citation-modal-title">
                  Section {selectedCitation.section_number}: {selectedCitation.section_title}
                </h3>
              </div>
              <button
                className="citation-modal-close-btn"
                onClick={() => setSelectedCitation(null)}
                aria-label="Close modal"
                title="Close (Esc)"
              >
                <X size={20} />
              </button>
            </div>

            {/* Modal Body: Complete Legal Text */}
            <div className="citation-modal-body">
              <div className="citation-modal-passage">
                {selectedCitation.full_text || selectedCitation.content_excerpt}
              </div>

              <div className="citation-modal-meta">
                <span className="score-badge">
                  <CheckCircle2 size={13} style={{ display: 'inline', marginRight: '4px' }} />
                  {selectedCitation.relevance_score
                    ? `${Math.round(selectedCitation.relevance_score * 100)}% verified statutory match`
                    : 'Grounded Statutory Provision'}
                </span>
              </div>
            </div>

            {/* Modal Footer: Official Links & Actions */}
            <div className="citation-modal-footer">
              <div className="modal-footer-links">
                <a
                  href={getIndiaCodeUrl(selectedCitation)}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="citation-pill-link official-link"
                >
                  <BookOpen size={13} />
                  <span>Open in India Code</span>
                  <ExternalLink size={11} />
                </a>

                <a
                  href={getKanoonUrl(selectedCitation)}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="citation-pill-link kanoon-link"
                >
                  <Scale size={13} />
                  <span>View on Indian Kanoon</span>
                  <ExternalLink size={11} />
                </a>
              </div>

              <div className="modal-footer-actions">
                <button
                  type="button"
                  className="citation-modal-copy-btn"
                  onClick={() => {
                    const text = `${selectedCitation.act_name}\nSection ${selectedCitation.section_number}: ${selectedCitation.section_title}\n\n${selectedCitation.full_text || selectedCitation.content_excerpt}`;
                    navigator.clipboard.writeText(text);
                    setCopiedId('modal');
                    setTimeout(() => setCopiedId(null), 2000);
                  }}
                >
                  {copiedId === 'modal' ? (
                    <>
                      <Check size={14} color="#34d399" />
                      <span>Copied!</span>
                    </>
                  ) : (
                    <>
                      <Copy size={14} />
                      <span>Copy Provision</span>
                    </>
                  )}
                </button>

                {onAskAboutSection && (
                  <button
                    type="button"
                    className="citation-modal-ask-btn"
                    onClick={() => {
                      const sec = selectedCitation;
                      setSelectedCitation(null);
                      onAskAboutSection(
                        `Please explain Section ${sec.section_number} of the ${sec.act_name} (${sec.section_title}) in simple terms and how it applies to my situation.`
                      );
                    }}
                  >
                    <MessageSquare size={14} />
                    <span>Ask AI About This Section</span>
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
