import React, { useState, useRef, useEffect } from 'react';
import { Send, Volume2, User, Bot, Loader2, HelpCircle, ShieldAlert } from 'lucide-react';
import VoiceRecorder from './VoiceRecorder';
import { synthesizeSpeech } from '../utils/api';

function detectScript(text) {
  if (!text) return 'en';
  for (let i = 0; i < text.length; i++) {
    const cp = text.charCodeAt(i);
    if (cp >= 0x0C00 && cp <= 0x0C7F) return 'te'; // Telugu
    if (cp >= 0x0C80 && cp <= 0x0CFF) return 'kn'; // Kannada
    if (cp >= 0x0B80 && cp <= 0x0BFF) return 'ta'; // Tamil
    if (cp >= 0x0980 && cp <= 0x09FF) return 'bn'; // Bengali
    if (cp >= 0x0A80 && cp <= 0x0AFF) return 'gu'; // Gujarati
    if (cp >= 0x0D00 && cp <= 0x0D7F) return 'ml'; // Malayalam
    if (cp >= 0x0600 && cp <= 0x06FF) return 'ur'; // Urdu
    if (cp >= 0x0900 && cp <= 0x097F) return 'hi'; // Devanagari
  }
  return 'en';
}

const CLARIFICATION_TITLES = {
  en: 'Please specify to refine your legal options:',
  hi: 'अपने कानूनी विकल्पों को स्पष्ट करने के लिए कृपया बताएं:',
  kn: 'ನಿಮ್ಮ ಕಾನೂನು ಆಯ್ಕೆಗಳನ್ನು ಸ್ಪಷ್ಟಪಡಿಸಲು ದಯವಿಟ್ಟು ತಿಳಿಸಿ:',
  te: 'మీ చట్టపరమైన ఎంపికలను స్పష్టం చేయడానికి దయచేసి వివరించండి:',
  ta: 'உங்கள் சட்ட விருப்பங்களை தெளிவுபடுத்த தயவுசெய்து குறிப்பிடவும்:',
  bn: 'আপনার আইনি বিকল্পগুলি স্পষ্ট করতে অনুগ্রহ করে উল্লেখ করুন:',
  mr: 'तुमचे कायदेशीर पर्याय स्पष्ट करण्यासाठी कृपया सांगा:',
  gu: 'તમારા કાનૂની વિકલ્પો સ્પષ્ટ કરવા માટે કૃપા કરીને જણાવો:',
  ml: 'നിങ്ങളുടെ നിയമപരമായ ഓപ്ഷനുകൾ വ്യക്തമാക്കാൻ ദയവായി വ്യക്തമാക്കുക:',
  ur: 'اپنے قانونی اختیارات کو واضح کرنے کے لیے براہ کرم بتائیں:',
};

