/**
 * CourtRoadmap.jsx
 *
 * Interactive Court Procedure & Timeline Roadmap ("Court Journey Visualizer")
 * Guides citizens through stage-by-stage Family Court & PWDVA procedures with timelines,
 * statutory rules, mandatory documents, and landmark Supreme Court guidelines.
 */

import React, { useState } from 'react';
import {
  Compass,
  Clock,
  FileCheck,
  AlertTriangle,
  ChevronRight,
  ShieldAlert,
  Scale,
  Users,
  HeartHandshake,
  CheckCircle2,
  Calendar,
  Sparkles
} from 'lucide-react';

const TRACKS = [
  {
    id: 'mutual_divorce',
    title: 'Mutual Consent Divorce',
    statute: 'Section 13B Hindu Marriage Act, 1955 / Section 28 Special Marriage Act, 1954',
    icon: HeartHandshake,
    totalDuration: '6 to 18 Months (Can be waived to 1–2 weeks under SC Guidelines)',
    estimatedCost: '₹15,000 – ₹45,000 (Court fee ₹15 – ₹100 + advocate drafting)',
    color: '#0ea5e9',
    steps: [
      {
        stepNum: 1,
        title: 'Drafting & Joint Petition Filing',
        duration: 'Days 1 – 7',
        description: 'Both spouses jointly prepare and execute the petition supported by affidavits confirming mutual agreement.',
        documents: [
          'Marriage Registration Certificate / Original Wedding Card & Photographs',
          'Passport-size photographs of both parties',
          'Address and ID proofs (Aadhaar / Voter ID / Passport)',
          'Proof of living separately for minimum 1 year (mandatory statutory prerequisite)',
          'Settlement Agreement covering permanent alimony and child custody'
        ],
        legalBasis: 'Section 13B(1) HMA — Requires proof that parties have lived separately for 1 year or more and cannot live together.',
        proTip: 'Ensure permanent alimony and child visitation terms are drafted with zero ambiguity to avoid future contempt proceedings.'
      },
      {
        stepNum: 2,
        title: 'First Motion Hearing & Statement Recording',
        duration: 'Day 10 – 30',
        description: 'Both parties appear before the Family Court Judge. Oaths and preliminary statements are formally recorded.',
        documents: [
          'Original Petitions and Affidavits of both spouses',
          'Physical appearance of both spouses or authorized POA (if living overseas)'
        ],
        legalBasis: 'First Motion recorded under oath. Court examines whether consent was free or procured by fraud/undue influence.',
        proTip: 'If one party is abroad, High Courts permit virtual appearance via video conferencing upon formal application.'
      },
      {
        stepNum: 3,
        title: 'Court-Directed Mediation & Counselling',
        duration: 'Weeks 4 – 8',
        description: 'Parties are directed to the in-house Family Court Mediation Centre to explore any last chance of reconciliation or confirm non-reconciliation.',
        documents: [
          'Order sheet directing parties to Mediation',
          'Mediation Settlement Agreement (Memorandum of Understanding)'
        ],
        legalBasis: 'Section 9 Family Courts Act, 1984 makes endeavour for reconciliation mandatory.',
        proTip: 'Mediation sessions are strictly confidential; anything spoken inside cannot be used against either party in future litigation.'
      },
      {
        stepNum: 4,
        title: '6-Month Cooling-Off Period & Waiver Application',
        duration: 'Months 2 – 6 (or Waived)',
        description: 'Statutory 6-month cooling period to reflect. Can be waived by filing an application under Amardeep Singh v. Harveen Kaur (2017).',
        documents: [
          'Application for waiver of statutory 6-month cooling-off period',
          'Affidavit showing prolonged separation, no coercion, and settlement finalized'
        ],
        legalBasis: 'Amardeep Singh v. Harveen Kaur (2017) 8 SCC 746 & Shilpa Sailesh v. Varun Sreenivasan (2023) SCC Online SC 544 (Art. 142 waiver).',
        proTip: 'If parties have lived separately for over 18 months and all alimony is already exchanged, courts routinely waive this 6-month wait.'
      },
      {
        stepNum: 5,
        title: 'Second Motion Hearing & Final Statements',
        duration: 'Month 6 (or immediately upon waiver)',
        description: 'Both parties re-affirm that they still wish to dissolve the marriage and all financial/custodial promises have been fulfilled.',
        documents: [
          'Demand Draft / RTGS receipt for permanent alimony balance (if agreed)',
          'Second Motion joint petition and affidavits'
        ],
        legalBasis: 'Section 13B(2) HMA — Motion must be made not earlier than 6 months and not later than 18 months from First Motion.',
        proTip: 'Either spouse retains the legal right to unilaterally withdraw consent prior to the passing of the final decree.'
      },
      {
        stepNum: 6,
        title: 'Final Decree of Divorce Pronounced',
        duration: '1 – 2 Weeks after Second Motion',
        description: 'The Judge signs the final judgment and decree officially dissolving the marriage. Certified copies are delivered to both parties.',
        documents: [
          'Application for Certified Copy (Form No. 16)',
          'Court receipt and stamp charges'
        ],
        legalBasis: 'Decree operates as a conclusive judgment in rem under Section 41 Indian Evidence Act / BSA.',
        proTip: 'Apply for at least 3 certified copies immediately; they are required for passport renewal, visa, or remarriage.'
      }
    ]
  },
  {
    id: 'domestic_violence',
    title: 'Domestic Violence Emergency Protection',
    statute: 'Protection of Women from Domestic Violence Act, 2005 (PWDVA)',
    icon: ShieldAlert,
    totalDuration: 'Immediate (Ex-parte) to 6 Months for Final Orders',
    estimatedCost: 'Free via Protection Officer / DLSA or ₹10,000 – ₹30,000 private counsel',
    color: '#ef4444',
    steps: [
      {
        stepNum: 1,
        title: 'Filing DIR (Domestic Incident Report)',
        duration: 'Day 1 – 3',
        description: 'Aggrieved woman approaches the local Protection Officer (PO), Service Provider, or Magistrate directly to record Form 1 (DIR).',
        documents: [
          'Form 1 DIR prescribed under PWDVA Rules',
          'Medical examination reports (MLC) if physical violence occurred',
          'Copies of police diary (GD/DD entries) or 112 emergency calls'
        ],
        legalBasis: 'Section 12 PWDVA read with Rule 8 — Magistrate must take into consideration any DIR submitted by Protection Officer.',
        proTip: 'Going through a Protection Officer creates a government-backed evidentiary record that judges prioritize.'
      },
      {
        stepNum: 2,
        title: 'First Hearing & Ex-Parte Interim Relief',
        duration: 'Within 3 Days of Filing',
        description: 'If there is imminent threat of violence or dispossession from the shared household, Magistrate can grant ex-parte relief on day one.',
        documents: [
          'Application under Section 23(2) with supporting Affidavit (Form III)',
          'Proof of residing in shared matrimonial home'
        ],
        legalBasis: 'Section 23 PWDVA empowers Magistrate to pass ex-parte interim orders without waiting for the respondent.',
        proTip: 'Ask specifically for an immediate Section 18 Protection Order restraining respondent from visiting your residence or workplace.'
      },
      {
        stepNum: 3,
        title: 'Notice Served on Respondents & Home Visit',
        duration: 'Day 7 – 15',
        description: 'Protection Officer serves court notice upon husband and named in-laws, and inspects the shared household.',
        documents: [
          'Summons served via registered post or Protection Officer',
          'Service report confirming delivery'
        ],
        legalBasis: 'Section 13 PWDVA — Notice must be served within maximum 2 days of issuance.',
        proTip: 'If respondents evade service, court can order service via WhatsApp or affix notice on the door of the matrimonial residence.'
      },
      {
        stepNum: 4,
        title: 'Respondent Reply & Affidavit of Assets',
        duration: 'Day 30 – 45',
        description: 'Respondents file their written statement and mandatory disclosure of income and assets under Rajnesh v. Neha guidelines.',
        documents: [
          'Written Statement / Objections by Respondents',
          'Comprehensive Disclosure Affidavit of Assets and Liabilities (Enclosure I)'
        ],
        legalBasis: 'Supreme Court guidelines in Rajnesh v. Neha (2020) apply strictly to Section 20 monetary relief claims.',
        proTip: 'Scrutinize respondent bank accounts and tax returns filed; any concealment invites perjury prosecution under Section 340 CrPC / 379 BNSS.'
      },
      {
        stepNum: 5,
        title: 'Final Reliefs & Compensation Order',
        duration: 'Months 2 – 6',
        description: 'Court passes comprehensive final orders granting residence, maintenance, child custody, and damages for emotional trauma.',
        documents: [
          'Evidence on Affidavit (Examination-in-Chief)',
          'Bank accounts, rent agreements, and school fee vouchers'
        ],
        legalBasis: 'Sections 18 (Protection), 19 (Residence), 20 (Monetary), 21 (Custody), 22 (Compensation).',
        proTip: 'Under Section 19(1)(f), if you cannot live in the shared home, respondent must secure alternate accommodation or pay monthly rent.'
      },
      {
        stepNum: 6,
        title: 'Breach of Protection Order & Police Enforcement',
        duration: 'Immediate if Violated',
        description: 'Any breach of a protection order by the respondent is a non-bailable criminal offense requiring immediate police arrest.',
        documents: [
          'Certified copy of Protection Order',
          'Complaint to Protection Officer or SHO of local Police Station'
        ],
        legalBasis: 'Section 31 PWDVA — Penalty for breach of protection order: up to 1 year imprisonment and ₹20,000 fine.',
        proTip: 'Keep digital and physical copies of the protection order with you at all times to show the police if approached.'
      }
    ]
  },
  {
    id: 'maintenance_125',
    title: 'Maintenance Claim Procedure',
    statute: 'Section 125 CrPC / Section 144 BNSS, 2023 & Section 24 Hindu Marriage Act',
    icon: Scale,
    totalDuration: 'Interim: 60 Days | Final: 6 – 18 Months',
    estimatedCost: 'Free via DLSA Legal Aid or ₹15,000 – ₹40,000',
    color: '#f59e0b',
    steps: [
      {
        stepNum: 1,
        title: 'Application for Maintenance & Interim Relief',
        duration: 'Day 1 – 7',
        description: 'Wife/children file petition demonstrating lack of independent income and respondent’s capacity to maintain.',
        documents: [
          'Petition under Section 125 CrPC / Section 144 BNSS',
          'Application for Interim Maintenance under proviso to Section 125(1)',
          'Income & Assets Affidavit conforming to Rajnesh v. Neha format'
        ],
        legalBasis: 'Section 125 CrPC / 144 BNSS is a summary remedy preventing vagrancy and destitution.',
        proTip: 'Always file an Interim Application alongside the main petition so you do not have to wait for full trial to receive financial support.'
      },
      {
        stepNum: 2,
        title: 'Affidavits of Assets and Liabilities (Rajnesh v. Neha)',
        duration: 'Day 30 – 60',
        description: 'Both spouses must file standard-format affidavits disclosing bank accounts, credit cards, real estate, lifestyle, and IT returns.',
        documents: [
          'Form Enclosure I / II / III as mandated by the Supreme Court',
          'Last 3 years Income Tax Returns and Form 16 / 26AS',
          'Statements of all bank accounts for the past 3 years'
        ],
        legalBasis: 'Rajnesh v. Neha (2020) 14 SCC 1 — Mandatory disclosure across all maintenance proceedings nationwide.',
        proTip: 'If respondent claims unemployment but maintains cars or high-end lifestyle, court infers income based on lifestyle.'
      },
      {
        stepNum: 3,
        title: 'Interim Maintenance Order',
        duration: 'Month 2 – 4',
        description: 'Court evaluates prima facie income and awards interim monthly support payable from the date of application.',
        documents: [
          'Court Interim Order directing monthly maintenance payment'
        ],
        legalBasis: 'Supreme Court mandates interim maintenance applications be decided within 60 days.',
        proTip: 'Interim maintenance is payable from the date of filing the application, not the date of order.'
      },
      {
        stepNum: 4,
        title: 'Evidence & Cross-Examination on Income',
        duration: 'Months 6 – 12',
        description: 'Parties depose on oath and undergo cross-examination regarding standard of living, concealed assets, and liabilities.',
        documents: [
          'Salary certificates, EPFO statements, corporate MCA filings',
          'Evidence by way of Affidavit'
        ],
        legalBasis: 'Sections 137 & 138 Indian Evidence Act / Section 142 BSA 2023.',
        proTip: 'If respondent fails to produce salary slips, apply under Section 91 CrPC / 94 BNSS summoning their employer or bank.'
      },
      {
        stepNum: 5,
        title: 'Final Maintenance Quantum & Execution',
        duration: 'Month 12+',
        description: 'Final order fixing permanent monthly maintenance. If default occurs, execution warrant is issued.',
        documents: [
          'Certified Copy of Final Order',
          'Execution Petition under Section 125(3) CrPC / Section 144(3) BNSS'
        ],
        legalBasis: 'Failure to comply without sufficient cause results in warrant for recovery and imprisonment up to 1 month per default.',
        proTip: 'Under Section 125(3), court can attach salary directly at source from employer or freeze bank accounts.'
      }
    ]
  },
  {
    id: 'child_custody',
    title: 'Child Custody & Visitation Roadmap',
    statute: 'Guardians and Wards Act, 1890 & Section 26 Hindu Marriage Act',
    icon: Users,
    totalDuration: 'Interim Visitation: 30 Days | Full Custody: 1 – 2 Years',
    estimatedCost: '₹20,000 – ₹60,000',
    color: '#10b981',
    steps: [
      {
        stepNum: 1,
        title: 'Custody & Interim Visitation Application',
        duration: 'Day 1 – 15',
        description: 'Filing application for legal custody, physical custody, or urgent weekend/holiday interim visitation rights.',
        documents: [
          'Application under Section 7/9/12 Guardians and Wards Act, 1890',
          'Birth certificate and school admission records of the child',
          'Proof of parent-child bond (photographs, medical involvement, school reports)'
        ],
        legalBasis: 'Gaurav Nagpal v. Sumedha Nagpal (2009) 1 SCC 42 — Welfare of the child is the paramount consideration, overriding statutory rights.',
        proTip: 'Never ask for full denial of access to the other parent unless physical safety is proven; courts favor shared parenting.'
      },
      {
        stepNum: 2,
        title: 'Judge’s Chamber Interaction with the Child',
        duration: 'Month 1 – 2',
        description: 'Judge meets the child privately in chambers or Child Friendly Court room to gauge mental state, comfort, and wishes.',
        documents: [
          'Confidential Court interaction report'
        ],
        legalBasis: 'Section 17(3) Guardians and Wards Act — If child is old enough to form an intelligent preference, court may consider it.',
        proTip: 'Do not coach or instruct the child before the interaction. Family court judges are experienced at detecting parental alienation.'
      },
      {
        stepNum: 3,
        title: 'Interim Visitation Schedule Established',
        duration: 'Month 2 – 3',
        description: 'Court establishes a structured visitation plan: weekend meetings, video calls, festival sharing, and summer vacation stays.',
        documents: [
          'Detailed Visitation Protocol Order'
        ],
        legalBasis: 'Yashita Sahu v. State of Rajasthan (2020) 3 SCC 67 — Child has the fundamental right to love and affection of both parents.',
        proTip: 'Supervised visitation in the Family Court children’s room is common initially until comfort and trust are established.'
      },
      {
        stepNum: 4,
        title: 'Final Custody & Shared Guardianship Decree',
        duration: 'Month 12+',
        description: 'Judgment establishing residential custody, education decision rights, financial upbringing contributions, and passport custody.',
        documents: [
          'Detailed Custody Decree & Parenting Plan'
        ],
        legalBasis: 'Section 26 HMA / GWA — Custody orders are never final and can be modified whenever child welfare demands.',
        proTip: 'Either parent can apply for modification of custody if circumstances change (relocation, remarriage, or neglect).'
      }
    ]
  }
];

