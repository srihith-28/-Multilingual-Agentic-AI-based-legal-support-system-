import React, { useState, useEffect, useCallback } from 'react';
import Header from './components/Header';
import ChatInterface from './components/ChatInterface';
import CitationDrawer from './components/CitationDrawer';
import EmergencyModal from './components/EmergencyModal';
import MaintenanceCalculator from './components/MaintenanceCalculator';
import DocumentDrafter from './components/DocumentDrafter';
import { sendChatMessageStreaming, sendChatMessage } from './utils/api';

const WELCOME_MESSAGES = {
  en:
    'Namaste. I am **Agent Forge**, an AI-powered Indian Family Law decision support assistant.\n\n' +
    'You can speak or type your queries in **English, हिन्दी, ಕನ್ನಡ, తెలుగు, தமிழ், বাংলা, मराठी, ગુજરાતી, മലയാളം, or اردو** regarding marriage, divorce, child custody, maintenance, and domestic violence protections.\n\n' +
    'How may I assist you today?',
  kn:
    'ನಮಸ್ಕಾರ. ನಾನು **ಏಜೆಂಟ್ ಫೋರ್ಜ್ (Agent Forge)**, AI-ಆಧಾರಿತ ಭಾರತೀಯ ಕೌಟುಂಬಿಕ ಕಾನೂನು ನಿರ್ಧಾರ ಬೆಂಬಲ ಸಹಾಯಕ.\n\n' +
    'ವಿವಾಹ, ವಿಚ್ಛೇದನ, ಮಕ್ಕಳ ಪಾಲನೆ (ಕಸ್ಟಡಿ), ಜೀವನಾಂಶ (ಮೈಂಟೆನೆನ್ಸ್), ಮತ್ತು ಕೌಟುಂಬಿಕ ಹಿಂಸಾಚಾರ ಸಂರಕ್ಷಣೆ ಕುರಿತು ನಿಮ್ಮ ಪ್ರಶ್ನೆಗಳನ್ನು ನೀವು **ಕನ್ನಡ, ಇಂಗ್ಲಿಷ್ ಅಥವಾ ಇತರ ಯಾವುದೇ ಭಾರತೀಯ ಭಾಷೆಯಲ್ಲಿ** ಧ್ವನಿ ಮೂಲಕ ಅಥವಾ ಟೈಪ್ ಮಾಡಿ ಕೇಳಬಹುದು.\n\n' +
    'ಇಂದು ನಾನು ನಿಮಗೆ ಹೇಗೆ ಸಹಾಯ ಮಾಡಲಿ?',
  hi:
    'नमस्ते। मैं **एजेंट फोर्ज (Agent Forge)** हूँ, एक AI-संचालित भारतीय पारिवारिक कानून निर्णय सहायता सहायक।\n\n' +
    'आप विवाह, तलाक, बच्चों की कस्टडी, भरण-पोषण (गुजारा भत्ता), और घरेलू हिंसा संरक्षण से जुड़े अपने प्रश्न **हिन्दी, English या किसी भी भारतीय भाषा में** बोलकर या लिखकर पूछ सकते हैं।\n\n' +
    'आज मैं आपकी किस प्रकार सहायता कर सकता हूँ?',
  te:
    'నమస్కారం. నేను **ఏజెంట్ ఫోర్జ్ (Agent Forge)**, AI-ఆధారిత భారతీయ కుటుంబ చట్ట నిర్ణయ మద్దతు సహాయకుడిని.\n\n' +
    'వివాహం, విడాకులు, పిల్లల సంరక్షణ (కస్టడీ), భరణం (జీవనభృతి), మరియు గృహ హింస రక్షణ చట్టాలకు సంబంధించి మీ సందేహాలను **తెలుగు, ఇంగ్లీష్ లేదా ఇతర భారతీయ భాషలలో** మాట్లాడి లేదా టైప్ చేసి అడగవచ్చు.\n\n' +
    'నేను మీకు ఈ రోజు ఎలా సహాయపడగలను?',
  ta:
    'வணக்கம். நான் **ஏஜென்ட் ஃபோர்ஜ் (Agent Forge)**, AI-ஆற்றல் கொண்ட இந்திய குடும்ப சட்ட முடிவெடுக்கும் உதவி உதவியாளர்.\n\n' +
    'திருமணம், விவாகரத்து, குழந்தை பராமரிப்பு (கஸ்டடி), ஜீவனாம்சம், மற்றும் குடும்ப வன்முறை பாதுகாப்பு தொடர்பான உங்கள் கேள்விகளை **தமிழ், ஆங்கிலம் அல்லது பிற இந்திய மொழிகளில்** பேசியோ அல்லது தட்டச்சு செய்தோ கேட்கலாம்.\n\n' +
    'இன்று நான் உங்களுக்கு எவ்வாறு உதவ முடியும்?',
  bn:
    'নমস্কার। আমি **এজেন্ট ফোর্জ (Agent Forge)**, এআই-চালিত ভারতীয় পারিবারিক আইন সিদ্ধান্ত সহায়তা সহকারী।\n\n' +
    'বিবাহ, বিবাহবিচ্ছেদ, সন্তানের হেফাজত (কাস্টডি), খোরপোশ/ভরণপোষণ, এবং গার্হস্থ্য হিংসা সুরক্ষা সম্পর্কিত আপনার প্রশ্নগুলি **বাংলা, ইংরেজি বা অন্য যেকোনো ভারতীয় ভাষায়** মুখে বলে বা টাইপ করে জিজ্ঞাসা করতে পারেন।\n\n' +
    'আজ আমি আপনাকে কীভাবে সাহায্য করতে পারি?',
  mr:
    'नमस्कार. मी **एजंट फोर्ज (Agent Forge)** आहे, एक AI-सक्षम भारतीय कौटुंबिक कायदा निर्णय सहाय्यक.\n\n' +
    'विवाह, घटस्फोट, मुलांचे पालकत्व (कस्टडी), पोटगी/भरणपोषण, आणि कौटुंबिक हिंसाचार संरक्षण याविषयी तुम्ही तुमचे प्रश्न **मराठी, इंग्रजी किंवा इतर कोणत्याही भारतीय भाषेत** बोलून किंवा टाइप करून विचारू शकता.\n\n' +
    'आज मी आपल्याला कशी मदत करू शकतो?',
  gu:
    'નમસ્તે. હું **એજન્ટ ફોર્જ (Agent Forge)** છું, એક AI-સંચાલિત ભારતીય કૌટુંબિક કાયદા નિર્ણય સહાયક.\n\n' +
    'લગ્ન, છૂટાછેડા, બાળકની કસ્ટડી, ભરણપોષણ, અને ઘરેલું હિંસા સુરક્ષા સંબંધિત તમારા પ્રશ્નો તમે **ગુજરાતી, અંગ્રેજી અથવા કોઈપણ ભારતીય ભાષામાં** બોલીને અથવા ટાઇપ કરીને પૂછી શકો છો.\n\n' +
    'આજે હું તમને કેવી રીતે મદદ કરી શકું?',
  ml:
    'നമസ്കാരം. ഞാൻ **ഏജന്റ് ഫോർജ് (Agent Forge)**, AI അധിഷ്ഠിത ഇന്ത്യൻ കുടുംബ നിയമ തീരുമാന പിന്തുണ സഹായിയാണ്.\n\n' +
    'വിവാഹം, വിവാഹമോചനം, കുട്ടികളുടെ സംരക്ഷണം (കസ്റ്റഡി), ജീവനാംശം, ഗാർഹിക പീഡന സംരക്ഷണം എന്നിവ സംബന്ധിച്ച നിങ്ങളുടെ സംശയങ്ങൾ **മലയാളം, ഇംഗ്ലീഷ് അല്ലെങ്കിൽ മറ്റേതെങ്കിലും ഇന്ത്യൻ ഭാഷകളിൽ** സംസാരിച്ചോ ടൈപ്പ് ചെയ്തോ ചോദിക്കാം.\n\n' +
    'ഇന്ന് ഞാൻ നിങ്ങളെ എങ്ങനെ സഹായിക്കണം?',
  ur:
    'سلام۔ میں **ایجنٹ فورج (Agent Forge)** ہوں، ایک AI پر مبنی ہندوستانی خاندانی قانون کا معاون۔\n\n' +
    'آپ شادی، طلاق، بچوں کی تحویل (کسٹڈی)، نفقہ، اور گھریلو تشدد کے تحفظ کے متعلق اپنے سوالات **اردو، انگریزی یا کسی بھی ہندوستانی زبان میں** بول کر یا لکھ کر پوچھ سکتے ہیں۔\n\n' +
    'آج میں آپ کی کس طرح مدد کر سکتا ہوں؟',
};

