/**
 * LegalAidLocator.jsx
 *
 * NALSA / DLSA Free Legal Aid & Family Court Directory
 * Article 39A Indian Constitution & Legal Services Authorities Act, 1987
 * District-level lookup for Family Courts, DLSA Offices, Sakhi Centers, and Helplines.
 */

import React, { useState, useMemo } from 'react';
import {
  Building2,
  PhoneCall,
  MapPin,
  ShieldCheck,
  Search,
  ExternalLink,
  HelpCircle,
  FileText,
  CheckCircle2,
  Scale,
  Users2,
  Clock,
  HeartHandshake
} from 'lucide-react';

// District directory covering key states & metropolitan hubs
const DISTRICT_DATA = [
  {
    state: 'Karnataka',
    district: 'Bengaluru Urban',
    familyCourt: 'Principal Judge, Family Court Complex, Nyaya Degula, Siddaiah Road, Bengaluru - 560027',
    dlsaOffice: 'District Legal Services Authority, City Civil Court Complex, Bengaluru - 560001',
    dlsaPhone: '080-22111746 / 080-22210874',
    sakhiCenter: 'Sakhi One Stop Centre, Bowring & Lady Curzon Hospital premises, Bengaluru',
    sakhiPhone: '080-25591325 / 181',
    poContact: 'District Child Protection & Dowry Prohibition Officer, Multistoried Building, Bengaluru'
  },
  {
    state: 'Karnataka',
    district: 'Mysuru',
    familyCourt: 'Family Court, Law Courts Complex, Krishnaraja Boulevard, Chamarajapuram, Mysuru - 570005',
    dlsaOffice: 'DLSA, District Court Building, Mysuru',
    dlsaPhone: '0821-2330130',
    sakhiCenter: 'One Stop Centre, K.R. Hospital Premises, Mysuru',
    sakhiPhone: '0821-2420003 / 181',
    poContact: 'Protection Officer, Women and Child Development Department, Mysuru'
  },
  {
    state: 'Maharashtra',
    district: 'Mumbai City & Suburban',
    familyCourt: 'Family Court Complex, Bandra Kurla Complex (BKC), Bandra (East), Mumbai - 400051',
    dlsaOffice: 'City Civil Court & DLSA, Old Secretariat Building, Fort, Mumbai - 400032',
    dlsaPhone: '022-22676348 / 022-26591740',
    sakhiCenter: 'Sakhi Centre, KEM Hospital / Sion Hospital campus, Mumbai',
    sakhiPhone: '022-24107000 / 181',
    poContact: 'Protection Officer (PWDVA), Old Custom House, Fort, Mumbai'
  },
  {
    state: 'Maharashtra',
    district: 'Pune',
    familyCourt: 'Principal Judge, Family Court, Bharati Bhavan, Behind Alka Talkies, Sadashiv Peth, Pune - 411030',
    dlsaOffice: 'Pune District Legal Services Authority, New District Court Building, Shivajinagar, Pune - 411005',
    dlsaPhone: '020-25534884',
    sakhiCenter: 'Sakhi One Stop Centre, Sassoon General Hospital, Pune',
    sakhiPhone: '020-26128000 / 181',
    poContact: 'Protection Officer (PWDVA), Shivajinagar Court Campus, Pune'
  },
  {
    state: 'Delhi (NCT)',
    district: 'Central / New Delhi',
    familyCourt: 'Principal Judge, Family Court, Patiala House Courts Complex, New Delhi - 110001',
    dlsaOffice: 'New Delhi Legal Services Authority, Patiala House Courts, New Delhi',
    dlsaPhone: '011-23072352 / 15100',
    sakhiCenter: 'One Stop Centre, Lady Hardinge Medical College, Connaught Place, New Delhi',
    sakhiPhone: '011-23363362 / 181',
    poContact: 'Protection Officer, Dept of Women & Child Development, 1 Canning Lane, K.G. Marg, New Delhi'
  },
  {
    state: 'Delhi (NCT)',
    district: 'South / Saket',
    familyCourt: 'Family Court, Saket Court Complex, Sector 6, Pushp Vihar, New Delhi - 110017',
    dlsaOffice: 'South District Legal Services Authority, Saket Courts, New Delhi',
    dlsaPhone: '011-29562524 / 15100',
    sakhiCenter: 'Sakhi Centre, AIIMS Trauma Centre / Safdarjung Hospital, New Delhi',
    sakhiPhone: '011-26165060 / 181',
    poContact: 'Protection Officer, District WCD Office, Saket, New Delhi'
  },
  {
    state: 'Telangana',
    district: 'Hyderabad',
    familyCourt: 'City Civil Court & Family Court Complex, Purani Haveli, Hyderabad - 500002',
    dlsaOffice: 'Metropolitan Legal Services Authority, City Civil Court Campus, Purani Haveli, Hyderabad',
    dlsaPhone: '040-24520979 / 15100',
    sakhiCenter: 'Sakhi One Stop Centre, Osmania General Hospital Campus, Afzal Gunj, Hyderabad',
    sakhiPhone: '040-24600121 / 181',
    poContact: 'District Welfare Officer & Protection Officer, Collectorate Complex, Chirag Ali Lane, Hyderabad'
  },
  {
    state: 'Tamil Nadu',
    district: 'Chennai',
    familyCourt: 'Principal Family Court, High Court Campus, George Town, Chennai - 600104',
    dlsaOffice: 'District Legal Services Authority, ADR Centre, High Court Campus, Chennai - 600104',
    dlsaPhone: '044-25342441 / 15100',
    sakhiCenter: 'One Stop Centre, Kilpauk Medical College Hospital campus, Chennai',
    sakhiPhone: '044-28364949 / 181',
    poContact: 'District Social Welfare Officer & Protection Officer, Singaravelar Maaligai, Rajaji Salai, Chennai'
  },
  {
    state: 'West Bengal',
    district: 'Kolkata',
    familyCourt: 'City Civil Court & Family Court, 2 & 3 Kiran Shankar Roy Road, Kolkata - 700001',
    dlsaOffice: 'District Legal Services Authority, City Civil Court, Bankshall Street, Kolkata - 700001',
    dlsaPhone: '033-22485501 / 15100',
    sakhiCenter: 'Sakhi OSC, Medical College and Hospital premises, College Street, Kolkata',
    sakhiPhone: '033-22551621 / 181',
    poContact: 'Protection Officer (DV), Social Welfare Department, Salt Lake, Kolkata'
  },
  {
    state: 'Gujarat',
    district: 'Ahmedabad',
    familyCourt: 'Family Court, Bhadra, Old High Court Building, Ahmedabad - 380001',
    dlsaOffice: 'Ahmedabad District Legal Services Authority, City Civil Court Complex, Bhadra, Ahmedabad',
    dlsaPhone: '079-25507119 / 15100',
    sakhiCenter: 'One Stop Crisis Centre, Civil Hospital Campus, Asarwa, Ahmedabad',
    sakhiPhone: '079-22683721 / 181',
    poContact: 'District Women and Child Officer, Collector Office, Subhash Bridge, Ahmedabad'
  }
];

