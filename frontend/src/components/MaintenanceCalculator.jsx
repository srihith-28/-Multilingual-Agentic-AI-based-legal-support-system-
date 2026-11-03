/**
 * MaintenanceCalculator.jsx
 *
 * Interactive Maintenance & Alimony Calculator
 * Based on Supreme Court guidelines in Rajnesh v. Neha (2020)
 */

import React, { useState, useMemo } from 'react';
import { Calculator, IndianRupee, Info, ChevronDown, ChevronUp } from 'lucide-react';

// ─── Multilingual labels ──────────────────────────────────────────────────────
const LABELS = {
  en: {
    title: 'Maintenance & Alimony Calculator',
    subtitle: 'Based on Rajnesh v. Neha (2020) Supreme Court Guidelines',
    husbandIncome: "Husband's Net Monthly Income (₹)",
    wifeIncome: "Wife's Net Monthly Income (₹)",
    children: 'Number of Minor Children',
    childExpenses: 'School/Tuition Expenses per Child (₹/month)',
    cityTier: 'City Tier',
    cityOptions: ['Metro (Delhi, Mumbai, Bangalore)', 'Tier-2 (Pune, Hyderabad, Ahmedabad)', 'Tier-3 / Rural'],
    calculate: 'Calculate Estimate',
    results: 'Estimated Maintenance Range',
    spouseMaint: 'Spouse Maintenance',
    childSupport: 'Child Support',
    totalRange: 'Total Estimated Range',
    perMonth: '/month',
    factors: '10 Factors Courts Evaluate',
    disclaimer: '⚠️ This is an educational estimate only. Actual court orders depend on detailed facts, legal arguments, and judicial discretion. Consult a qualified family law advocate.',
    basis: 'Legal Basis',
    noResult: 'Fill in the details above to calculate.',
    to: 'to',
    cityMultiplierLabel: 'City Cost-of-Living Factor',
  },
  hi: {
    title: 'भरण-पोषण और गुजारा भत्ता कैलकुलेटर',
    subtitle: 'राजनेश बनाम नेहा (2020) सुप्रीम कोर्ट दिशानिर्देशों पर आधारित',
    husbandIncome: 'पति की शुद्ध मासिक आय (₹)',
    wifeIncome: 'पत्नी की शुद्ध मासिक आय (₹)',
    children: 'अवयस्क बच्चों की संख्या',
    childExpenses: 'प्रति बच्चे स्कूल/ट्यूशन खर्च (₹/माह)',
    cityTier: 'शहर श्रेणी',
    cityOptions: ['मेट्रो', 'टियर-2', 'टियर-3 / ग्रामीण'],
    calculate: 'अनुमान लगाएं',
    results: 'अनुमानित भरण-पोषण सीमा',
    spouseMaint: 'पति/पत्नी भरण-पोषण',
    childSupport: 'बाल सहायता',
    totalRange: 'कुल अनुमानित सीमा',
    perMonth: '/माह',
    factors: '10 कारक जो न्यायालय मूल्यांकन करता है',
    disclaimer: '⚠️ यह केवल एक शैक्षिक अनुमान है। वास्तविक न्यायालय आदेश विस्तृत तथ्यों पर निर्भर करते हैं। एक योग्य पारिवारिक कानून वकील से परामर्श करें।',
    basis: 'कानूनी आधार',
    noResult: 'गणना करने के लिए ऊपर विवरण भरें।',
    to: 'से',
    cityMultiplierLabel: 'शहर जीवन-यापन कारक',
  },
  kn: {
    title: 'ಜೀವನಾಂಶ ಮತ್ತು ಗುಜರಾನ ಭತ್ಯ ಕ್ಯಾಲ್ಕುಲೇಟರ್',
    subtitle: 'ರಾಜ್ನೇಶ್ vs ನೇಹಾ (2020) ಸುಪ್ರೀಂ ಕೋರ್ಟ್ ಮಾರ್ಗಸೂಚಿ ಆಧಾರಿತ',
    husbandIncome: 'ಗಂಡನ ಮಾಸಿಕ ನಿವ್ವಳ ಆದಾಯ (₹)',
    wifeIncome: 'ಹೆಂಡತಿಯ ಮಾಸಿಕ ನಿವ್ವಳ ಆದಾಯ (₹)',
    children: 'ಅಪ್ರಾಪ್ತ ಮಕ್ಕಳ ಸಂಖ್ಯೆ',
    childExpenses: 'ಪ್ರತಿ ಮಗುವಿಗೆ ಶಾಲೆ/ಟ್ಯೂಷನ್ ವೆಚ್ಚ (₹/ತಿಂಗಳು)',
    cityTier: 'ನಗರ ವರ್ಗ',
    cityOptions: ['ಮೆಟ್ರೋ', 'ಟಯರ್-2', 'ಟಯರ್-3 / ಗ್ರಾಮೀಣ'],
    calculate: 'ಲೆಕ್ಕ ಹಾಕಿ',
    results: 'ಅಂದಾಜು ಜೀವನಾಂಶ ಶ್ರೇಣಿ',
    spouseMaint: 'ಸಂಗಾತಿ ಜೀವನಾಂಶ',
    childSupport: 'ಮಕ್ಕಳ ಬೆಂಬಲ',
    totalRange: 'ಒಟ್ಟು ಅಂದಾಜು ಶ್ರೇಣಿ',
    perMonth: '/ತಿಂಗಳು',
    factors: 'ನ್ಯಾಯಾಲಯ ಮೌಲ್ಯಮಾಪನ ಮಾಡುವ 10 ಅಂಶಗಳು',
    disclaimer: '⚠️ ಇದು ಕೇವಲ ಶೈಕ್ಷಣಿಕ ಅಂದಾಜು. ವಾಸ್ತವಿಕ ನ್ಯಾಯಾಲಯ ಆದೇಶಗಳು ವಿಸ್ತೃತ ಸಂಗತಿಗಳ ಮೇಲೆ ಅವಲಂಬಿತವಾಗಿರುತ್ತವೆ।',
    basis: 'ಕಾನೂನು ಆಧಾರ',
    noResult: 'ಲೆಕ್ಕ ಹಾಕಲು ಮೇಲಿನ ವಿವರಗಳನ್ನು ಭರ್ತಿ ಮಾಡಿ.',
    to: 'ರಿಂದ',
    cityMultiplierLabel: 'ನಗರ ಜೀವನ ವೆಚ್ಚ ಅಂಶ',
  },
  te: {
    title: 'భరణపోషణ మరియు జీవనభృతి కాలిక్యులేటర్',
    subtitle: 'రాజ్నేష్ vs నేహా (2020) సుప్రీం కోర్ట్ మార్గదర్శకాలు ఆధారంగా',
    husbandIncome: 'భర్త నెట్ నెలసరి ఆదాయం (₹)',
    wifeIncome: 'భార్య నెట్ నెలసరి ఆదాయం (₹)',
    children: 'మైనర్ పిల్లల సంఖ్య',
    childExpenses: 'పిల్లల పాఠశాల/ట్యూషన్ ఖర్చు (₹/నెల)',
    cityTier: 'నగర స్థాయి',
    cityOptions: ['మెట్రో', 'టైర్-2', 'టైర్-3 / గ్రామీణ'],
    calculate: 'అంచనా వేయండి',
    results: 'అంచనా భరణపోషణ పరిధి',
    spouseMaint: 'జీవిత భాగస్వామి భరణపోషణ',
    childSupport: 'పిల్లల మద్దతు',
    totalRange: 'మొత్తం అంచనా పరిధి',
    perMonth: '/నెల',
    factors: 'న్యాయస్థానం మూల్యాంకనం చేసే 10 అంశాలు',
    disclaimer: '⚠️ ఇది కేవలం విద్యా అంచనా మాత్రమే. వాస్తవ న్యాయస్థాన ఆదేశాలు వివరణాత్మక వాస్తవాలపై ఆధారపడతాయి.',
    basis: 'చట్టపరమైన ఆధారం',
    noResult: 'లెక్కించడానికి పై వివరాలు నమోదు చేయండి.',
    to: 'నుండి',
    cityMultiplierLabel: 'నగర జీవన వ్యయ కారకం',
  },
};

