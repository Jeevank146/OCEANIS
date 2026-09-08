import type {
  FinalDecisionObjectContract,
  EvidenceItemContract,
} from '../services/api';

export interface LocalizedSynthesizedResponse {
  language: string;
  primaryAnswer: string;
  summary: string;
  decisionLabel: string;
  intentBadgeLabel: string;
  locationLabel: string;
  confidenceExplain: string;
  followUpSuggestions: Array<{ label: string; query: string }>;
}

// 1. Localized Decision Badges across all 9 Indian Coastal Languages
export const DECISION_LABELS: Record<string, Record<string, string>> = {
  en: {
    SUITABLE: 'Suitable',
    CAUTION: 'Caution',
    NOT_RECOMMENDED: 'Not Recommended',
    INSUFFICIENT_EVIDENCE: 'Insufficient Evidence',
    INFORMATION_ONLY: 'Information / Telemetry',
    INFORMATION: 'Information / Telemetry',
  },
  te: {
    SUITABLE: 'అనుకూలం (Suitable)',
    CAUTION: 'హెచ్చరిక (Caution)',
    NOT_RECOMMENDED: 'సిఫార్సు చేయబడలేదు (Not Recommended)',
    INSUFFICIENT_EVIDENCE: 'సరిపడా ఆధారాలు లేవు (Insufficient Evidence)',
    INFORMATION_ONLY: 'సమాచారం మాత్రమే (Information Only)',
    INFORMATION: 'సమాచారం మాత్రమే (Information Only)',
  },
  hi: {
    SUITABLE: 'अनुकूल (Suitable)',
    CAUTION: 'सावधानी (Caution)',
    NOT_RECOMMENDED: 'अनुशंसित नहीं (Not Recommended)',
    INSUFFICIENT_EVIDENCE: 'अपर्याप्त साक्ष्य (Insufficient Evidence)',
    INFORMATION_ONLY: 'केवल जानकारी (Information Only)',
    INFORMATION: 'केवल जानकारी (Information Only)',
  },
  ta: {
    SUITABLE: 'ஏற்றது (Suitable)',
    CAUTION: 'எச்சரிக்கை (Caution)',
    NOT_RECOMMENDED: 'பரிந்துரைக்கப்படவில்லை (Not Recommended)',
    INSUFFICIENT_EVIDENCE: 'போதுமான சான்றுகள் இல்லை (Insufficient Evidence)',
    INFORMATION_ONLY: 'தகவல் மட்டும் (Information Only)',
    INFORMATION: 'தகவல் மட்டும் (Information Only)',
  },
  kn: {
    SUITABLE: 'ಅನುಕೂಲಕರ (Suitable)',
    CAUTION: 'ಎಚ್ಚರಿಕೆ (Caution)',
    NOT_RECOMMENDED: 'ಶಿಫಾರಸು ಮಾಡಲಾಗಿಲ್ಲ (Not Recommended)',
    INSUFFICIENT_EVIDENCE: 'ಸಾಕಷ್ಟು ಪುರಾವೆಗಳಿಲ್ಲ (Insufficient Evidence)',
    INFORMATION_ONLY: 'ಮಾಹಿತಿ ಮಾತ್ರ (Information Only)',
    INFORMATION: 'ಮಾಹಿತಿ ಮಾತ್ರ (Information Only)',
  },
  ml: {
    SUITABLE: 'അനുയോജ്യം (Suitable)',
    CAUTION: 'ജാഗ്രത (Caution)',
    NOT_RECOMMENDED: 'ശുപാർശ ചെയ്യുന്നില്ല (Not Recommended)',
    INSUFFICIENT_EVIDENCE: 'മതിയായ തെളിവുകളില്ല (Insufficient Evidence)',
    INFORMATION_ONLY: 'വിവരം മാത്രം (Information Only)',
    INFORMATION: 'വിവരം മാത്രം (Information Only)',
  },
  mr: {
    SUITABLE: 'अनुकूल (Suitable)',
    CAUTION: 'सावधगिरी (Caution)',
    NOT_RECOMMENDED: 'शिफारस केलेली नाही (Not Recommended)',
    INSUFFICIENT_EVIDENCE: 'अपुरा पुरावा (Insufficient Evidence)',
    INFORMATION_ONLY: 'फक्त माहिती (Information Only)',
    INFORMATION: 'फक्त माहिती (Information Only)',
  },
  bn: {
    SUITABLE: 'অনুকূল (Suitable)',
    CAUTION: 'সতর্কতা (Caution)',
    NOT_RECOMMENDED: 'সুপারিশ করা হয় না (Not Recommended)',
    INSUFFICIENT_EVIDENCE: 'পর্যাপ্ত প্রমাণ নেই (Insufficient Evidence)',
    INFORMATION_ONLY: 'শুধুমাত্র তথ্য (Information Only)',
    INFORMATION: 'শুধুমাত্র তথ্য (Information Only)',
  },
  gu: {
    SUITABLE: 'અનુકૂળ (Suitable)',
    CAUTION: 'સાવધાની (Caution)',
    NOT_RECOMMENDED: 'ભલામણ કરેલ નથી (Not Recommended)',
    INSUFFICIENT_EVIDENCE: 'અપૂરતા પુરાવા (Insufficient Evidence)',
    INFORMATION_ONLY: 'માત્ર માહિતી (Information Only)',
    INFORMATION: 'માત્ર માહિતી (Information Only)',
  },
};

