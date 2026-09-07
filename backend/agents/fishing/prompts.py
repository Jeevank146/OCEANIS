from typing import Any, Dict, List, Optional


FISHING_AGENT_SYSTEM_PROMPT = """
You are the OCEANIS Fishing Intelligence Agent, an expert AI decision-support specialist for marine fishing, coastal oceanography, and maritime safety.

STRICT OPERATIONAL GUIDELINES:
1. Base all narrative explanations ONLY on the provided structured evidence, deterministic suitability scores, and safety findings.
2. Under NO circumstances fabricate or invent oceanographic numbers, wave heights, SST values, or Potential Fishing Zones (PFZs).
3. If official PFZ data is marked UNAVAILABLE, state clearly that official PFZ maps are unavailable and that recommendations derive from satellite SST and chlorophyll observations.
4. SAFETY OVERRIDE: Never override official marine alerts, restricted military exclusion zones, or deterministic safety statuses. If safety is BLOCKED or WARNING, you must explicitly advise against operations.
5. PROHIBITED PHRASES: Never use '100% safe', 'guaranteed safe', 'no risk', or absolute risk-free guarantees. Always qualify recommendations based on available observation data.
6. Provide concise, clear, and actionable advice tailored to fishermen and vessel operators.
""".strip()


def build_fishing_prompt(
    query: Dict[str, Any],
    evidence: List[Dict[str, Any]],
    suitability: Dict[str, Any],
    safety: Dict[str, Any],
    confidence: Dict[str, Any],
) -> str:
    """
    Constructs a controlled prompt incorporating structured telemetry and decision facts
    for future LLM inference.
    """
    evidence_lines = []
    for e in evidence:
        val_str = f"{e.get('value')} {e.get('unit', '')}".strip()
        evidence_lines.append(f"- {e.get('factor')}: {val_str} ({e.get('assessment')}, source: {e.get('source')}, freshness: {e.get('freshness')})")

    reasons_str = "\n".join([f"- {r}" for r in suitability.get("reasons", [])])

    prompt = f"""
Location: Lat {query.get('latitude')}, Lon {query.get('longitude')}
Target Species: {query.get('target_species', 'General Pelagic')}
Vessel Type: {query.get('vessel_type', 'Small Boat')}
User Query: {query.get('question', 'Assess fishing suitability and safety conditions')}

DETERMINISTIC FINDINGS:
- Suitability Status: {suitability.get('status')} (Score: {suitability.get('score')})
- Safety Status: {safety.get('status')}
- Confidence: {confidence.get('level')}

STRUCTURED EVIDENCE:
{chr(10).join(evidence_lines) if evidence_lines else '- No telemetry available'}

DIAGNOSTIC REASONS:
{reasons_str}

Please generate an evidence-grounded, safety-compliant fishing advisory explaining these findings clearly.
""".strip()
    return prompt


def generate_deterministic_narrative(
    suitability_status: str,
    safety_status: str,
    reasons: List[str],
    confidence_level: str,
    target_species: Optional[str] = None,
    vessel_type: Optional[str] = None,
) -> str:
    """
    Deterministic narrative fallback generator when no external LLM API is connected.
    """
    species_str = f" for {target_species}" if target_species else ""
    vessel_str = f" on a {vessel_type.replace('_', ' ')}" if vessel_type else ""

    if suitability_status == "BLOCKED":
        return (
            f"OPERATIONS BLOCKED: Active safety restrictions or critical hazards prevent maritime operations{species_str}{vessel_str}. "
            "Adhere strictly to official port authority regulations and avoid vessel deployment."
        )
    elif suitability_status == "WARNING":
        return (
            f"WARNING ADVISORY: Hazardous marine conditions or active weather advisories detected{species_str}. "
            "Vessels are advised to remain in port or return to safe harbor."
        )
    elif suitability_status == "CAUTION":
        return (
            f"CAUTION ADVISED: Marine conditions require elevated operational care{vessel_str}. "
            "Monitor local forecasts, inspect communication and safety equipment, and observe designated sanctuary boundaries."
        )
    elif suitability_status == "INSUFFICIENT_DATA":
        return (
            "INSUFFICIENT DATA: Real-time oceanographic observations for this coordinate are incomplete or unverified. "
            "Maintain high vigilance as absence of reports does not guarantee safe sea conditions."
        )
    elif suitability_status == "FAVORABLE":
        return (
            f"FAVORABLE CONDITIONS: Sea state, thermal gradients, and wind patterns indicate suitable conditions{species_str}. "
            f"Proceed with standard coastal navigation safety precautions ({confidence_level.capitalize()} confidence)."
        )
    else:
        return (
            f"NEUTRAL CONDITIONS: Environmental metrics reflect seasonal averages{species_str}. "
            "Exercise standard marine operational vigilance."
        )
