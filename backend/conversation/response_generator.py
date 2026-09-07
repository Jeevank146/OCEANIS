import re
from typing import Any, Dict, List, Optional

from conversation.llm_client import BaseLLMClient, LLMClientFactory
from conversation.prompts import RESPONSE_GENERATOR_SYSTEM_PROMPT
from conversation.schemas import ParsedQuery
from orchestrator.schemas import OrchestrationResponse


class ConversationalResponseGenerator:
    """
    Multilingual conversational response generator.
    Translates structured backend orchestration decisions into natural, localized speech
    while rigorously upholding deterministic safety decisions, evidence grounding,
    and prohibition of absolute safety claims.
    """

    PROHIBITED_CLAIMS_PATTERN = re.compile(
        r"(100%\s*safe|guaranteed\s*safe|completely\s*safe|risk[-\s]*free|zero\s*risk|absolute\s*safety)",
        re.IGNORECASE,
    )

    def __init__(self, llm_client: Optional[BaseLLMClient] = None):
        self.llm_client = llm_client or LLMClientFactory.get_client()

    def generate_response(
        self,
        orchestration: OrchestrationResponse,
        parsed_query: ParsedQuery,
    ) -> str:
        """
        Generates localized natural-language response based strictly on orchestration evidence.
        """
        lang = parsed_query.language
        mode = parsed_query.input_mode

        # If an external LLM is configured (non-deterministic fallback), we can use it with safety prompts
        if self.llm_client.provider_name != "deterministic_rule_engine":
            try:
                evidence_summary = [
                    f"- {ev.factor}: {ev.value} {ev.unit or ''} (Source: {ev.source}, Severity: {ev.severity})"
                    for ev in orchestration.evidence[:8]
                ]
                prompt = (
                    f"User Message: {parsed_query.original_query}\n"
                    f"Target Language: {lang}, Script Mode: {mode}\n"
                    f"Authoritative Decision: {orchestration.decision}\n"
                    f"Risk Level: {orchestration.risk_level}\n"
                    f"Confidence: {orchestration.confidence}\n"
                    f"Freshness: {orchestration.freshness}\n"
                    f"Active Warnings: {', '.join(orchestration.warnings) if orchestration.warnings else 'None'}\n"
                    f"Evidence Items:\n" + "\n".join(evidence_summary) + "\n\n"
                    f"Reasoning Summary from Backend:\n{orchestration.reasoning_summary}\n\n"
                    f"Generate a clear, natural conversational response for the user in the requested language and mode."
                )
                raw_response = self.llm_client.generate_text(
                    prompt=prompt,
                    system_prompt=RESPONSE_GENERATOR_SYSTEM_PROMPT,
                    temperature=0.2,
                )
                if raw_response and len(raw_response.strip()) > 10:
                    return self._sanitize_response(raw_response, orchestration.decision)
            except Exception:
                pass

        # Deterministic multilingual response generator
        response_text = self._deterministic_generate(
            orchestration=orchestration,
            parsed_query=parsed_query,
            lang=lang,
            mode=mode,
        )
        return self._sanitize_response(response_text, orchestration.decision)

    def _deterministic_generate(
        self,
        orchestration: OrchestrationResponse,
        parsed_query: ParsedQuery,
        lang: str,
        mode: str,
    ) -> str:
        """
        Rule-based multilingual response synthesis based strictly on verified evidence.
        """
        decision = orchestration.decision
        risk = orchestration.risk_level
        conf = orchestration.confidence
        fresh = orchestration.freshness
        warnings = orchestration.warnings
        loc_name = parsed_query.location.name if parsed_query.location else "the requested sector"

        # Extract primary metrics from evidence
        wave_height = None
        wind_speed = None
        chl_density = None
        active_alerts_count = 0

        for ev in orchestration.evidence:
            if ev.factor == "wave_height" and ev.value is not None:
                wave_height = ev.value
            elif ev.factor == "wind_speed" and ev.value is not None:
                wind_speed = ev.value
            elif ev.factor == "chlorophyll_density" and ev.value is not None:
                chl_density = ev.value
            elif ev.factor == "active_alerts" and isinstance(ev.value, list):
                active_alerts_count = len(ev.value)

        metrics_parts: List[str] = []
        if wave_height is not None:
            metrics_parts.append(f"wave height {wave_height} m")
        if wind_speed is not None:
            metrics_parts.append(f"sustained winds {wind_speed} km/h")
        if chl_density is not None:
            metrics_parts.append(f"chlorophyll-a {chl_density} mg/m³")

        metrics_str = f" ({', '.join(metrics_parts)})" if metrics_parts else ""

        # 1. Telugu Transliterated
        if lang == "te" and mode == "transliterated":
            if decision == "BLOCKED":
                return (
                    f"DECISION: BLOCKED. {loc_name} daggara operations ippudu strictly BLOCKED cheyabadindi. "
                    f"Risk Level: CRITICAL. Active hazard zones, severe storm threat leda naval exclusion barriers valla "
                    f"samudram loki vellatam pramadakaram. Dayanunchi aagandi."
                )
            elif decision == "WARNING":
                warn_str = f" Active warnings: {'; '.join(warnings)}." if warnings else ""
                return (
                    f"DECISION: WARNING. {loc_name} daggara high operational risk undi.{metrics_str}{warn_str} "
                    f"Adverse sea state leda gale winds valla non-essential fishing trips postpone cheyatam manchidi."
                )
            elif decision == "CAUTION":
                return (
                    f"DECISION: CAUTION. {loc_name} daggara marine conditions permissible under heightened vigilance.{metrics_str} "
                    f"Moderate wave/wind dynamics unna kani, safe navigation rules follow avvandi."
                )
            elif decision == "INSUFFICIENT_DATA":
                return (
                    f"DECISION: INSUFFICIENT DATA. {loc_name} daggara fresh environmental telemetry ledu. "
                    f"Fresh satellite leda in-situ coverage lekunda clearance ivvalemu. Jagratha vahinchandi."
                )
            elif decision == "FAVORABLE":
                return (
                    f"DECISION: FAVORABLE. {loc_name} daggara fishing conditions anukulanga unnayi.{metrics_str} "
                    f"0 active warnings detect ayyayi. Normal operational parameters lo vetaki vellavachu."
                )
            else:
                return (
                    f"DECISION: CLEAR. {loc_name} daggara normal maritime parameters unnayani confirm cheyabadindi.{metrics_str} "
                    f"Confidence: {conf}, Data Freshness: {fresh}."
                )

        # 2. Telugu Unicode
        elif lang == "te" and mode == "standard":
            if decision == "BLOCKED":
                return (
                    f"నిర్ణయం: BLOCKED. {loc_name} వద్ద కార్యకలాపాలు అత్యంత ప్రమాదకరం మరియు నిషేధించబడ్డాయి. "
                    f"రిస్క్ స్థాయి: CRITICAL. క్రిటికల్ హజార్డ్ లేదా నేవల్ ఎక్స్‌క్లూజన్ జోన్ల కారణంగా సముద్రంలోకి వెళ్లడం నిషిద్ధం."
                )
            elif decision == "WARNING":
                return (
                    f"నిర్ణయం: WARNING. {loc_name} వద్ద తీవ్ర వాతావరణ హెచ్చరికలు గుర్తించబడ్డాయి.{metrics_str} "
                    f"రిస్క్ స్థాయి: HIGH. వేటకు వెళ్లడం ప్రస్తుతానికి వాయిదా వేయడం మంచిది."
                )
            elif decision == "CAUTION":
                return (
                    f"నిర్ణయం: CAUTION. {loc_name} వద్ద సాధారణం కంటే ఎక్కువ గాలి/అలల తీవ్రత ఉంది.{metrics_str} "
                    f"జాగ్రత్తగా ప్రయాణించండి."
                )
            elif decision == "INSUFFICIENT_DATA":
                return (
                    f"నిర్ణయం: INSUFFICIENT DATA. {loc_name} వద్ద తాజా పర్యావరణ సమాచారం అందుబాటులో లేదు. "
                    f"క్లియరెన్స్ ఇవ్వలేము."
                )
            else:
                return (
                    f"నిర్ణయం: FAVORABLE / CLEAR. {loc_name} వద్ద సముద్ర పరిస్థితులు అనుకూలంగా ఉన్నాయి.{metrics_str} "
                    f"యాక్టివ్ హెచ్చరికలు లేవు. సాధారణ నిబంధనలు పాటించండి."
                )

        # 3. Hindi
        elif lang == "hi":
            if decision == "BLOCKED":
                return (
                    f"निर्णय: BLOCKED (अवरुद्ध). {loc_name} के पास परिचालन पूरी तरह से वर्जित है। "
                    f"जोखिम स्तर: CRITICAL. गंभीर खतरे या नौसेना प्रतिबंध के कारण समुद्र में जाना मना है।"
                )
            elif decision == "WARNING":
                return (
                    f"निर्णय: WARNING (चेतावनी). {loc_name} के पास उच्च परिचालन जोखिम पाया गया है।{metrics_str} "
                    f"मौसम खराब होने के कारण गैर-जरूरी यात्राएं स्थगित करें।"
                )
            elif decision == "CAUTION":
                return (
                    f"निर्णय: CAUTION (सावधानी). {loc_name} के पास समुद्र में मध्यम लहरें और हवाएं हैं।{metrics_str} "
                    f"सतर्कता के साथ ही आगे बढ़ें।"
                )
            elif decision == "INSUFFICIENT_DATA":
                return (
                    f"निर्णय: INSUFFICIENT DATA. {loc_name} के लिए पर्याप्त डेटा उपलब्ध नहीं है।"
                )
            else:
                return (
                    f"निर्णय: CLEAR / FAVORABLE. {loc_name} के पास समुद्री परिस्थितियां अनुकूल हैं।{metrics_str} "
                    f"कोई सक्रिय चेतावनी नहीं है।"
                )

        # 4. Standard English
        else:
            if decision == "BLOCKED":
                return (
                    f"DECISION: BLOCKED (Risk Level: CRITICAL). Operations at {loc_name} are strictly barred due to critical safety barriers. "
                    f"Active prohibitive hazards, extreme cyclone tracks, or military exclusion zones mandate complete postponement."
                )
            elif decision == "WARNING":
                warn_str = f" Active warnings: {'; '.join(warnings)}." if warnings else ""
                return (
                    f"DECISION: WARNING (Risk Level: HIGH). High operational risk detected near {loc_name}.{metrics_str}{warn_str} "
                    f"Adverse marine conditions warrant postponement of non-essential voyages."
                )
            elif decision == "CAUTION":
                return (
                    f"DECISION: CAUTION (Risk Level: MODERATE). Marine conditions near {loc_name} are permissible under heightened vigilance.{metrics_str} "
                    f"Exercise care and monitor local VHF forecasts."
                )
            elif decision == "INSUFFICIENT_DATA":
                return (
                    f"DECISION: INSUFFICIENT_DATA (Confidence: INSUFFICIENT_DATA). Real-time environmental telemetry is missing or unavailable for {loc_name}. "
                    f"In accordance with OCEANIS safety rules, operational clearance cannot be verified without fresh coverage."
                )
            elif decision == "FAVORABLE":
                return (
                    f"DECISION: FAVORABLE (Risk Level: LOW). Verified environmental and marine dynamics near {loc_name} support fishing operations.{metrics_str} "
                    f"0 active marine alerts or exclusion barriers detected."
                )
            else:
                return (
                    f"DECISION: CLEAR (Risk Level: LOW). Conditions near {loc_name} currently indicate normal maritime operational parameters.{metrics_str} "
                    f"Confidence: {conf}, Data Freshness: {fresh}."
                )

    def _sanitize_response(self, text: str, decision: str) -> str:
        """
        Sanitizes generated response against prohibited absolute safety claims.
        """
        if not text:
            return text
        sanitized = self.PROHIBITED_CLAIMS_PATTERN.sub("normal operational parameters", text)
        return sanitized