const FACTORS = [
  { en: 'Income and earning capacity of both spouses', hi: 'दोनों पक्षों की आय और कमाई की क्षमता', kn: 'ಎರಡೂ ಪಕ್ಷಗಳ ಆದಾಯ ಮತ್ತು ಗಳಿಕೆ ಸಾಮರ್ಥ್ಯ', te: 'ఇద్దరు జీవిత భాగస్వాముల ఆదాయం మరియు సంపాదనా సామర్థ్యం' },
  { en: 'Financial needs and obligations of the claimant', hi: 'दावेदार की वित्तीय जरूरतें', kn: 'ದಾವೆದಾರರ ಆರ್ಥಿಕ ಅಗತ್ಯಗಳು', te: 'దాఖలుదారుని ఆర్థిక అవసరాలు' },
  { en: 'Standard of living during marriage', hi: 'विवाह के दौरान जीवन स्तर', kn: 'ವಿವಾಹದ ಸಮಯದಲ್ಲಿ ಜೀವನ ಮಟ್ಟ', te: 'వివాహ సమయంలో జీవన ప్రమాణం' },
  { en: 'Duration of the marriage', hi: 'विवाह की अवधि', kn: 'ವಿವಾಹದ ಅವಧಿ', te: 'వివాహ వ్యవధి' },
  { en: 'Age and health of both spouses', hi: 'दोनों पक्षों की आयु और स्वास्थ्य', kn: 'ಎರಡೂ ಪಕ್ಷಗಳ ವಯಸ್ಸು ಮತ್ತು ಆರೋಗ್ಯ', te: 'ఇద్దరు జీవిత భాగస్వాముల వయస్సు మరియు ఆరోగ్యం' },
  { en: 'Custody and child-rearing responsibilities', hi: 'बच्चों की अभिरक्षा और पालन-पोषण की जिम्मेदारी', kn: 'ಮಕ್ಕಳ ಸಂರಕ್ಷಣೆ ಮತ್ತು ಪಾಲನೆ-ಪೋಷಣೆ ಜವಾಬ್ದಾರಿ', te: 'పిల్లల సంరక్షణ మరియు పెంపకం బాధ్యత' },
  { en: 'Employment gap due to marriage/childcare', hi: 'विवाह/बच्चों की देखभाल के कारण रोजगार अंतर', kn: 'ವಿವಾಹ/ಮಕ್ಕಳ ಆರೈಕೆ ಕಾರಣ ಉದ್ಯೋಗ ಅಂತರ', te: 'వివాహం/శిశు సంరక్షణ కారణంగా ఉద్యోగ అంతరం' },
  { en: 'Existing liabilities and debts of either party', hi: 'किसी भी पक्ष की मौजूदा देनदारियां', kn: 'ಯಾವುದೇ ಪಕ್ಷದ ಅಸ್ತಿತ್ವದ ಹೊಣೆಗಾರಿಕೆಗಳು', te: 'ఏదైనా పక్షం యొక్క ప్రస్తుత బాధ్యతలు' },
  { en: 'Conduct of the parties and reason for separation', hi: 'पक्षों का आचरण और अलगाव का कारण', kn: 'ಪಕ್ಷಗಳ ನಡವಳಿಕೆ ಮತ್ತು ವಿಭಜನೆಯ ಕಾರಣ', te: 'పక్షాల ప్రవర్తన మరియు విభజన కారణం' },
  { en: 'Property owned by both parties (movable & immovable)', hi: 'दोनों पक्षों की संपत्ति (चल और अचल)', kn: 'ಎರಡೂ ಪಕ್ಷಗಳ ಆಸ್ತಿ (ಚರ ಮತ್ತು ಅಚರ)', te: 'ఇద్దరు పక్షాల ఆస్తి (చర మరియు స్థావర)' },
];