export default function CourtRoadmap({ language = 'en' }) {
  const [activeTrackId, setActiveTrackId] = useState('mutual_divorce');
  const [activeStepIndex, setActiveStepIndex] = useState(0);

  const activeTrack = TRACKS.find((t) => t.id === activeTrackId) || TRACKS[0];
  const activeStep = activeTrack.steps[activeStepIndex] || activeTrack.steps[0];
  const IconComponent = activeTrack.icon;

  function handleSelectTrack(id) {
    setActiveTrackId(id);
    setActiveStepIndex(0);
  }

  return (
    <div className="roadmap-container">
      {/* Header */}
      <div className="roadmap-header">
        <div className="roadmap-header-icon" style={{ borderColor: `${activeTrack.color}40`, background: `${activeTrack.color}15` }}>
          <Compass size={28} style={{ color: activeTrack.color }} />
        </div>
        <div>
          <h2 className="roadmap-title">Interactive Court Procedure Roadmap</h2>
          <p className="roadmap-subtitle">
            Demystifying Indian Family Court and PWDVA proceedings step-by-step with realistic timelines, required documents, and Supreme Court directives.
          </p>
        </div>
      </div>

      {/* Track Selector Tabs */}
      <div className="roadmap-track-tabs">
        {TRACKS.map((t) => {
          const TIcon = t.icon;
          const isActive = t.id === activeTrackId;
          return (
            <button
              key={t.id}
              className={`track-tab-btn ${isActive ? 'track-tab-btn--active' : ''}`}
              style={{
                borderColor: isActive ? t.color : undefined,
                background: isActive ? `${t.color}18` : undefined
              }}
              onClick={() => handleSelectTrack(t.id)}
            >
              <TIcon size={18} style={{ color: isActive ? t.color : '#8faad4' }} />
              <span>{t.title}</span>
            </button>
          );
        })}
      </div>

      {/* Track Overview Card */}
      <div className="track-overview-card" style={{ borderColor: `${activeTrack.color}35` }}>
        <div className="track-statute-row">
          <div>
            <div className="track-statute-badge" style={{ color: activeTrack.color, background: `${activeTrack.color}15`, borderColor: `${activeTrack.color}30` }}>
              Governing Law
            </div>
            <div className="track-statute-title">{activeTrack.statute}</div>
          </div>
        </div>

        <div className="track-meta-grid">
          <div className="track-meta-item">
            <Clock size={16} className="track-meta-icon" />
            <div>
              <div className="track-meta-label">Estimated Timeline</div>
              <div className="track-meta-val">{activeTrack.totalDuration}</div>
            </div>
          </div>

          <div className="track-meta-item">
            <Scale size={16} className="track-meta-icon" />
            <div>
              <div className="track-meta-label">Court Fee & Cost Range</div>
              <div className="track-meta-val">{activeTrack.estimatedCost}</div>
            </div>
          </div>
        </div>
      </div>

      {/* Step Stepper Progress Bar */}
      <div className="step-stepper-bar">
        {activeTrack.steps.map((st, idx) => {
          const isCurrent = idx === activeStepIndex;
          const isPast = idx < activeStepIndex;
          return (
            <button
              key={idx}
              className={`stepper-pill ${isCurrent ? 'stepper-pill--active' : ''} ${isPast ? 'stepper-pill--past' : ''}`}
              onClick={() => setActiveStepIndex(idx)}
              style={{
                borderColor: isCurrent ? activeTrack.color : undefined,
                background: isCurrent ? `${activeTrack.color}25` : undefined
              }}
            >
              <div
                className="stepper-circle"
                style={{
                  background: isCurrent ? activeTrack.color : isPast ? '#10b981' : 'rgba(255,255,255,0.1)',
                  color: isCurrent || isPast ? '#0a1428' : '#8faad4'
                }}
              >
                {isPast ? <CheckCircle2 size={13} /> : st.stepNum}
              </div>
              <div className="stepper-info">
                <span className="stepper-step-title">{st.title}</span>
                <span className="stepper-duration">{st.duration}</span>
              </div>
            </button>
          );
        })}
      </div>

      {/* Active Step Detailed Card */}
      <div className="active-step-card" style={{ borderColor: `${activeTrack.color}40` }}>
        <div className="step-card-header">
          <div className="step-number-tag" style={{ background: activeTrack.color, color: '#070a11' }}>
            Stage {activeStep.stepNum} of {activeTrack.steps.length}
          </div>
          <div className="step-time-tag">
            <Calendar size={14} />
            <span>{activeStep.duration}</span>
          </div>
        </div>

        <h3 className="step-main-title">{activeStep.title}</h3>
        <p className="step-desc">{activeStep.description}</p>

        {/* Mandatory Documents */}
        <div className="step-detail-section">
          <h4 className="detail-section-title">
            <FileCheck size={16} style={{ color: '#38bdf8' }} />
            Mandatory Documents & Stamp Papers Needed
          </h4>
          <ul className="docs-list">
            {activeStep.documents.map((doc, i) => (
              <li key={i}>
                <CheckCircle2 size={14} className="doc-check-icon" />
                <span>{doc}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Legal Authority & Precedent */}
        <div className="step-detail-section legal-authority-box">
          <h4 className="detail-section-title">
            <Scale size={16} style={{ color: '#f59e0b' }} />
            Statutory Rule & Supreme Court Precedent
          </h4>
          <p className="legal-basis-p">{activeStep.legalBasis}</p>
        </div>

        {/* Litigant Pro-Tip */}
        <div className="step-detail-section pro-tip-box">
          <h4 className="detail-section-title" style={{ color: '#38bdf8' }}>
            <Sparkles size={16} style={{ color: '#38bdf8' }} />
            Litigant Pro-Tip & Strategic Advice
          </h4>
          <p className="pro-tip-p">{activeStep.proTip}</p>
        </div>

        {/* Navigation Buttons */}
        <div className="step-nav-footer">
          <button
            className="step-nav-btn"
            disabled={activeStepIndex === 0}
            onClick={() => setActiveStepIndex((i) => Math.max(0, i - 1))}
          >
            ← Previous Stage
          </button>
          <button
            className="step-nav-btn step-nav-btn--primary"
            style={{ background: activeTrack.color }}
            disabled={activeStepIndex === activeTrack.steps.length - 1}
            onClick={() => setActiveStepIndex((i) => Math.min(activeTrack.steps.length - 1, i + 1))}
          >
            Next Stage →
          </button>
        </div>
      </div>
    </div>
  );
}

