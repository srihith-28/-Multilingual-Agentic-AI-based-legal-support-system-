/**
 * EvidenceScanner.jsx
 *
 * Case Strength & Evidence Admissibility Scanner (Litigation Readiness Score)
 * Evaluates admissibility under Section 65B IEA / Section 63 BSA 2023,
 * Rajnesh v. Neha asset disclosures, and Indian criminal/family evidence standards.
 */

import React, { useState, useMemo } from 'react';
import {
  ShieldCheck,
  AlertCircle,
  FileText,
  Smartphone,
  CreditCard,
  HeartPulse,
  Award,
  CheckSquare,
  Square,
  HelpCircle,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  FileCheck2,
  Download
} from 'lucide-react';

const CASE_TYPES = [
  { id: 'dv', label: 'Domestic Violence Relief (PWDVA 2005)', icon: '🛡️' },
  { id: 'maintenance', label: 'Maintenance & Child Support (Sec 125 / 144 BNSS)', icon: '💰' },
  { id: 'divorce_cruelty', label: 'Contested Divorce on Cruelty / Desertion (Sec 13 HMA)', icon: '⚖️' },
  { id: 'child_custody', label: 'Child Custody & Guardianship (GWA 1890)', icon: '👶' }
];

const EVIDENCE_ITEMS = [
  // Electronic Evidence (Sec 65B IEA / Sec 63 BSA)
  {
    id: 'whatsapp_chats',
    category: 'electronic',
    label: 'WhatsApp / Telegram / SMS Chat Exports',
    desc: 'Screenshots or PDF exports of text conversations showing threats, demands, or admissions.',
    weight: 15,
    applicableTo: ['dv', 'maintenance', 'divorce_cruelty', 'child_custody'],
    statuteWarning: 'Mandatory Section 63 BSA 2023 / 65B Indian Evidence Act Certificate required. Raw screenshots alone are inadmissible as secondary evidence without phone certificate.'
  },
  {
    id: 'audio_recordings',
    category: 'electronic',
    label: 'Recorded Phone Calls or Audio Clips',
    desc: 'Voice recordings of verbal abuse, dowry demands, or conversations with spouse/in-laws.',
    weight: 12,
    applicableTo: ['dv', 'divorce_cruelty', 'maintenance'],
    statuteWarning: 'Device on which call was recorded must be preserved. Section 65B/63 BSA certificate signed by person in lawful control of the recording device is mandatory.'
  },
  {
    id: 'cctv_video',
    category: 'electronic',
    label: 'CCTV / Video Footage of Incidents',
    desc: 'Visual footage of physical assault, harassment, abandonment, or forced eviction.',
    weight: 15,
    applicableTo: ['dv', 'divorce_cruelty'],
    statuteWarning: 'Requires preservation of the original DVR/SD card or certified digital clone with MD5 hash validation.'
  },
  {
    id: 'emails',
    category: 'electronic',
    label: 'Official Emails with RFC Headers',
    desc: 'Emails discussing matrimonial issues, financial arrangements, or marital dispute correspondence.',
    weight: 10,
    applicableTo: ['dv', 'maintenance', 'divorce_cruelty'],
    statuteWarning: 'Must include full email message headers (DKIM/SPF) to prove non-tampering.'
  },

  // Financial Documentation (Rajnesh v. Neha)
  {
    id: 'bank_statements',
    category: 'financial',
    label: '3 Years Certified Bank Account Statements',
    desc: 'Official bank passbooks or bank-stamped account statements of both spouses.',
    weight: 15,
    applicableTo: ['maintenance', 'dv', 'divorce_cruelty', 'child_custody'],
    statuteWarning: 'Mandated under Enclosure I of Supreme Court decision in Rajnesh v. Neha (2020) 14 SCC 1.'
  },
  {
    id: 'itr_form16',
    category: 'financial',
    label: 'Income Tax Returns (ITR-V) & Form 16 / 26AS for Last 3 Years',
    desc: 'Certified tax filings showing gross annual income, tax deductions, and employer TDS credits.',
    weight: 15,
    applicableTo: ['maintenance', 'dv', 'child_custody'],
    statuteWarning: 'Crucial for family court to deduce actual earning capacity and standard of living.'
  },
  {
    id: 'lifestyle_proof',
    category: 'financial',
    label: 'Lifestyle Proof (Vehicles, Credit Card Statements, Foreign Travel)',
    desc: 'Vehicle registration (RC), club memberships, international flight tickets, or high-end expenses.',
    weight: 10,
    applicableTo: ['maintenance', 'dv'],
    statuteWarning: 'Used to establish concealment of true earnings when spouse falsely claims zero income.'
  },

  // Medical & Incident Records
  {
    id: 'mlc_medical',
    category: 'medical',
    label: 'Government Hospital Medico-Legal Case (MLC) / Doctor Prescription',
    desc: 'Emergency medical examination records, injury certificates, or psychological treatment notes.',
    weight: 20,
    applicableTo: ['dv', 'divorce_cruelty'],
    statuteWarning: 'A government hospital MLC is the highest standard of physical cruelty corroboration under Section 320 IPC / 116 BNS.'
  },
  {
    id: 'police_complaints',
    category: 'formal',
    label: 'Police Station GD/DD Entry or NCR / FIR Registration',
    desc: 'Copies of earlier formal complaints made to police or Women & Child Helpline (181/1091).',
    weight: 15,
    applicableTo: ['dv', 'divorce_cruelty'],
    statuteWarning: 'Contemporaneous police complaints prevent the opposing side from arguing allegations are an afterthought.'
  },

  // Formal Documents
  {
    id: 'marriage_cert',
    category: 'formal',
    label: 'Marriage Certificate / Wedding Invitation & Photos',
    desc: 'Official registration certificate under HMA / SMA or original photographs with negatives/metadata.',
    weight: 10,
    applicableTo: ['dv', 'maintenance', 'divorce_cruelty', 'child_custody'],
    statuteWarning: 'Prima facie proof of solemnized marriage required before any matrimonial relief is maintainable.'
  },
  {
    id: 'residence_proof',
    category: 'formal',
    label: 'Proof of Residing in Shared Matrimonial Household',
    desc: 'Rent agreement naming both, utility bills, Aadhaar card with marital address, or postal delivery slips.',
    weight: 12,
    applicableTo: ['dv', 'divorce_cruelty'],
    statuteWarning: 'Statutory prerequisite for Residence Orders under Section 19 PWDVA (Satish Chander Ahuja v. Sneha Ahuja).'
  },
  {
    id: 'child_records',
    category: 'formal',
    label: 'Child School Records, Medical History, & Parent Involvement Proof',
    desc: 'Report cards, fee payment receipts, doctor visits, photos of celebrations, and parenting milestones.',
    weight: 18,
    applicableTo: ['child_custody', 'maintenance'],
    statuteWarning: 'Directly influences judge’s determination of the child’s best emotional and educational welfare.'
  }
];