const LEGAL_BASIS = [
  'Section 125 CrPC / Section 144 BNSS — Maintenance of wives, children, and parents',
  'Hindu Marriage Act, 1955 — Sections 24 & 25 (Interim & Permanent Alimony)',
  'Protection of Women from Domestic Violence Act, 2005 — Section 20 (Monetary Reliefs)',
  'Hindu Adoption and Maintenance Act, 1956 — Sections 18–22',
  'Rajnesh v. Neha (2020) 14 SCC 1 — Comprehensive SC guidelines on maintenance',
];

const CITY_MULTIPLIER = { 0: 1.0, 1: 0.85, 2: 0.70 };

// ─── Format INR ──────────────────────────────────────────────────────────────
function formatINR(amount) {
  if (amount >= 100000) return `₹${(amount / 100000).toFixed(1)}L`;
  if (amount >= 1000) return `₹${(amount / 1000).toFixed(1)}K`;
  return `₹${Math.round(amount)}`;
}

// ─── Core Calculation (Rajnesh v. Neha guidelines) ──────────────────────────
function calculateMaintenance({ husbandIncome, wifeIncome, children, childExpenses, cityTier }) {
  const multiplier = CITY_MULTIPLIER[cityTier] ?? 1.0;
  const netDiff = husbandIncome - wifeIncome;

  // Spouse maintenance: 25% of husband's net income if wife has no/low income
  // Reduced proportionally if wife earns more
  let spouseMin = 0;
  let spouseMax = 0;
  if (netDiff > 0) {
    const ratio = wifeIncome > 0 ? Math.max(0, 1 - wifeIncome / husbandIncome) : 1;
    spouseMin = husbandIncome * 0.20 * ratio * multiplier;
    spouseMax = husbandIncome * 0.30 * ratio * multiplier;
  }

  // Child support: 20–25% of husband's income per child (Rajnesh guidelines)
  // Plus actual school expenses (capped at 50% of husband income total)
  const childSupportBase = children * husbandIncome * 0.20 * multiplier;
  const childSupportMax  = children * husbandIncome * 0.25 * multiplier + children * childExpenses;
  const childMin = Math.min(childSupportBase, husbandIncome * 0.5);
  const childMax = Math.min(childSupportMax,  husbandIncome * 0.5);

  const totalMin = Math.round(spouseMin + childMin);
  const totalMax = Math.round(spouseMax + childMax);

  return {
    spouseMin: Math.round(spouseMin),
    spouseMax: Math.round(spouseMax),
    childMin: Math.round(childMin),
    childMax: Math.round(childMax),
    totalMin,
    totalMax,
    hasResult: husbandIncome > 0,
  };
}