const ELIGIBILITY_RULES = [
  { group: 'Women & Children', rule: 'Eligible automatically without any income restriction (Sec 12(c) LSAA, 1987).' },
  { group: 'Persons with Disabilities', rule: 'Eligible automatically as per Persons with Disabilities Act (Sec 12(e)).' },
  { group: 'Victims of Violence & Trafficking', rule: 'Eligible automatically without income restriction (Sec 12(d)).' },
  { group: 'General Income Category', rule: 'Eligible if annual family income is below state ceiling (typically ₹3,00,000/yr).' }
];

export default function LegalAidLocator({ language = 'en' }) {
  const [selectedState, setSelectedState] = useState('All');
  const [searchQuery, setSearchQuery] = useState('');
  const [showEligibility, setShowEligibility] = useState(false);

  // Unique states
  const states = useMemo(() => {
    return ['All', ...Array.from(new Set(DISTRICT_DATA.map((d) => d.state)))];
  }, []);

  // Filtered districts
  const filteredDistricts = useMemo(() => {
    return DISTRICT_DATA.filter((item) => {
      const matchState = selectedState === 'All' || item.state === selectedState;
      const matchQuery =
        !searchQuery ||
        item.district.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.state.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.familyCourt.toLowerCase().includes(searchQuery.toLowerCase());
      return matchState && matchQuery;
    });
  }, [selectedState, searchQuery]);

  return (
    <div className="locator-container">
      {/* Header */}
      <div className="locator-header">
        <div className="locator-header-icon">
          <Building2 size={28} style={{ color: '#f59e0b' }} />
        </div>
        <div>
          <h2 className="locator-title">Free Legal Aid & Family Court Directory</h2>
          <p className="locator-subtitle">
            Under Article 39A of the Indian Constitution, free legal counsel and court representation are guaranteed through District Legal Services Authorities (DLSA) and NALSA.
          </p>
        </div>
      </div>

      {/* Emergency Helplines Quick Banner */}
      <div className="helpline-banner-grid">
        <div className="helpline-card helpline-card--nalsa">
          <PhoneCall size={20} className="helpline-icon" />
          <div className="helpline-details">
            <div className="helpline-number">15100</div>
            <div className="helpline-name">NALSA National Legal Aid Helpline (24×7 Toll-Free)</div>
          </div>
        </div>

        <div className="helpline-card helpline-card--women">
          <PhoneCall size={20} className="helpline-icon" />
          <div className="helpline-details">
            <div className="helpline-number">181 / 1091</div>
            <div className="helpline-name">Women Helpline (Domestic Abuse & Distress Support)</div>
          </div>
        </div>

        <div className="helpline-card helpline-card--emergency">
          <PhoneCall size={20} className="helpline-icon" />
          <div className="helpline-details">
            <div className="helpline-number">112</div>
            <div className="helpline-name">National Emergency Response (Police, Ambulance)</div>
          </div>
        </div>
      </div>

      {/* Eligibility Dropdown / Card */}
      <div className="eligibility-card">
        <div
          className="eligibility-header"
          onClick={() => setShowEligibility((prev) => !prev)}
        >
          <div className="eligibility-title-wrap">
            <Scale size={18} style={{ color: '#38bdf8' }} />
            <span className="eligibility-title">
              Who is Entitled to 100% Free Government Legal Aid? (Section 12 LSAA, 1987)
            </span>
          </div>
          <span className="eligibility-toggle-text">
            {showEligibility ? 'Hide Details' : 'Check Eligibility →'}
          </span>
        </div>

        {showEligibility && (
          <div className="eligibility-body">
            <p className="eligibility-intro">
              You do not need to pay any advocate fee, court fee, or drafting charges if you qualify under any of the categories below:
            </p>
            <div className="eligibility-grid">
              {ELIGIBILITY_RULES.map((r, i) => (
                <div key={i} className="eligibility-item">
                  <CheckCircle2 size={16} style={{ color: '#10b981', flexShrink: 0 }} />
                  <div>
                    <strong>{r.group}:</strong> <span>{r.rule}</span>
                  </div>
                </div>
              ))}
            </div>
            <div className="how-to-apply-note">
              <strong>How to Apply:</strong> Simply visit the Front Office of your local DLSA with an ID proof and write a 1-page application stating your dispute. A dedicated panel advocate will be assigned to fight your case free of cost.
            </div>
          </div>
        )}
      </div>

      {/* Filter & Search Bar */}
      <div className="locator-filters-row">
        <div className="state-select-wrap">
          <label>Filter by State:</label>
          <select value={selectedState} onChange={(e) => setSelectedState(e.target.value)}>
            {states.map((st) => (
              <option key={st} value={st}>{st}</option>
            ))}
          </select>
        </div>

        <div className="locator-search-wrap">
          <label>Search District or Court:</label>
          <div className="search-input-box">
            <Search size={16} className="search-icon" />
            <input
              type="text"
              placeholder="e.g. Bengaluru, Pune, Saket, High Court..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
        </div>
      </div>

      {/* District Cards Grid */}
      <div className="district-cards-grid">
        {filteredDistricts.length > 0 ? (
          filteredDistricts.map((item, idx) => (
            <div key={idx} className="district-card">
              <div className="district-card-top">
                <span className="district-name">{item.district}</span>
                <span className="district-state-badge">{item.state}</span>
              </div>

              {/* Family Court Info */}
              <div className="district-field">
                <div className="field-label">
                  <Building2 size={15} style={{ color: '#38bdf8' }} />
                  <span>Principal Family Court</span>
                </div>
                <div className="field-val">{item.familyCourt}</div>
              </div>

              {/* DLSA Info */}
              <div className="district-field">
                <div className="field-label">
                  <Scale size={15} style={{ color: '#f59e0b' }} />
                  <span>District Legal Services Authority (DLSA)</span>
                </div>
                <div className="field-val">{item.dlsaOffice}</div>
                <div className="field-phone">
                  <PhoneCall size={13} />
                  <span>{item.dlsaPhone}</span>
                </div>
              </div>

              {/* Sakhi / One-Stop Centre */}
              <div className="district-field">
                <div className="field-label">
                  <ShieldCheck size={15} style={{ color: '#10b981' }} />
                  <span>Sakhi One-Stop Crisis Center (Medical & Shelter)</span>
                </div>
                <div className="field-val">{item.sakhiCenter}</div>
                <div className="field-phone">
                  <PhoneCall size={13} />
                  <span>{item.sakhiPhone}</span>
                </div>
              </div>

              {/* Protection Officer */}
              <div className="district-field">
                <div className="field-label">
                  <Users2 size={15} style={{ color: '#a78bfa' }} />
                  <span>Protection Officer (PWDVA)</span>
                </div>
                <div className="field-val">{item.poContact}</div>
              </div>
            </div>
          ))
        ) : (
          <div className="no-districts-card">
            <Building2 size={32} style={{ color: '#5a84a8' }} />
            <div>No court complexes found matching your search.</div>
            <p>Call the 24×7 NALSA Helpline at <strong>15100</strong> for your district office.</p>
          </div>
        )}
      </div>
    </div>
  );
}