export default function EvidenceScanner({ language = 'en' }) {
  const [caseType, setCaseType] = useState('dv');
  const [selectedItems, setSelectedItems] = useState(
    new Set(['whatsapp_chats', 'bank_statements', 'marriage_cert'])
  );
  const [has65BCertificate, setHas65BCertificate] = useState(false);

  // Filter applicable items
  const applicableItems = useMemo(() => {
    return EVIDENCE_ITEMS.filter((item) => item.applicableTo.includes(caseType));
  }, [caseType]);

  // Toggle selection
  function handleToggle(id) {
    setSelectedItems((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  // Calculate score
  const { score, totalPossible, grade, color, recommendations } = useMemo(() => {
    let earned = 0;
    let max = 0;
    const recs = [];

    applicableItems.forEach((item) => {
      max += item.weight;
      if (selectedItems.has(item.id)) {
        // Penalty if electronic evidence is selected without 65B/63 BSA certificate
        if (item.category === 'electronic' && !has65BCertificate) {
          earned += Math.round(item.weight * 0.45); // 55% penalty for lack of certification
          if (!recs.includes('Prepare and execute Section 63 BSA / 65B IEA Electronic Evidence Affidavit for your digital proof.')) {
            recs.push('Prepare and execute Section 63 BSA / 65B IEA Electronic Evidence Affidavit for your digital proof.');
          }
        } else {
          earned += item.weight;
        }
      } else {
        if (item.category === 'financial' && caseType === 'maintenance') {
          recs.push(`Obtain ${item.label} to prevent respondent from under-declaring income.`);
        }
        if (item.category === 'medical' && caseType === 'dv') {
          recs.push('Consult a registered medical practitioner / hospital immediately to document any physical injuries or emotional trauma.');
        }
      }
    });

    const finalScore = max > 0 ? Math.min(100, Math.round((earned / max) * 100)) : 0;

    let g = 'High Risk';
    let c = '#ef4444';
    if (finalScore >= 80) {
      g = 'Very Strong — High Admissibility';
      c = '#10b981';
    } else if (finalScore >= 60) {
      g = 'Moderate — Needs Key Corroboration';
      c = '#f59e0b';
    } else if (finalScore >= 40) {
      g = 'Sub-optimal — Evidentiary Gaps';
      c = '#f97316';
    }

    return {
      score: finalScore,
      totalPossible: max,
      grade: g,
      color: c,
      recommendations: recs
    };
  }, [applicableItems, selectedItems, has65BCertificate, caseType]);

  return (
    <div className="scanner-container">
      {/* Header */}
      <div className="scanner-header">
        <div className="scanner-header-icon">
          <ShieldCheck size={28} style={{ color: '#38bdf8' }} />
        </div>
        <div>
          <h2 className="scanner-title">Evidence & Case Strength Scanner</h2>
          <p className="scanner-subtitle">
            Evaluate your case evidence against Indian statutory admissibility standards (Section 65B IEA, Section 63 BSA 2023, & Supreme Court asset disclosure mandates).
          </p>
        </div>
      </div>

      {/* Case Type Selector */}
      <div className="scanner-case-selector">
        <label className="scanner-selector-label">Select Your Legal Proceeding Type:</label>
        <div className="case-type-chips">
          {CASE_TYPES.map((ct) => (
            <button
              key={ct.id}
              className={`case-chip ${caseType === ct.id ? 'case-chip--active' : ''}`}
              onClick={() => setCaseType(ct.id)}
            >
              <span>{ct.icon}</span>
              <span>{ct.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Main Grid: Checklist Left, Score Gauge Right */}
      <div className="scanner-content-grid">
        {/* Left: Checklist */}
        <div className="scanner-checklist-card">
          <div className="checklist-card-header">
            <FileCheck2 size={18} style={{ color: '#38bdf8' }} />
            <span>Select the Evidence in Your Possession:</span>
          </div>

          {/* 65B / 63 BSA Switch Toggle */}
          <div className="cert-65b-box">
            <div className="cert-65b-content">
              <Smartphone size={20} style={{ color: has65BCertificate ? '#10b981' : '#f59e0b', flexShrink: 0 }} />
              <div>
                <div className="cert-65b-title">
                  Section 63 BSA / 65B Evidence Act Certificate Ready?
                </div>
                <div className="cert-65b-desc">
                  Is a signed affidavit confirming device serial number, possession, and non-tampering prepared for chats/recordings?
                </div>
              </div>
            </div>
            <button
              type="button"
              className={`toggle-switch-btn ${has65BCertificate ? 'toggle-switch-btn--on' : ''}`}
              onClick={() => setHas65BCertificate((v) => !v)}
            >
              {has65BCertificate ? 'YES (Certified)' : 'NO (Uncertified)'}
            </button>
          </div>

          <div className="evidence-items-list">
            {applicableItems.map((item) => {
              const isChecked = selectedItems.has(item.id);
              return (
                <div
                  key={item.id}
                  className={`evidence-item-card ${isChecked ? 'evidence-item-card--checked' : ''}`}
                  onClick={() => handleToggle(item.id)}
                >
                  <div className="evidence-checkbox">
                    {isChecked ? (
                      <CheckSquare size={20} style={{ color: '#38bdf8' }} />
                    ) : (
                      <Square size={20} style={{ color: '#5a84a8' }} />
                    )}
                  </div>
                  <div className="evidence-info">
                    <div className="evidence-item-header">
                      <span className="evidence-label">{item.label}</span>
                      <span className="evidence-weight-badge">+{item.weight} pts</span>
                    </div>
                    <p className="evidence-desc">{item.desc}</p>
                    {isChecked && (
                      <div className="evidence-statute-note">
                        <AlertTriangle size={13} style={{ color: '#f59e0b', flexShrink: 0 }} />
                        <span>{item.statuteWarning}</span>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right: Score Gauge & Analysis */}
        <div className="scanner-analysis-column">
          <div className="score-gauge-card" style={{ borderColor: `${color}40` }}>
            <div className="gauge-header">
              <Award size={20} style={{ color }} />
              <span>Litigation Readiness Score</span>
            </div>

            {/* Circular Gauge / Numerical Display */}
            <div className="score-circle-display">
              <div className="score-radial-wrap" style={{ borderColor: color }}>
                <span className="score-number" style={{ color }}>{score}%</span>
                <span className="score-subtext">Case Strength</span>
              </div>
            </div>

            <div className="score-grade-pill" style={{ background: `${color}18`, borderColor: `${color}35`, color }}>
              {grade}
            </div>

            <p className="score-explanation">
              {score >= 80
                ? 'Your documentary evidence is substantially robust. Proper affidavit presentation in court will strongly support interim reliefs.'
                : score >= 60
                ? 'Reasonable prima facie case, but critical gaps exist in financial disclosure or digital certification that opposition can challenge.'
                : 'High evidentiary risk. Uncertified digital files or absent financial records risk dismissal during preliminary arguments.'}
            </p>

            {/* Strategic Recommendations */}
            <div className="recs-section">
              <h4 className="recs-title">Critical Next Steps to Fortify Evidence:</h4>
              <ul className="recs-list">
                {recommendations.length > 0 ? (
                  recommendations.map((rec, i) => (
                    <li key={i}>
                      <ChevronRight size={14} style={{ color, flexShrink: 0 }} />
                      <span>{rec}</span>
                    </li>
                  ))
                ) : (
                  <li className="recs-all-good">
                    <CheckCircle2 size={16} style={{ color: '#10b981', flexShrink: 0 }} />
                    <span>All key primary evidence categories are accounted for. Ensure certified court copies are preserved.</span>
                  </li>
                )}
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