const DOMAIN_LABELS = {
  divorce_mutual_consent: {
    te: 'పరస్పర అంగీకార విడాకులు',
    hi: 'आपसी सहमति से तलाक',
    kn: 'ಪರಸ್ಪರ ಒಪ್ಪಿಗೆಯ ವಿಚ್ಛೇದನ',
    ta: 'பரஸ்பர சம்மத விவாகரத்து',
    bn: 'পারস্পরিক সম্মতিতে বিবাহবিচ্ছেদ',
    mr: 'परस्पर संमतीने घटस्फोट',
    gu: 'પરસ્પર સંમતિથી છૂટાછેડા',
    ml: 'പരസ്പര സമ്മതത്തോടെയുള്ള വിവാഹമോചനം',
    ur: 'باہمی رضامندی سے طلاق',
    en: 'Divorce Mutual Consent',
  },
  divorce_contested: {
    te: 'వివాదాస్పద విడాకులు',
    hi: 'विवादित तलाक',
    kn: 'ವಿವಾದಿತ ವಿಚ್ಛೇದನ',
    ta: 'மறுக்கப்படும் விவாகரத்து',
    bn: 'প্রতিদ্বন্দ্বিতাপূর্ণ বিবাহবিচ্ছেদ',
    mr: 'तक्रारी घटस्फोट',
    gu: 'વિવાદિત છૂટાછેડા',
    ml: 'തർക്കപരമായ വിവാഹമോചനം',
    ur: 'متنازعہ طلاق',
    en: 'Contested Divorce',
  },
  maintenance_alimony: {
    te: 'భరణం / మనోవర్తి',
    hi: 'भरण-पोषण एवं गुजारा भत्ता',
    kn: 'ಜೀವನಾಂಶ / ನಿರ್ವಹಣೆ',
    ta: 'ஜீவனாம்சம் / பராமரிப்பு',
    bn: 'ভরণপোষণ এবং খোরপোশ',
    mr: 'पोटगी आणि देखभाल',
    gu: 'ભરણપોષણ',
    ml: 'ജീവനാംശം',
    ur: 'نفقہ اور گزارہ الاؤنس',
    en: 'Maintenance & Alimony',
  },
  domestic_violence: {
    te: 'గృహహింస రక్షణ',
    hi: 'घरेलू हिंसा से सुरक्षा',
    kn: 'ಗೃಹ ಹಿಂಸಾಚಾರ ರಕ್ಷಣೆ',
    ta: 'குடும்ப வன்முறை பாதுகாப்பு',
    bn: 'গার্হস্থ্য হিংসা সুরক্ষা',
    mr: 'घरगुती हिंसाचार संरक्षण',
    gu: 'ઘરેલુ હિંસા રક્ષણ',
    ml: 'ഗാർഹിക പീഡന സംരക്ഷണം',
    ur: 'گھریلو تشدد سے تحفظ',
    en: 'Domestic Violence',
  },
  child_custody: {
    te: 'పిల్లల సంరక్షణ / కస్టడీ',
    hi: 'बच्चों की कस्टडी',
    kn: 'ಮಕ್ಕಳ ಪಾಲನೆ / ಕಸ್ಟಡಿ',
    ta: 'குழந்தை காவல்',
    bn: 'সন্তানের হেফাজত',
    mr: 'मुलांचा ताबा',
    gu: 'બાળકોની કસ્ટડી',
    ml: 'കുട്ടികളുടെ സംരക്ഷണം',
    ur: 'بچوں کی تحویل',
    en: 'Child Custody',
  },
  restitution_conjugal_rights: {
    te: 'దాంపత్య హక్కుల పునరుద్ధరణ',
    hi: 'वैवाहिक अधिकारों की पुनर्स्थापना',
    kn: 'ದಾಂಪತ್ಯ ಹಕ್ಕುಗಳ ಮರುಸ್ಥಾಪನೆ',
    ta: 'தாம்பத்திய உரிமைகள் மீட்டெடுப்பு',
    bn: 'বৈবাহিক অধিকার পুনরুদ্ধার',
    mr: 'वैवाहिक हक्कांची पुनर्स्थापना',
    gu: 'વૈવાહિક અધિકારોની પુનઃસ્થાપના',
    ml: 'വൈവാഹിക അവകാശങ്ങൾ പുനഃസ്ഥാപിക്കൽ',
    ur: 'ازدواجی حقوق کی بحالی',
    en: 'Restitution of Conjugal Rights',
  },
  property_succession: {
    te: 'ఆస్తి హక్కులు / వారసత్వం',
    hi: 'सम्पत्ति एवं उत्तराधिकार',
    kn: 'ಆಸ್ತಿ ಮತ್ತು ಉತ್ತರಾಧಿಕಾರ',
    ta: 'சொத்து மற்றும் வாரிசுரிமை',
    bn: 'সম্পত্তি এবং উত্তরাধিকার',
    mr: 'मालमत्ता आणि वारसा',
    gu: 'સંપત્તિ અને વારસો',
    ml: 'സ്വത്തും അനന്തരാവകാശവും',
    ur: 'جائیداد اور وراثت',
    en: 'Property Succession',
  },
  general_family_law: {
    te: 'సాధారణ కుటుంబ చట్టం',
    hi: 'सामान्य पारिवारिक कानून',
    kn: 'ಸಾಮಾನ್ಯ ಕುಟುಂಬ ಕಾನೂನು',
    ta: 'பொது குடும்ப சட்டம்',
    bn: 'সাধারণ পারিবারিক আইন',
    mr: 'सामान्य कौटुंबिक कायदा',
    gu: 'સામાન્ય કૌટુંબિક કાયદો',
    ml: 'പൊതു കുടുംബ നിയമം',
    ur: 'عام خاندانی قانون',
    en: 'General Family Law',
  },
};

const LISTEN_LABELS = {
  en: { play: 'Listen', pause: 'Pause' },
  kn: { play: 'ಕೇಳಿ', pause: 'ವಿರಾಮ' },
  hi: { play: 'सुनें', pause: 'रोकें' },
  te: { play: 'వినండి', pause: 'ఆపండి' },
  ta: { play: 'கேளுங்கள்', pause: 'நிறுத்து' },
  bn: { play: 'শুনুন', pause: 'থামান' },
  mr: { play: 'ऐका', pause: 'थांबवा' },
  gu: { play: 'સાંભળો', pause: 'અટકાવો' },
  ml: { play: 'കേൾക്കുക', pause: 'നിർത്തുക' },
  ur: { play: 'سنیں', pause: 'روکیں' },
};