export default function App() {
  const [language, setLanguage]                     = useState('en');
  const [isEmergencyModalOpen, setIsEmergencyModal] = useState(false);
  const [citations, setCitations]                   = useState([]);
  const [isLoading, setIsLoading]                   = useState(false);
  const [activeTab, setActiveTab]                   = useState('chat'); // 'chat' | 'calculator' | 'drafter'

  const [sessionId] = useState(
    () => 'sess_' + Math.random().toString(36).substring(2, 10)
  );

  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      sender: 'assistant',
      text: WELCOME_MESSAGES.en,
      language: 'en',
      domain: 'general_family_law',
      citations: [],
    },
  ]);

  // Immediately update intro/welcome message when language changes
  useEffect(() => {
    setMessages((prev) =>
      prev.map((msg) =>
        msg.id === 'welcome'
          ? {
              ...msg,
              text: WELCOME_MESSAGES[language] || WELCOME_MESSAGES.en,
              language: language,
            }
          : msg
      )
    );
  }, [language]);

  // ── Streaming send ─────────────────────────────────────────────────────────
  const handleSendMessage = useCallback(
    async (text, inputMode = 'text', overrideLang = null) => {
      const userMsg = {
        id: 'user_' + Date.now(),
        sender: 'user',
        text,
        language: overrideLang || language,
      };

      setMessages((prev) => [...prev, userMsg]);
      setIsLoading(true);

      // Placeholder streaming message
      const streamId = 'asst_' + Date.now();
      setMessages((prev) => [
        ...prev,
        {
          id: streamId,
          sender: 'assistant',
          text: '',
          language: overrideLang || language,
          domain: null,
          isStreaming: true,
          citations: [],
        },
      ]);

      let usedStreaming = false;

      try {
        await sendChatMessageStreaming({
          message: text,
          session_id: sessionId,
          language: overrideLang || language,
          input_mode: inputMode,
          onChunk: (chunk) => {
            usedStreaming = true;
            setMessages((prev) =>
              prev.map((m) =>
                m.id === streamId ? { ...m, text: m.text + chunk } : m
              )
            );
          },
          onComplete: (data) => {
            setMessages((prev) =>
              prev.map((m) =>
                m.id === streamId
                  ? {
                      ...m,
                      text: data.plain_language_summary || m.text,
                      language: data.detected_language || m.language,
                      domain: data.law_domain,
                      isEmergency: data.is_emergency,
                      needsClarification: data.needs_clarification,
                      clarificationQuestions: data.clarification_questions,
                      citations: data.statutory_citations || [],
                      isStreaming: false,
                    }
                  : m
              )
            );

            if (data.is_emergency) setIsEmergencyModal(true);
            if (data.statutory_citations?.length > 0) {
              setCitations(data.statutory_citations);
            }
            setIsLoading(false);
          },
          onError: async (err) => {
            console.warn('Streaming error, attempting non-streaming fallback:', err);
            try {
              const data = await sendChatMessage({
                message: text,
                session_id: sessionId,
                language: overrideLang || language,
                input_mode: inputMode,
              });
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === streamId
                    ? {
                        ...m,
                        text: data.plain_language_summary,
                        language: data.detected_language,
                        domain: data.law_domain,
                        isEmergency: data.is_emergency,
                        needsClarification: data.needs_clarification,
                        clarificationQuestions: data.clarification_questions,
                        citations: data.statutory_citations || [],
                        isStreaming: false,
                      }
                    : m
                )
              );
              if (data.is_emergency) setIsEmergencyModal(true);
              if (data.statutory_citations?.length > 0) setCitations(data.statutory_citations);
            } catch (fallbackErr) {
              const isTimeout = fallbackErr?.message?.includes('timed out');
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === streamId
                    ? {
                        ...m,
                        text: isTimeout
                          ? '⏳ The legal AI verification process is taking longer than expected. Please try again with a specific question.'
                          : '⚠️ An error occurred while communicating with the legal AI service. Please check your connection and try again.',
                        isStreaming: false,
                      }
                    : m
                )
              );
            }
            setIsLoading(false);
          },
        });
      } catch (err) {
        console.error('Chat error:', err);
        setMessages((prev) =>
          prev.map((m) =>
            m.id === streamId
              ? {
                  ...m,
                  text: '⚠️ An unexpected error occurred. Please try again.',
                  isStreaming: false,
                }
              : m
          )
        );
        setIsLoading(false);
      }
    },
    [language, sessionId]
  );

  return (
    <div className="app-container">
      <Header
        language={language}
        setLanguage={setLanguage}
        onOpenEmergency={() => setIsEmergencyModal(true)}
      />

      {/* Tab Navigation */}
      <nav className="tab-nav">
        <button
          className={`tab-btn${activeTab === 'chat' ? ' tab-btn--active' : ''}`}
          onClick={() => setActiveTab('chat')}
        >
          💬 Legal AI Chat
        </button>
        <button
          className={`tab-btn${activeTab === 'calculator' ? ' tab-btn--active' : ''}`}
          onClick={() => setActiveTab('calculator')}
        >
          🧮 Maintenance Calculator
        </button>
        <button
          className={`tab-btn${activeTab === 'drafter' ? ' tab-btn--active' : ''}`}
          onClick={() => setActiveTab('drafter')}
        >
          📄 Document Drafter
        </button>
      </nav>

      {activeTab === 'chat' && (
        <main className="main-grid">
          <ChatInterface
            messages={messages}
            onSendMessage={handleSendMessage}
            isLoading={isLoading}
            language={language}
            onSelectCitationMessage={(selectedCitations) => {
              if (selectedCitations?.length > 0) {
                setCitations(selectedCitations);
              }
            }}
          />

          <CitationDrawer
            citations={citations}
            onAskAboutSection={(q) => handleSendMessage(q)}
          />
        </main>
      )}

      {activeTab === 'calculator' && (
        <main className="tool-main">
          <MaintenanceCalculator language={language} />
        </main>
      )}

      {activeTab === 'drafter' && (
        <main className="tool-main">
          <DocumentDrafter language={language} />
        </main>
      )}

      <EmergencyModal
        isOpen={isEmergencyModalOpen}
        onClose={() => setIsEmergencyModal(false)}
      />
    </div>
  );
}