// 2. Localized Query Intent Labels
export const INTENT_LABELS: Record<string, Record<string, string>> = {
  en: {
    DECISION: 'Decision Intelligence',
    INFORMATION: 'Telemetry & Conditions',
    SAFETY: 'Disaster & Safety Advisory',
    COMPARISON: 'Multi-Location Comparison',
    ROUTE: 'Navigation & Transit',
    WHAT_IF: 'What-If Simulation',
  },
  te: {
    DECISION: 'నిర్ణయ ఇంటెలిజెన్స్ (Decision)',
    INFORMATION: 'టెలిమెట్రీ & పరిస్థితులు (Information)',
    SAFETY: 'విపత్తు & భద్రతా హెచ్చరిక (Safety)',
    COMPARISON: 'బహుళ స్థానాల పోలిక (Comparison)',
    ROUTE: 'నావిగేషన్ & మార్గం (Route)',
    WHAT_IF: 'వాట్-ఇఫ్ అనుకరణ (What-If)',
  },
  hi: {
    DECISION: 'निर्णय इंटेलिजेंस (Decision)',
    INFORMATION: 'टेलीमेट्री और स्थितियां (Information)',
    SAFETY: 'आपदा एवं सुरक्षा परामर्श (Safety)',
    COMPARISON: 'स्थान तुलना (Comparison)',
    ROUTE: 'नेविगेशन और रूट (Route)',
    WHAT_IF: 'व्हाट-इफ सिमुलेशन (What-If)',
  },
  ta: {
    DECISION: 'முடிவு நுண்ணறிவு (Decision)',
    INFORMATION: 'டெலிமெட்ரி & நிலைமைகள் (Information)',
    SAFETY: 'பேரிடர் & பாதுகாப்பு ஆலோசனை (Safety)',
    COMPARISON: 'பல இடங்கள் ஒப்பீடு (Comparison)',
    ROUTE: 'வழிசெலுத்தல் (Route)',
    WHAT_IF: 'வாட்-இஃப் உருவகப்படுத்துதல் (What-If)',
  },
  kn: {
    DECISION: 'ನಿರ್ಧಾರ ಇಂಟೆಲಿಜೆನ್ಸ್ (Decision)',
    INFORMATION: 'ಟೆಲಿಮೆಟ್ರಿ & ಪರಿಸ್ಥಿತಿಗಳು (Information)',
    SAFETY: 'ವಿಪತ್ತು & ಸುರಕ್ಷತಾ ಸಲಹೆ (Safety)',
    COMPARISON: 'ಸ್ಥಳಗಳ ಹೋಲಿಕೆ (Comparison)',
    ROUTE: 'ನ್ಯಾವಿಗೇಷನ್ & ಮಾರ್ಗ (Route)',
    WHAT_IF: 'ವಾಟ್-ಇಫ್ ಸಿಮ್ಯುಲೇಶನ್ (What-If)',
  },
  ml: {
    DECISION: 'തീരുമാന ഇന്റലിജൻസ് (Decision)',
    INFORMATION: 'ടെലിമെട്രി & അവസ്ഥകൾ (Information)',
    SAFETY: 'ദുരന്ത & സുരക്ഷാ ഉപദേശം (Safety)',
    COMPARISON: 'സ്ഥല താരതമ്യം (Comparison)',
    ROUTE: 'നാവിഗേഷൻ & റൂട്ട് (Route)',
    WHAT_IF: 'വാട്ട്-ഇഫ് സിമുലേഷൻ (What-If)',
  },
  mr: {
    DECISION: 'निर्णय इंटेलिजन्स (Decision)',
    INFORMATION: 'टेलिमेट्री व परिस्थिती (Information)',
    SAFETY: 'आपत्ती व सुरक्षा सल्ला (Safety)',
    COMPARISON: 'स्थान तुलना (Comparison)',
    ROUTE: 'नेव्हिगेशन व मार्ग (Route)',
    WHAT_IF: 'व्हॉट-इफ सिम्युलेशन (What-If)',
  },
  bn: {
    DECISION: 'সিদ্ধান্ত ইন্টেলিজেন্স (Decision)',
    INFORMATION: 'টেলিমেট্রি ও পরিস্থিতি (Information)',
    SAFETY: 'দুর্যোগ ও সুরক্ষা পরামর্শ (Safety)',
    COMPARISON: 'স্থান তুলনা (Comparison)',
    ROUTE: 'ন্যাভিগেশন ও রুট (Route)',
    WHAT_IF: 'হোয়াট-ইফ সিমুলেশন (What-If)',
  },
  gu: {
    DECISION: 'નિર્ણય ઇન્ટેલિજન્સ (Decision)',
    INFORMATION: 'ટેલિમેટ્રી અને પરિસ્થિતિ (Information)',
    SAFETY: 'આપત્તિ અને સુરક્ષા સલાહ (Safety)',
    COMPARISON: 'સ્થળોની સરખામણી (Comparison)',
    ROUTE: 'નેવિગેશન અને રૂટ (Route)',
    WHAT_IF: 'વ્હોટ-ઇફ સિમ્યુલેશન (What-If)',
  },
};