export default function ChatInterface({
  messages,
  onSendMessage,
  isLoading,
  language,
  onSelectCitationMessage,
}) {
  const [inputText, setInputText]         = useState('');
  const [playingAudioId, setPlayingAudioId] = useState(null);
  const audioRef      = useRef(null);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!inputText.trim() || isLoading) return;
    onSendMessage(inputText.trim(), 'text');
    setInputText('');
  };

  const handleVoiceTranscription = (transcript, detectedLang) => {
    if (transcript) {
      onSendMessage(transcript, 'voice', detectedLang);
    }
  };

  const cleanTextForTTS = (rawText, lang) => {
    if (!rawText) return '';
    let cleaned = rawText
      // Convert markdown links [link text](url) -> link text
      .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
      // Remove all bracketed / parenthetical text and brackets: (...), [...], {...}, （...）
      .replace(/\([^)]*\)/g, '')
      .replace(/\[[^\]]*\]/g, '')
      .replace(/\{[^}]*\}/g, '')
      .replace(/（[^）]*）/g, '')
      // Remove markdown bold/italics/headers
      .replace(/\*\*([^*]+)\*\*/g, '$1')
      .replace(/\*([^*]+)\*/g, '$1')
      .replace(/#{1,6}\s+/g, '');

    // Map "AI" to native script phonetics in Indian languages so neural voices pronounce "AI" clearly
    const aiPhonetics = {
      te: 'ఏఐ',
      kn: 'ಎಐ',
      hi: 'एआई',
      ta: 'ஏஐ',
      bn: 'এআই',
      mr: 'एआय',
      gu: 'એઆઈ',
      ml: 'എഐ',
      ur: 'اے آئی',
    };
    const phoneticAI = aiPhonetics[lang];
    if (phoneticAI) {
      cleaned = cleaned
        .replace(/\bA\.?I\.?[-–—]\s*/gi, `${phoneticAI} `)
        .replace(/\bA\.?I\.?\b/gi, phoneticAI);
    } else {
      cleaned = cleaned.replace(/\bA\.?I\.?[-–—]\s*/gi, 'AI ');
    }

    // Fix spaces before punctuation caused by bracket removal
    cleaned = cleaned.replace(/\s+([,.\?!;:])/g, '$1');
    // Collapse redundant spaces
    cleaned = cleaned.replace(/\s{2,}/g, ' ').trim();

    return cleaned || rawText;
  };

  const playTTS = async (messageId, text, lang) => {
    try {
      if (playingAudioId === messageId && audioRef.current) {
        audioRef.current.pause();
        setPlayingAudioId(null);
        return;
      }

      // Determine the exact language to use based on script and selection
      const scriptLang = detectScript(text);
      const langToUse = scriptLang !== 'en' ? scriptLang : (lang && lang !== 'en' ? lang : language || 'en');

      const textToSpeak = cleanTextForTTS(text, langToUse);
      if (!textToSpeak) return;

      setPlayingAudioId(messageId);

      const blob     = await synthesizeSpeech(textToSpeak, langToUse);
      const audioUrl = URL.createObjectURL(blob);

      if (audioRef.current) {
        audioRef.current.pause();
      }

      const audio      = new Audio(audioUrl);
      audioRef.current = audio;

      audio.onended = () => {
        setPlayingAudioId(null);
      };

      await audio.play();
    } catch (err) {
      console.error('Error playing TTS:', err);
      setPlayingAudioId(null);
    }
  };

  /** Render message text with simple **bold** markdown support */
  const renderText = (text) => {
    if (!text) return null;
    const parts = text.split(/(\*\*[^*]+\*\*)/g);
    return parts.map((part, i) =>
      part.startsWith('**') && part.endsWith('**') ? (
        <strong key={i}>{part.slice(2, -2)}</strong>
      ) : (
        <span key={i}>{part}</span>
      )
    );
  };

  return (
    <div className="chat-container">
      <div className="chat-messages" id="chat-messages-list">
        {messages.map((msg) => (
          <div
            key={msg.id}
            id={`msg-${msg.id}`}
            className={`message-row ${msg.sender}`}
            onClick={() => msg.citations?.length > 0 && onSelectCitationMessage(msg.citations)}
            style={{ cursor: msg.citations?.length > 0 ? 'pointer' : 'default' }}
          >
            <div className={`avatar ${msg.sender}`}>
              {msg.sender === 'user' ? <User size={18} /> : <Bot size={18} />}
            </div>

            <div className="message-bubble">
              <div style={{ whiteSpace: 'pre-wrap', lineHeight: '1.65' }}>
                {renderText(msg.text)}
                {/* Blinking cursor while streaming */}
                {msg.isStreaming && <span className="stream-cursor">|</span>}
              </div>

              {/* Clarification prompt */}
              {msg.needsClarification && msg.clarificationQuestions && msg.clarificationQuestions.length > 0 && (
                <div className="clarification-box">
                  <div className="clarification-title">
                    <HelpCircle size={14} style={{ display: 'inline', marginRight: '4px' }} />
                    {CLARIFICATION_TITLES[msg.language || language] || CLARIFICATION_TITLES.en}
                  </div>
                  <ul className="clarification-list">
                    {msg.clarificationQuestions.map((q, i) => (
                      <li key={i}>{q}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Message metadata */}
              {msg.sender === 'assistant' && !msg.isStreaming && (
                <div className="bubble-meta">
                  <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', flexWrap: 'wrap' }}>
                    {msg.domain && (
                      <span className="domain-tag">
                        {DOMAIN_LABELS[msg.domain]?.[msg.language || language] || msg.domain.replace(/_/g, ' ')}
                      </span>
                    )}
                    {msg.isEmergency && (
                      <span style={{ color: '#f87171', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '3px', fontSize: '0.75rem' }}>
                        <ShieldAlert size={12} /> Emergency Routed
                      </span>
                    )}
                  </div>

                  {msg.text && (
                    <button
                      className="audio-play-btn"
                      onClick={(e) => {
                        e.stopPropagation();
                        const fullText = (msg.clarificationQuestions && msg.clarificationQuestions.length > 0)
                          ? `${msg.text}. ${msg.clarificationQuestions.join('. ')}`
                          : msg.text;
                        playTTS(msg.id, fullText, msg.language);
                      }}
                      title="Listen to response (Neural Voice)"
                    >
                      <Volume2 size={13} />
                      <span>
                        {playingAudioId === msg.id
                          ? (LISTEN_LABELS[msg.language || language]?.pause || 'Pause')
                          : (LISTEN_LABELS[msg.language || language]?.play || 'Listen')}
                      </span>
                    </button>
                  )}
                </div>
              )}
            </div>
          </div>
        ))}

        <div ref={messagesEndRef} />
      </div>

      {/* Input bar */}
      <div className="chat-input-wrapper">
        <VoiceRecorder
          onTranscription={handleVoiceTranscription}
          language={language}
          disabled={isLoading}
        />

        <form id="chat-input-form" className="chat-input-form" onSubmit={handleSubmit}>
          <input
            id="chat-input-field"
            type="text"
            className="chat-input-field"
            placeholder={
              language === 'hi'
                ? 'पारिवारिक कानून के बारे में पूछें (उदा. आपसी सहमति से तलाक के नियम)...'
                : language === 'kn'
                ? 'ಕುಟುಂಬ ಕಾನೂನಿನ ಬಗ್ಗೆ ಪ್ರಶ್ನೆ ಕೇಳಿ (ಉದಾ: ಪರಸ್ಪರ ಒಪ್ಪಿಗೆಯ ವಿಚ್ಛೇದನ)...'
                : language === 'te'
                ? 'కుటుంబ చట్టం గురించి అడగండి (ఉదా: పరస్పర అంగీకార విడాకులు, భరణం)...'
                : language === 'ta'
                ? 'குடும்ப சட்டம் பற்றி கேளுங்கள் (எ.கா: பரஸ்பர விவாகரத்து, பராமரிப்பு)...'
                : language === 'bn'
                ? 'পারিবারিক আইন সম্পর্কে জিজ্ঞাসা করুন (যেমন: পারস্পরিক সম্মতিতে বিবাহবিচ্ছেদ)...'
                : language === 'mr'
                ? 'कौटुंबिक कायद्याबद्दल विचारा (उदा: परस्पर संमतीने घटस्फोट, पोटगी)...'
                : language === 'gu'
                ? 'કૌટુંબિક કાયદા વિશે પૂછો (દા.ત. પરસ્પર સંમતિથી છૂટાછેડા, ભરણપોષણ)...'
                : language === 'ml'
                ? 'കുടുംബ നിയമത്തെക്കുറിച്ച് ചോദിക്കുക (ഉദാ: പരസ്പര സമ്മതത്തോടെയുള്ള വിവാഹമോചനം)...'
                : language === 'ur'
                ? 'خاندانی قانون کے بارے میں پوچھیں (مثلاً باہمی رضامندی سے طلاق، نفقہ)...'
                : 'Ask about divorce, custody, maintenance, domestic violence in your language...'
            }
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            disabled={isLoading}
            autoComplete="off"
          />
          <button
            id="send-btn"
            type="submit"
            className="send-btn"
            disabled={!inputText.trim() || isLoading}
            title="Send query"
          >
            {isLoading ? <Loader2 size={18} className="animate-spin" /> : <Send size={18} />}
          </button>
        </form>
      </div>
    </div>
  );
}
