/**
 * DocumentDrafter.jsx
 *
 * One-Click Bilingual Legal Document & Petition Drafter
 * Generates court-compliant PDF templates via backend API
 */

import React, { useState } from 'react';
import { FileText, Download, Loader2, ChevronLeft, CheckCircle, AlertCircle } from 'lucide-react';

// ─── Template definitions ─────────────────────────────────────────────────────
const TEMPLATES = [
  {
    id: 'mutual_divorce_petition',
    icon: '⚖️',
    titleEn: 'Mutual Consent Divorce Petition',
    descEn: 'Joint petition under Section 13B HMA / Section 28 SMA',
    fields: [
      { name: 'petitioner1_name', label: "Petitioner 1 (Husband) Full Name", type: 'text', required: true },
      { name: 'petitioner1_age', label: "Petitioner 1 Age", type: 'number', required: true },
      { name: 'petitioner1_address', label: "Petitioner 1 Address", type: 'textarea', required: true },
      { name: 'petitioner2_name', label: "Petitioner 2 (Wife) Full Name", type: 'text', required: true },
      { name: 'petitioner2_age', label: "Petitioner 2 Age", type: 'number', required: true },
      { name: 'petitioner2_address', label: "Petitioner 2 Address", type: 'textarea', required: true },
      { name: 'marriage_date', label: "Date of Marriage", type: 'date', required: true },
      { name: 'marriage_place', label: "Place of Marriage", type: 'text', required: true },
      { name: 'court_district', label: "Court District", type: 'text', required: true },
      { name: 'separation_date', label: "Date of Separation", type: 'date', required: true },
    ],
  },
  {
    id: 'protection_order_application',
    icon: '🛡️',
    titleEn: 'Protection Order Application',
    descEn: 'Application under Section 12 PWDVA 2005',
    fields: [
      { name: 'applicant_name', label: "Applicant (Aggrieved Person) Full Name", type: 'text', required: true },
      { name: 'applicant_age', label: "Applicant Age", type: 'number', required: true },
      { name: 'applicant_address', label: "Applicant's Current Address", type: 'textarea', required: true },
      { name: 'respondent_name', label: "Respondent Full Name", type: 'text', required: true },
      { name: 'respondent_relation', label: "Respondent's Relation to Applicant", type: 'text', required: true, placeholder: 'e.g., Husband, In-laws' },
      { name: 'respondent_address', label: "Respondent's Address", type: 'textarea', required: true },
      { name: 'incident_date', label: "Date of Latest Incident", type: 'date', required: true },
      { name: 'incident_description', label: "Brief Description of Domestic Violence Acts", type: 'textarea', required: true },
      { name: 'court_district', label: "Court District / Jurisdiction", type: 'text', required: true },
    ],
  },
  {
    id: 'maintenance_application',
    icon: '💰',
    titleEn: 'Maintenance Application',
    descEn: 'Application under Section 125 CrPC / Section 144 BNSS',
    fields: [
      { name: 'applicant_name', label: "Applicant Full Name", type: 'text', required: true },
      { name: 'applicant_age', label: "Applicant Age", type: 'number', required: true },
      { name: 'applicant_address', label: "Applicant's Address", type: 'textarea', required: true },
      { name: 'respondent_name', label: "Respondent Full Name", type: 'text', required: true },
      { name: 'respondent_address', label: "Respondent's Address", type: 'textarea', required: true },
      { name: 'marriage_date', label: "Date of Marriage", type: 'date', required: true },
      { name: 'respondent_income', label: "Respondent's Estimated Monthly Income (₹)", type: 'number', required: true },
      { name: 'applicant_income', label: "Applicant's Monthly Income (₹, if any)", type: 'number', required: false },
      { name: 'num_children', label: "Number of Minor Children", type: 'number', required: false },
      { name: 'monthly_expenses', label: "Applicant's Monthly Expenses (₹)", type: 'number', required: true },
      { name: 'court_district', label: "Court District", type: 'text', required: true },
    ],
  },
  {
    id: 'rcr_notice',
    icon: '📬',
    titleEn: 'Legal Notice for Restitution of Conjugal Rights',
    descEn: 'Legal notice for RCR under Section 9 HMA / Section 22 SMA',
    fields: [
      { name: 'sender_name', label: "Sender (Your) Full Name", type: 'text', required: true },
      { name: 'sender_address', label: "Sender's Address", type: 'textarea', required: true },
      { name: 'recipient_name', label: "Recipient (Spouse) Full Name", type: 'text', required: true },
      { name: 'recipient_address', label: "Recipient's Address", type: 'textarea', required: true },
      { name: 'marriage_date', label: "Date of Marriage", type: 'date', required: true },
      { name: 'separation_date', label: "Date of Withdrawal from Society", type: 'date', required: true },
      { name: 'reason_given', label: "Reason Spouse Gave for Leaving (if any)", type: 'textarea', required: false },
      { name: 'court_district', label: "Court District", type: 'text', required: true },
    ],
  },
];

const LANGUAGE_OPTIONS = [
  { code: 'en', label: 'English Only' },
  { code: 'hi', label: 'English + हिंदी (Hindi)' },
  { code: 'kn', label: 'English + ಕನ್ನಡ (Kannada)' },
  { code: 'te', label: 'English + తెలుగు (Telugu)' },
  { code: 'ta', label: 'English + தமிழ் (Tamil)' },
  { code: 'bn', label: 'English + বাংলা (Bengali)' },
  { code: 'mr', label: 'English + मराठी (Marathi)' },
  { code: 'gu', label: 'English + ગુજરાતી (Gujarati)' },
  { code: 'ml', label: 'English + മലയാളം (Malayalam)' },
];