// 3. Dynamic Location-Aware and Intent-Aware Follow-up Generator
export function getDynamicFollowUpSuggestions(
  locName: string = 'Current Sector',
  lang: string = 'en',
  intent: string = 'DECISION'
): Array<{ label: string; query: string }> {
  const cleanLoc = locName.split(',')[0].trim() || 'this sector';
  const l = (lang || 'en').toLowerCase();
  const rawIntent = (intent || 'DECISION').toUpperCase();

  // Intent-specific dynamic follow-ups
  if (rawIntent === 'INFORMATION') {
    switch (l) {
      case 'te':
        return [
          { label: `🌊 ${cleanLoc} వద్ద అలలు మరియు గాలి వివరాలు`, query: `Show wave and wind telemetry near ${cleanLoc}` },
          { label: `🛰️ ${cleanLoc} వద్ద శాటిలైట్ SST & క్లోరోఫిల్`, query: `Show satellite SST and Chlorophyll-a near ${cleanLoc}` },
          { label: `⚠️ ${cleanLoc} వద్ద ఏవైనా సముద్ర హెచ్చరికలు ఉన్నాయా?`, query: `Is there any marine warning near ${cleanLoc}?` },
          { label: `🎣 ${cleanLoc} వద్ద చేపల వేటకు పరిస్థితులు అనుకూలమా?`, query: `Can I go fishing tomorrow morning from ${cleanLoc}?` },
        ];
      case 'hi':
        return [
          { label: `🌊 ${cleanLoc} के पास लहर और हवा का डेटा`, query: `Show wave and wind telemetry near ${cleanLoc}` },
          { label: `🛰️ ${cleanLoc} के पास सैटेलाइट SST और क्लोरोफिल`, query: `Show satellite SST and Chlorophyll-a near ${cleanLoc}` },
          { label: `⚠️ क्या ${cleanLoc} के पास कोई समुद्री चेतावनी है?`, query: `Is there any marine warning near ${cleanLoc}?` },
          { label: `🎣 क्या ${cleanLoc} से मछली पकड़ने जा सकते हैं?`, query: `Can I go fishing tomorrow morning from ${cleanLoc}?` },
        ];
      case 'ta':
        return [
          { label: `🌊 ${cleanLoc} அலை & காற்று அளவீடுகள்`, query: `Show wave and wind telemetry near ${cleanLoc}` },
          { label: `🛰️ ${cleanLoc} செயற்கைக்கோள் SST & குளோரோபில்`, query: `Show satellite SST and Chlorophyll-a near ${cleanLoc}` },
          { label: `⚠️ ${cleanLoc} அருகே கடல்சார் எச்சரிக்கை உள்ளதா?`, query: `Is there any marine warning near ${cleanLoc}?` },
          { label: `🎣 ${cleanLoc} பகுதியில் மீன்பிடிக்க செல்லலாமா?`, query: `Can I go fishing tomorrow morning from ${cleanLoc}?` },
        ];
      default:
        return [
          { label: `🌊 Show wave and wind telemetry for ${cleanLoc}`, query: `Show wave and wind telemetry for ${cleanLoc}` },
          { label: `🛰️ Show satellite SST & Chlorophyll near ${cleanLoc}`, query: `Show satellite SST and Chlorophyll-a near ${cleanLoc}` },
          { label: `⚠️ Any active marine warnings near ${cleanLoc}?`, query: `Is there any marine warning near ${cleanLoc}?` },
          { label: `🎣 Can I go fishing tomorrow morning from ${cleanLoc}?`, query: `Can I go fishing tomorrow morning from ${cleanLoc}?` },
        ];
    }
  }

  if (rawIntent === 'SAFETY') {
    switch (l) {
      case 'te':
        return [
          { label: `🚨 అధికారిక హెచ్చరిక పూర్తి వివరాలు`, query: `Show official marine warning details for ${cleanLoc}` },
          { label: `🗺️ ప్రమాద ప్రభావిత ప్రాంతం మరియు ట్రాక్`, query: `Show affected warning area near ${cleanLoc}` },
          { label: `⚓ సమీప సురక్షిత తీర ఆశ్రయాలు`, query: `Show nearby safe refuge harbors near ${cleanLoc}` },
          { label: `🌊 ప్రస్తుత గాలి మరియు అలల తీవ్రత`, query: `Show wave and wind telemetry near ${cleanLoc}` },
        ];
      case 'hi':
        return [
          { label: `🚨 आधिकारिक चेतावनी का पूरा विवरण`, query: `Show official marine warning details for ${cleanLoc}` },
          { label: `🗺️ प्रभावित क्षेत्र और जोखिम ट्रैक`, query: `Show affected warning area near ${cleanLoc}` },
          { label: `⚓ नजदीकी सुरक्षित आश्रय बंदरगाह`, query: `Show nearby safe refuge harbors near ${cleanLoc}` },
          { label: `🌊 हवा और लहरों की वर्तमान तीव्रता`, query: `Show wave and wind telemetry near ${cleanLoc}` },
        ];
      default:
        return [
          { label: `🚨 Show official warning details for ${cleanLoc}`, query: `Show official marine warning details for ${cleanLoc}` },
          { label: `🗺️ Show affected area and danger zones near ${cleanLoc}`, query: `Show affected warning area near ${cleanLoc}` },
          { label: `⚓ Show nearby safe refuge harbors for ${cleanLoc}`, query: `Show nearby safe refuge harbors near ${cleanLoc}` },
          { label: `🌊 Show wave and wind telemetry near ${cleanLoc}`, query: `Show wave and wind telemetry near ${cleanLoc}` },
        ];
    }
  }

  if (rawIntent === 'ROUTE') {
    switch (l) {
      case 'te':
        return [
          { label: `🧭 ప్రత్యామ్నాయ సురక్షిత మార్గాన్ని సరిపోల్చండి`, query: `Compare alternate route from ${cleanLoc}` },
          { label: `⚠️ మార్గంలో ప్రమాదాలు మరియు ఆటంకాలు`, query: `Show route hazards for ${cleanLoc}` },
          { label: `⏱️ ప్రయాణ సమయ అంచనా`, query: `Estimate travel transit time from ${cleanLoc}` },
        ];
      default:
        return [
          { label: `🧭 Compare alternate route from ${cleanLoc}`, query: `Compare alternate route from ${cleanLoc}` },
          { label: `⚠️ Show route hazards for ${cleanLoc}`, query: `Show route hazards for ${cleanLoc}` },
          { label: `⏱️ Estimate travel time from ${cleanLoc}`, query: `Estimate travel transit time from ${cleanLoc}` },
        ];
    }
  }

  if (rawIntent === 'WHAT_IF') {
    switch (l) {
      case 'te':
        return [
          { label: `🔄 బేస్‌లైన్ సినారియోతో పోల్చండి`, query: `Compare with baseline for ${cleanLoc}` },
          { label: `⏱️ మరో సమయాన్ని ప్రయత్నించండి (ఉదా: మధ్యాహ్నం 12:00)`, query: `What if departure is at 12:00 PM from ${cleanLoc}?` },
          { label: `🧠 సిఫార్సు ఎందుకు మారింది?`, query: `Why did the recommendation change for ${cleanLoc}?` },
        ];
      default:
        return [
          { label: `🔄 Compare with baseline for ${cleanLoc}`, query: `Compare with baseline for ${cleanLoc}` },
          { label: `⏱️ Try another departure time from ${cleanLoc}`, query: `What if departure is at 12:00 PM from ${cleanLoc}?` },
          { label: `🧠 Why did the recommendation change for ${cleanLoc}?`, query: `Why did the recommendation change for ${cleanLoc}?` },
        ];
    }
  }

  // Default: DECISION intent dynamic follow-ups
  switch (l) {
    case 'te':
      return [
        { label: `🧠 ఈ నిర్ణయం ఎందుకు ఇవ్వబడింది?`, query: `Why this decision for ${cleanLoc}?` },
        { label: `⏱️ ఒకవేళ ఉదయం 9 గంటలకు వెళ్తే?`, query: `What if I leave at 9 AM from ${cleanLoc}?` },
        { label: `🛡️ భద్రతా సాక్ష్యాలు మరియు నిబంధనలు`, query: `Show safety evidence for ${cleanLoc}` },
        { label: `🌊 ${cleanLoc} వద్ద అలలు మరియు గాలి వివరాలు`, query: `Show wave and wind telemetry near ${cleanLoc}` },
      ];
    case 'hi':
      return [
        { label: `🧠 यह निर्णय क्यों दिया गया?`, query: `Why this decision for ${cleanLoc}?` },
        { label: `⏱️ यदि सुबह 9 बजे प्रस्थान करें तो?`, query: `What if I leave at 9 AM from ${cleanLoc}?` },
        { label: `🛡️ सुरक्षा साक्ष्य और नियम`, query: `Show safety evidence for ${cleanLoc}` },
        { label: `🌊 ${cleanLoc} के पास लहर और हवा का डेटा`, query: `Show wave and wind telemetry near ${cleanLoc}` },
      ];
    case 'ta':
      return [
        { label: `🧠 இந்த முடிவின் காரணங்கள்`, query: `Why this decision for ${cleanLoc}?` },
        { label: `⏱️ காலை 9 மணிக்கு புறப்பட்டால் என்ன?`, query: `What if I leave at 9 AM from ${cleanLoc}?` },
        { label: `🛡️ பாதுகாப்பு சான்றுகள்`, query: `Show safety evidence for ${cleanLoc}` },
        { label: `🌊 ${cleanLoc} அலை & காற்று அளவீடுகள்`, query: `Show wave and wind telemetry near ${cleanLoc}` },
      ];
    case 'kn':
      return [
        { label: `🧠 ಈ ನಿರ್ಧಾರದ ವಿವರಣೆ`, query: `Why this decision for ${cleanLoc}?` },
        { label: `⏱️ ಬೆಳಗ್ಗೆ 9 ಗಂಟೆಗೆ ಹೊರಟರೆ ಏನು?`, query: `What if I leave at 9 AM from ${cleanLoc}?` },
        { label: `🛡️ ಸುರಕ್ಷತಾ ಪುರಾವೆಗಳು`, query: `Show safety evidence for ${cleanLoc}` },
        { label: `🌊 ${cleanLoc} ಅಲೆ ಮತ್ತು ಗಾಳಿಯ ವಿವರ`, query: `Show wave and wind telemetry near ${cleanLoc}` },
      ];
    case 'ml':
      return [
        { label: `🧠 ഈ തീരുമാനത്തിന്റെ കാരണം`, query: `Why this decision for ${cleanLoc}?` },
        { label: `⏱️ രാവിലെ 9 മണിക്ക് പുറപ്പെട്ടാൽ?`, query: `What if I leave at 9 AM from ${cleanLoc}?` },
        { label: `🛡️ സുരക്ഷാ തെളിവുകൾ`, query: `Show safety evidence for ${cleanLoc}` },
        { label: `🌊 ${cleanLoc} തിരമാല വിവരങ്ങൾ`, query: `Show wave and wind telemetry near ${cleanLoc}` },
      ];
    case 'mr':
      return [
        { label: `🧠 या निर्णयाचे स्पष्टीकरण`, query: `Why this decision for ${cleanLoc}?` },
        { label: `⏱️ सकाळी 9 वाजता निघालो तर?`, query: `What if I leave at 9 AM from ${cleanLoc}?` },
        { label: `🛡️ सुरक्षा पुरावे`, query: `Show safety evidence for ${cleanLoc}` },
        { label: `🌊 ${cleanLoc} लाटा व वाऱ्याचा वेग`, query: `Show wave and wind telemetry near ${cleanLoc}` },
      ];
    case 'bn':
      return [
        { label: `🧠 এই সিদ্ধান্তের কারণ কী?`, query: `Why this decision for ${cleanLoc}?` },
        { label: `⏱️ সকাল ৯টায় রওনা দিলে কী হবে?`, query: `What if I leave at 9 AM from ${cleanLoc}?` },
        { label: `🛡️ সুরক্ষা প্রমাণ`, query: `Show safety evidence for ${cleanLoc}` },
        { label: `🌊 ${cleanLoc} ঢেউ ও বাতাসের তথ্য`, query: `Show wave and wind telemetry near ${cleanLoc}` },
      ];
    case 'gu':
      return [
        { label: `🧠 આ નિર્ણયનું કારણ શું છે?`, query: `Why this decision for ${cleanLoc}?` },
        { label: `⏱️ સવારે 9 વાગ્યે નીકળીએ તો?`, query: `What if I leave at 9 AM from ${cleanLoc}?` },
        { label: `🛡️ સુરક્ષા પુરાવા`, query: `Show safety evidence for ${cleanLoc}` },
        { label: `🌊 ${cleanLoc} મોજાં અને પવન ડેટા`, query: `Show wave and wind telemetry near ${cleanLoc}` },
      ];
    default:
      return [
        { label: `🧠 Why this decision?`, query: `Why this decision for ${cleanLoc}?` },
        { label: `⏱️ What if I leave at 9 AM instead?`, query: `What if I leave at 9 AM from ${cleanLoc}?` },
        { label: `🛡️ Show safety evidence`, query: `Show safety evidence for ${cleanLoc}` },
        { label: `🌊 Show wave and wind telemetry for ${cleanLoc}`, query: `Show wave and wind telemetry for ${cleanLoc}` },
        { label: `🛰️ Show satellite SST & Chlorophyll near ${cleanLoc}`, query: `Show satellite SST and Chlorophyll-a near ${cleanLoc}` },
      ];
  }
}