// ─── Bar Chart Component ─────────────────────────────────────────────────────
function BreakdownBar({ label, min, max, totalMax, color }) {
  const widthPct = totalMax > 0 ? Math.min(100, (max / totalMax) * 100) : 0;
  return (
    <div className="breakdown-row">
      <div className="breakdown-label">{label}</div>
      <div className="breakdown-bar-track">
        <div
          className="breakdown-bar-fill"
          style={{ width: `${widthPct}%`, background: color }}
        />
      </div>
      <div className="breakdown-amount">
        {formatINR(min)} – {formatINR(max)}
      </div>
    </div>
  );
}

// ─── Main Component ──────────────────────────────────────────────────────────
export default function MaintenanceCalculator({ language = 'en' }) {
  const L = LABELS[language] || LABELS.en;

  const [form, setForm] = useState({
    husbandIncome: '',
    wifeIncome: '',
    children: '0',
    childExpenses: '0',
    cityTier: '0',
  });
  const [showFactors, setShowFactors] = useState(false);
  const [calculated, setCalculated] = useState(false);

  const result = useMemo(() => {
    if (!calculated) return null;
    return calculateMaintenance({
      husbandIncome: parseFloat(form.husbandIncome) || 0,
      wifeIncome: parseFloat(form.wifeIncome) || 0,
      children: parseInt(form.children, 10) || 0,
      childExpenses: parseFloat(form.childExpenses) || 0,
      cityTier: parseInt(form.cityTier, 10),
    });
  }, [calculated, form]);

  function handleChange(e) {
    setForm((f) => ({ ...f, [e.target.name]: e.target.value }));
    setCalculated(false);
  }

  function handleCalculate(e) {
    e.preventDefault();
    setCalculated(true);
  }

  return (
    <div className="calculator-container">
      {/* Header */}
      <div className="calc-header">
        <Calculator size={28} className="calc-icon" />
        <div>
          <h2 className="calc-title">{L.title}</h2>
          <p className="calc-subtitle">{L.subtitle}</p>
        </div>
      </div>

      {/* Form */}
      <form className="calculator-form" onSubmit={handleCalculate}>
        <div className="calc-form-grid">
          <div className="calc-field">
            <label>{L.husbandIncome}</label>
            <div className="calc-input-wrap">
              <IndianRupee size={14} className="calc-input-icon" />
              <input
                type="number"
                name="husbandIncome"
                value={form.husbandIncome}
                onChange={handleChange}
                placeholder="e.g. 80000"
                min="0"
                required
              />
            </div>
          </div>

          <div className="calc-field">
            <label>{L.wifeIncome}</label>
            <div className="calc-input-wrap">
              <IndianRupee size={14} className="calc-input-icon" />
              <input
                type="number"
                name="wifeIncome"
                value={form.wifeIncome}
                onChange={handleChange}
                placeholder="e.g. 0"
                min="0"
              />
            </div>
          </div>

          <div className="calc-field">
            <label>{L.children}</label>
            <input
              type="number"
              name="children"
              value={form.children}
              onChange={handleChange}
              min="0"
              max="10"
            />
          </div>

          <div className="calc-field">
            <label>{L.childExpenses}</label>
            <div className="calc-input-wrap">
              <IndianRupee size={14} className="calc-input-icon" />
              <input
                type="number"
                name="childExpenses"
                value={form.childExpenses}
                onChange={handleChange}
                placeholder="e.g. 5000"
                min="0"
              />
            </div>
          </div>

          <div className="calc-field calc-field-full">
            <label>{L.cityTier}</label>
            <select name="cityTier" value={form.cityTier} onChange={handleChange}>
              {L.cityOptions.map((opt, i) => (
                <option key={i} value={String(i)}>{opt}</option>
              ))}
            </select>
          </div>
        </div>

        <button type="submit" className="calc-btn">
          <Calculator size={16} />
          {L.calculate}
        </button>
      </form>

      {/* Results */}
      {result && result.hasResult ? (
        <div className="calc-result-card">
          <h3 className="result-title">
            <IndianRupee size={18} />
            {L.results}
          </h3>

          <div className="breakdown-chart">
            <BreakdownBar
              label={L.spouseMaint}
              min={result.spouseMin}
              max={result.spouseMax}
              totalMax={result.totalMax}
              color="linear-gradient(90deg, #1e6fa8, #3b9fe8)"
            />
            {parseInt(form.children, 10) > 0 && (
              <BreakdownBar
                label={L.childSupport}
                min={result.childMin}
                max={result.childMax}
                totalMax={result.totalMax}
                color="linear-gradient(90deg, #c47f0a, #f5a623)"
              />
            )}
          </div>

          <div className="total-range-card">
            <div className="total-label">{L.totalRange}</div>
            <div className="total-amount">
              {formatINR(result.totalMin)}
              <span className="total-to"> {L.to} </span>
              {formatINR(result.totalMax)}
              <span className="total-per-month">{L.perMonth}</span>
            </div>
          </div>

          {/* Legal Basis */}
          <div className="legal-basis-section">
            <h4>{L.basis}</h4>
            <ul className="legal-basis-list">
              {LEGAL_BASIS.map((b, i) => (
                <li key={i}>{b}</li>
              ))}
            </ul>
          </div>

          <p className="calc-disclaimer">{L.disclaimer}</p>
        </div>
      ) : calculated ? (
        <div className="calc-result-card calc-no-result">
          <Info size={20} />
          <span>{L.noResult}</span>
        </div>
      ) : null}

      {/* Factors Accordion */}
      <div className="factors-accordion">
        <button
          type="button"
          className="factors-toggle"
          onClick={() => setShowFactors((s) => !s)}
        >
          <Info size={16} />
          {L.factors}
          {showFactors ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </button>
        {showFactors && (
          <ul className="factor-list">
            {FACTORS.map((f, i) => (
              <li key={i}>
                <span className="factor-num">{i + 1}.</span>
                {f[language] || f.en}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
