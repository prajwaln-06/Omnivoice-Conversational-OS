import requests
import logging
logger = logging.getLogger(__name__)

# ── RxNorm — NIH Drug Standardization (no API key needed) ──────────────────

def rxnorm_validate_drug(drug_name: str) -> dict:
    """Validate drug name and get RxCUI code from NIH RxNorm."""
    try:
        url = f"https://rxnav.nlm.nih.gov/REST/rxcui.json?name={drug_name}&search=1"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        rxcui = data.get("idGroup", {}).get("rxnormId", [None])[0]
        if rxcui:
            return {"valid": True, "drug": drug_name, "rxcui": rxcui}
        return {"valid": False, "drug": drug_name, "rxcui": None}
    except Exception as e:
        logger.error(f"[RxNorm] {e}")
        return {"valid": False, "drug": drug_name, "error": str(e)}


def rxnorm_get_interactions(rxcui_list: list) -> list:
    """Check drug-drug interactions for a list of RxCUI codes."""
    if not rxcui_list:
        return []
    try:
        ids = "+".join(rxcui_list)
        url = f"https://rxnav.nlm.nih.gov/REST/interaction/list.json?rxcuis={ids}"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        pairs = data.get("fullInteractionTypeGroup", [])
        interactions = []
        for group in pairs:
            for itype in group.get("fullInteractionType", []):
                for pair in itype.get("interactionPair", []):
                    interactions.append({
                        "severity": pair.get("severity", "unknown"),
                        "description": pair.get("description", ""),
                    })
        return interactions
    except Exception as e:
        logger.error(f"[RxNorm Interactions] {e}")
        return []


def enrich_medications_with_rxnorm(medications: list) -> dict:
    """
    Takes medications list from extracted doc_data,
    validates each drug and checks interactions.
    Returns enriched result with rxcui codes + interaction warnings.
    """
    validated = []
    rxcui_list = []

    for med in medications:
        name = med.get("name", "")
        result = rxnorm_validate_drug(name)
        validated.append({**med, **result})
        if result.get("rxcui"):
            rxcui_list.append(result["rxcui"])

    interactions = rxnorm_get_interactions(rxcui_list)

    return {
        "medications_validated": validated,
        "drug_interactions": interactions,
        "interaction_count": len(interactions),
        "has_severe_interactions": any(
            i.get("severity", "").lower() == "high" for i in interactions
        ),
    }


# ── ICD-10 Code Inference (Clinical Tables API — no key needed) ─────────────

def infer_icd10_codes(symptoms_or_diagnosis: str) -> list:
    """
    Infers ICD-10 codes from symptom text using NLM Clinical Tables API.
    Free, no API key required.
    """
    try:
        url = "https://clinicaltables.nlm.nih.gov/api/icd10cm/v3/search"
        params = {"sf": "code,name", "terms": symptoms_or_diagnosis, "maxList": 5}
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        codes = []
        if len(data) >= 4 and data[3]:
            for item in data[3]:
                codes.append({"code": item[0], "description": item[1]})
        return codes
    except Exception as e:
        logger.error(f"[ICD10] {e}")
        return []


def enrich_with_icd10(doc_data: dict) -> dict:
    """
    Takes extracted doc_data, infers ICD-10 codes from symptoms field.
    Returns icd10_codes list to add to doc_data.
    """
    symptoms = doc_data.get("symptoms", [])
    if isinstance(symptoms, list):
        query = " ".join(symptoms)
    else:
        query = str(symptoms)

    diagnosis = doc_data.get("diagnosis", "")
    search_term = diagnosis if diagnosis else query

    return infer_icd10_codes(search_term)