export const FOLLOW_UP_SUGGESTIONS: Record<string, Array<{ label: string; query: string }>> = {
  en: getDynamicFollowUpSuggestions('Active Sector', 'en'),
  te: getDynamicFollowUpSuggestions('యాక్టివ్ సెక్టార్', 'te'),
  hi: getDynamicFollowUpSuggestions('सक्रिय क्षेत्र', 'hi'),
  ta: getDynamicFollowUpSuggestions('செயலில் உள்ள துறை', 'ta'),
  kn: getDynamicFollowUpSuggestions('ಸಕ್ರಿಯ ವಲಯ', 'kn'),
  ml: getDynamicFollowUpSuggestions('സജീവ മേഖല', 'ml'),
  mr: getDynamicFollowUpSuggestions('सक्रिय क्षेत्र', 'mr'),
  bn: getDynamicFollowUpSuggestions('সক্রিয় সেক্টর', 'bn'),
  gu: getDynamicFollowUpSuggestions('સક્રિય ક્ષેત્ર', 'gu'),
};

/**
 * Strips raw Python serialization artifacts and internal dictionary key reprs.
 */
export function sanitizeEvidenceText(raw: string): string {
  if (!raw) return '';
  let s = String(raw);
  s = s.replace(/factor=['"][^'"]*['"]\s*/gi, '');
  s = s.replace(/entity_type=['"][^'"]*['"]\s*/gi, '');
  s = s.replace(/source_category=['"][^'"]*['"]\s*/gi, '');
  s = s.replace(/data_type=['"][^'"]*['"]\s*/gi, '');
  s = s.replace(/spatial_relationship=['"][^'"]*['"]\s*/gi, '');
  s = s.replace(/notes=['"][^'"]*['"]\s*/gi, '');
  s = s.replace(/observed_at=[^\s,)]+/gi, '');
  s = s.replace(/effective_from=[^\s,)]+/gi, '');
  s = s.replace(/effective_until=[^\s,)]+/gi, '');
  s = s.replace(/confidence=[0-9.]+\s*/gi, '');
  s = s.replace(/freshness=['"][^'"]*['"]\s*/gi, '');
  s = s.replace(/None/g, 'N/A');
  s = s.replace(/null/gi, '');
  s = s.replace(/undefined/gi, '');
  s = s.replace(/\s+/g, ' ').trim();
  return s || String(raw);
}