const API_HOST = (import.meta.env.VITE_API_URL || '').trim().replace(/\/+$/, '');

// ─── Main Component ──────────────────────────────────────────────────────────
export default function DocumentDrafter({ language = 'en' }) {
  const [step, setStep] = useState(1); // 1=select template, 2=fill form, 3=done
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [formData, setFormData] = useState({});
  const [docLanguage, setDocLanguage] = useState(language !== 'en' ? language : 'en');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [downloadSuccess, setDownloadSuccess] = useState(false);

  function handleSelectTemplate(tpl) {
    setSelectedTemplate(tpl);
    setFormData({});
    setError(null);
    setDownloadSuccess(false);
    setStep(2);
  }

  function handleFieldChange(name, value) {
    setFormData((f) => ({ ...f, [name]: value }));
  }

  function handleBack() {
    setStep(1);
    setSelectedTemplate(null);
    setError(null);
    setDownloadSuccess(false);
  }

  async function handleGenerate(e) {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    setDownloadSuccess(false);

    try {
      const res = await fetch(`${API_HOST}/api/documents/draft`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          template_type: selectedTemplate.id,
          party_details: formData,
          language: docLanguage,
        }),
        signal: AbortSignal.timeout(60000), // 60s timeout
      });

      if (!res.ok) {
        const errText = await res.text().catch(() => res.statusText);
        throw new Error(`Server error ${res.status}: ${errText}`);
      }

      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${selectedTemplate.id}_${docLanguage}_${Date.now()}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      setDownloadSuccess(true);
    } catch (err) {
      setError(err.message || 'Failed to generate document. Please try again.');
    } finally {
      setIsLoading(false);
    }
  }

  // ── Step 1: Template selection ──────────────────────────────────────────────
  if (step === 1) {
    return (
      <div className="drafter-container">
        <div className="drafter-header">
          <FileText size={28} className="drafter-icon" />
          <div>
            <h2 className="drafter-title">Legal Document Drafter</h2>
            <p className="drafter-subtitle">Generate court-compliant bilingual legal petitions as PDF</p>
          </div>
        </div>

        <div className="template-grid">
          {TEMPLATES.map((tpl) => (
            <button
              key={tpl.id}
              className="template-card"
              onClick={() => handleSelectTemplate(tpl)}
            >
              <span className="template-icon">{tpl.icon}</span>
              <div>
                <div className="template-title">{tpl.titleEn}</div>
                <div className="template-desc">{tpl.descEn}</div>
              </div>
            </button>
          ))}
        </div>

        <div className="drafter-notice">
          <AlertCircle size={14} />
          Documents are generated as bilingual PDFs (English + selected Indian language). For use as drafts only — have a qualified advocate review before filing in court.
        </div>
      </div>
    );
  }

  // ── Step 2: Form ────────────────────────────────────────────────────────────
  return (
    <div className="drafter-container">
      <div className="drafter-header">
        <button className="drafter-back-btn" onClick={handleBack}>
          <ChevronLeft size={16} /> Back
        </button>
        <div>
          <h2 className="drafter-title">
            {selectedTemplate.icon} {selectedTemplate.titleEn}
          </h2>
          <p className="drafter-subtitle">{selectedTemplate.descEn}</p>
        </div>
      </div>

      <form className="drafter-form" onSubmit={handleGenerate}>
        {/* Language selector */}
        <div className="calc-field calc-field-full drafter-lang-select">
          <label>Document Language (Bilingual)</label>
          <select value={docLanguage} onChange={(e) => setDocLanguage(e.target.value)}>
            {LANGUAGE_OPTIONS.map((opt) => (
              <option key={opt.code} value={opt.code}>{opt.label}</option>
            ))}
          </select>
        </div>

        {/* Dynamic fields */}
        {selectedTemplate.fields.map((field) => (
          <div key={field.name} className="calc-field calc-field-full">
            <label>
              {field.label}
              {field.required && <span className="required-star"> *</span>}
            </label>
            {field.type === 'textarea' ? (
              <textarea
                name={field.name}
                value={formData[field.name] || ''}
                onChange={(e) => handleFieldChange(field.name, e.target.value)}
                placeholder={field.placeholder || ''}
                required={field.required}
                rows={3}
              />
            ) : (
              <input
                type={field.type}
                name={field.name}
                value={formData[field.name] || ''}
                onChange={(e) => handleFieldChange(field.name, e.target.value)}
                placeholder={field.placeholder || ''}
                required={field.required}
                min={field.type === 'number' ? '0' : undefined}
              />
            )}
          </div>
        ))}

        {/* Error */}
        {error && (
          <div className="drafter-error">
            <AlertCircle size={16} />
            {error}
          </div>
        )}

        {/* Success */}
        {downloadSuccess && (
          <div className="drafter-success">
            <CheckCircle size={16} />
            PDF downloaded successfully! Check your Downloads folder.
          </div>
        )}

        <button type="submit" className="calc-btn" disabled={isLoading}>
          {isLoading ? (
            <>
              <Loader2 size={16} className="spin-icon" />
              Generating Bilingual PDF…
            </>
          ) : (
            <>
              <Download size={16} />
              Generate &amp; Download Bilingual PDF
            </>
          )}
        </button>
      </form>

      <div className="drafter-notice" style={{ marginTop: '1rem' }}>
        <AlertCircle size={14} />
        This draft is for educational purposes. Always consult a qualified advocate before filing.
      </div>
    </div>
  );
}