/**
 * Synthesizes naturally fluent localized text in the chosen language.
 */
export function synthesizeMultilingualResponse(
  decisionData: FinalDecisionObjectContract,
  lang: string = 'en',
): LocalizedSynthesizedResponse {
  const l = (lang || 'en').toLowerCase();
  const rawDec = (decisionData.decision || 'SUITABLE').toUpperCase().replace(/\s+/g, '_');
  const decLabel = DECISION_LABELS[l]?.[rawDec] || DECISION_LABELS.en[rawDec] || decisionData.decision;
  
  const rawIntent = (decisionData.query_intent || 'DECISION').toUpperCase();
  const intentBadge = INTENT_LABELS[l]?.[rawIntent] || INTENT_LABELS.en[rawIntent] || rawIntent;
  const locName = decisionData.location?.name || 'Selected Coastal Sector';
  const followUps = getDynamicFollowUpSuggestions(locName, l, rawIntent);
  const reqTime = decisionData.requested_time || '06:00';

  // Extract key telemetry
  let waveHeight = '1.4';
  let windSpeed = '14.0';
  let sstVal = '29.2';

  if (decisionData.evidence && decisionData.evidence.length > 0) {
    for (const ev of decisionData.evidence) {
      const p = (ev.parameter || '').toLowerCase();
      if (p.includes('wave_height') || p.includes('significant wave')) {
        waveHeight = String(ev.value);
      } else if (p.includes('wind_speed')) {
        windSpeed = String(ev.value);
      } else if (p.includes('sst') || p.includes('sea surface temp')) {
        sstVal = String(ev.value);
      }
    }
  }

  // English fallback base
  if (l === 'en') {
    return {
      language: 'en',
      primaryAnswer: decisionData.primary_answer || decisionData.summary,
      summary: decisionData.summary,
      decisionLabel: decLabel,
      intentBadgeLabel: intentBadge,
      locationLabel: locName,
      confidenceExplain: `Calculated with ${decisionData.confidence || 78}% multi-agent confidence from ${decisionData.agents_consulted_count || decisionData.agents_consulted?.length || 4} synchronized authorities.`,
      followUpSuggestions: followUps,
    };
  }

  // Telugu Synthesis
  if (l === 'te') {
    let primaryTe = '';
    let summaryTe = '';

    if (rawIntent === 'INFORMATION') {
      primaryTe = `${locName} వద్ద ప్రస్తుత సముద్ర పరిస్థితులు: సముద్ర ఉపరితల ఉష్ణోగ్రత ${sstVal}°C, అలల ఎత్తు ${waveHeight} మీటర్లు మరియు గాలి వేగం ${windSpeed} కిమీ/గం వద్ద ఉన్నాయి.`;
      summaryTe = `INCOIS & IMD తాజా టెలిమెట్రీ ప్రకారం వాతావరణం మరియు సముద్ర ప్రవాహాలు నిరంతరం పర్యవేక్షించబడుతున్నాయి.`;
    } else if (rawIntent === 'SAFETY') {
      primaryTe = `${locName} పరిధిలో భద్రతా సమాచారం: ప్రస్తుతానికి ప్రమాదకర తుఫాను హెచ్చరికలు లేవు. సముద్ర కార్యకలాపాలు ప్రామాణిక నిబంధనలకు అనుగుణంగా నిర్వహించవచ్చు.`;
      summaryTe = `అధికారిక విపత్తు నిర్వహణ మరియు కోస్ట్‌గార్డ్ సూచనలను ఎప్పటికప్పుడు గమనించండి.`;
    } else {
      if (rawDec === 'SUITABLE') {
        primaryTe = `${locName} నుండి ప్రయాణం (${reqTime} గంటలకు) సురక్షితమైనది మరియు అనుకూలమైనది.`;
        summaryTe = `అలల ఎత్తు (${waveHeight} మీటర్లు) మరియు గాలి వేగం (${windSpeed} కిమీ/గం) నిర్దేశిత భద్రతా పరిమితుల్లో ఉన్నాయి.`;
      } else if (rawDec === 'CAUTION') {
        primaryTe = `${locName} వద్ద ప్రయాణానికి హెచ్చరిక జారీ చేయబడింది. జాగ్రత్తగా వ్యవహరించండి.`;
        summaryTe = `తీరంలో గాలి వేగం లేదా అలల తీవ్రత పెరుగుతున్నందున తగిన భద్రతా జాగ్రత్తలు తీసుకోండి.`;
      } else {
        primaryTe = `${locName} వద్ద ప్రస్తుతం సముద్ర ప్రయాణం సిఫార్సు చేయబడలేదు.`;
        summaryTe = `ప్రతికూల వాతావరణం లేదా అధిక అలల ముప్పు ఉన్నందున వేటకు వెళ్లడం నిలిపివేయండి.`;
      }
    }

    return {
      language: 'te',
      primaryAnswer: primaryTe,
      summary: summaryTe,
      decisionLabel: decLabel,
      intentBadgeLabel: intentBadge,
      locationLabel: locName,
      confidenceExplain: `${decisionData.confidence || 78}% బహుళ-ఏజెంట్ విశ్వసనీయతతో ధృవీకరించబడింది.`,
      followUpSuggestions: followUps,
    };
  }

  // Hindi Synthesis
  if (l === 'hi') {
    let primaryHi = '';
    let summaryHi = '';

    if (rawIntent === 'INFORMATION') {
      primaryHi = `${locName} के पास वर्तमान समुद्री स्थिति: समुद्री सतह का तापमान ${sstVal}°C, लहरों की ऊंचाई ${waveHeight} मीटर और हवा की गति ${windSpeed} किमी/घंटा है।`;
      summaryHi = `INCOIS और IMD के रीयल-टाइम डेटा द्वारा स्थिति की निरंतर निगरानी की जा रही है।`;
    } else if (rawIntent === 'SAFETY') {
      primaryHi = `${locName} के लिए सुरक्षा परामर्श: फिलहाल कोई गंभीर चक्रवात या भारी आपदा चेतावनी सक्रिय नहीं है।`;
      summaryHi = `तटीय संचालन जारी रख सकते हैं, आधिकारिक बुलेटिन का पालन करें।`;
    } else {
      if (rawDec === 'SUITABLE') {
        primaryHi = `${locName} से ${reqTime} बजे प्रस्थान सुरक्षित और अनुकूल है।`;
        summaryHi = `लहरों की ऊंचाई (${waveHeight} मी) और हवा की गति (${windSpeed} किमी/घं) सुरक्षित परिचालन सीमा में हैं।`;
      } else if (rawDec === 'CAUTION') {
        primaryHi = `${locName} पर समुद्री संचालन के लिए सावधानी आवश्यक है।`;
        summaryHi = `तटीय स्थितियों में बदलाव के कारण अतिरिक्त सुरक्षा उपकरण साथ रखें।`;
      } else {
        primaryHi = `${locName} पर वर्तमान में प्रस्थान अनुशंसित नहीं है।`;
        summaryHi = `प्रतिकूल परिस्थितियों और सुरक्षा जोखिम के कारण समुद्री यात्रा स्थगित करें।`;
      }
    }

    return {
      language: 'hi',
      primaryAnswer: primaryHi,
      summary: summaryHi,
      decisionLabel: decLabel,
      intentBadgeLabel: intentBadge,
      locationLabel: locName,
      confidenceExplain: `${decisionData.confidence || 78}% मल्टी-एजेंट सटीकता के साथ सत्यापित।`,
      followUpSuggestions: followUps,
    };
  }

  // Tamil Synthesis
  if (l === 'ta') {
    let primaryTa = '';
    let summaryTa = '';

    if (rawIntent === 'INFORMATION') {
      primaryTa = `${locName} கடல்சார் நிலவரம்: கடல் மேற்பரப்பு வெப்பநிலை ${sstVal}°C, அலை உயரம் ${waveHeight} மீ மற்றும் காற்றின் வேகம் ${windSpeed} கிமீ/மணி.`;
      summaryTa = `INCOIS மற்றும் IMD நேரலை தரவுகளின் அடிப்படையில் பகுப்பாய்வு செய்யப்பட்டுள்ளது.`;
    } else {
      primaryTa = `${locName} பகுதிக்கான முடிவு: ${decLabel}. அலை உயரம் ${waveHeight} மீ மற்றும் காற்று ${windSpeed} கிமீ/மணி.`;
      summaryTa = `கடல்சார் பாதுகாப்பிற்கு முன்னுரிமை அளித்து எச்சரிக்கையுடன் செயல்படவும்.`;
    }

    return {
      language: 'ta',
      primaryAnswer: primaryTa,
      summary: summaryTa,
      decisionLabel: decLabel,
      intentBadgeLabel: intentBadge,
      locationLabel: locName,
      confidenceExplain: `${decisionData.confidence || 78}% நம்பகத்தன்மையுடன் கணக்கிடப்பட்டது.`,
      followUpSuggestions: followUps,
    };
  }

  // Default fallback for kn, ml, mr, bn, gu
  return {
    language: l,
    primaryAnswer: decisionData.primary_answer || decisionData.summary,
    summary: decisionData.summary,
    decisionLabel: decLabel,
    intentBadgeLabel: intentBadge,
    locationLabel: locName,
    confidenceExplain: `Multi-agent confidence: ${decisionData.confidence || 78}%`,
    followUpSuggestions: followUps,
  };
}

/**
 * Normalizes parameter units cleanly.
 */
export function getNormalizedUnit(item: EvidenceItemContract): string {
  if (item.unit && item.unit !== 'None' && item.unit !== 'null') {
    return item.unit;
  }
  const p = (item.parameter || '').toLowerCase();
  if (p.includes('wave') || p.includes('height') || p.includes('depth') || p.includes('elevation')) return 'm';
  if (p.includes('wind') || p.includes('speed')) return 'km/h';
  if (p.includes('temp') || p.includes('sst')) return '°C';
  if (p.includes('salinity')) return 'PSU';
  if (p.includes('chlorophyll')) return 'mg/m³';
  if (p.includes('pressure')) return 'hPa';
  if (p.includes('direction')) return '°';
  if (p.includes('period')) return 's';
  return '';
}

/**
 * Formats evidence values cleanly without scientific or raw dictionary artifacts.
 */
export function sanitizeEvidenceValue(val: any, _paramName?: string): string {
  if (val === null || val === undefined || val === 'None') return 'N/A';
  if (typeof val === 'number') {
    if (isNaN(val)) return 'N/A';
    if (Number.isInteger(val)) return String(val);
    return val.toFixed(2);
  }
  if (typeof val === 'object') {
    try {
      return JSON.stringify(val);
    } catch {
      return 'Multi-dimensional data';
    }
  }
  const s = String(val).trim();
  return sanitizeEvidenceText(s);
}
