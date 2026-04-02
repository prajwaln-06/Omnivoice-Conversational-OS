# backend/ai/features.py
"""
OmniVoice Feature Pack — Part 1
================================
Feature 1 : Medication Scheduler  (WhatsApp reminders)
Feature 2 : Plain-English Translator (jargon → simple text via Groq)
Feature 3 : Sentiment Analysis     (Groq-powered, 1-10 scale, terminal + WhatsApp)
Feature 4 : Longitudinal Patient Summary (JSON store, per-patient history)

All features are self-contained functions.
Every function has a try/except so a failure in any feature
NEVER crashes the main pipeline.
"""

import os
import json
import re
import threading
import logging
from datetime import datetime
from pathlib import Path

from groq import Groq

logger = logging.getLogger(__name__)

# ─── shared Groq client ────────────────────────────────────────────────────────
def _groq() -> Groq:
    return Groq(api_key=os.getenv("GROQ_API_KEY"))


def _ask_groq(system: str, user: str, temperature: float = 0.2) -> str:
    """Fire a single Groq call and return the text content."""
    resp = _groq().chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ],
        temperature=temperature,
        max_tokens=1024,
    )
    return resp.choices[0].message.content.strip()


# ══════════════════════════════════════════════════════════════════════════════
# FEATURE 1 — MEDICATION SCHEDULER
# ══════════════════════════════════════════════════════════════════════════════

# Maps plain-English frequency words → interval in real hours
_FREQ_MAP = {
    "once daily": 24,      "once a day": 24,
    "twice daily": 12,     "twice a day": 12,   "2x daily": 12,
    "three times": 8,      "3x daily": 8,        "thrice": 8,
    "four times": 6,       "4x daily": 6,
    "every 4 hours": 4,    "every 6 hours": 6,
    "every 8 hours": 8,    "every 12 hours": 12,
    "every 5 hours": 5,    "every 24 hours": 24,
    "as needed": 0,        "prn": 0,              "sos": 0,
}

def _parse_interval_hours(frequency_str: str) -> float:
    """Convert a frequency string to hours. Returns 0 if on-demand."""
    freq_lower = frequency_str.lower()
    for pattern, hours in _FREQ_MAP.items():
        if pattern in freq_lower:
            return hours
    # Fallback: look for "every N hours"
    m = re.search(r"every\s+(\d+)\s+hour", freq_lower)
    if m:
        return int(m.group(1))
    # Default to 8hr if we can't parse
    return 8


def _send_reminder(send_message_fn, to_number: str, med_name: str,
                   dosage: str, frequency: str, reminder_count: list,
                   interval_sec: float, max_reminders: int):
    """Recursive timer callback — fires a WhatsApp reminder then reschedules."""
    if reminder_count[0] >= max_reminders:
        return

    reminder_count[0] += 1
    msg = (
        f"⏰ *OmniVoice Medication Reminder #{reminder_count[0]}*\n\n"
        f"💊 *{med_name}* — {dosage}\n"
        f"📋 Frequency: {frequency}\n\n"
        f"Please take your medication now. 🙏\n"
        f"_(Reminder {reminder_count[0]} of {max_reminders})_"
    )

    try:
        ok, result = send_message_fn(to_number, msg)
        status = "✅ sent" if ok else f"⚠️ {result}"
        print(f"  [MedScheduler] Reminder #{reminder_count[0]} for {med_name}: {status}", flush=True)
    except Exception as e:
        print(f"  [MedScheduler] ❌ WhatsApp error: {e}", flush=True)

    # Reschedule if more reminders remain
    if reminder_count[0] < max_reminders:
        t = threading.Timer(
            interval_sec,
            _send_reminder,
            args=[send_message_fn, to_number, med_name, dosage,
                  frequency, reminder_count, interval_sec, max_reminders]
        )
        t.daemon = True
        t.start()


def schedule_medication_reminders(
    doc_data: dict,
    to_number: str,
    send_message_fn,
    demo_mode: bool = True,
    max_reminders: int = 3,
):
    """
    Feature 1 — Medication Scheduler
    ---------------------------------
    Parses medications from doc_data and schedules WhatsApp reminders.
    demo_mode=True  → converts hours to MINUTES (5 hr → 5 min) for live demo.
    demo_mode=False → real intervals in hours.
    """
    try:
        medications = doc_data.get("medications", [])
        if not medications:
            print("  [MedScheduler] No medications found — skipping scheduler.", flush=True)
            return

        if not send_message_fn or not to_number:
            print("  [MedScheduler] WhatsApp unavailable — skipping.", flush=True)
            return

        print(f"\n  [MedScheduler] Scheduling reminders for {len(medications)} medication(s)...", flush=True)

        for med in medications:
            if not isinstance(med, dict):
                continue

            name      = med.get("name", "Medication")
            dosage    = med.get("dosage", "as prescribed")
            frequency = med.get("frequency", "as needed")
            duration  = med.get("duration", "as directed")

            interval_hours = _parse_interval_hours(frequency)
            if interval_hours == 0:
                print(f"  [MedScheduler] {name} is on-demand (PRN) — no reminders.", flush=True)
                continue

            # DEMO: convert hours → minutes (so 5hr becomes 5min)
            if demo_mode:
                interval_sec = interval_hours * 60          # 1 hr = 1 min in demo
                mode_label   = f"{interval_hours} min (DEMO)"
            else:
                interval_sec = interval_hours * 3600
                mode_label   = f"{interval_hours} hr"

            print(f"  [MedScheduler] 💊 {name} | every {mode_label} | {max_reminders} reminders", flush=True)

            # Send first reminder immediately after a short delay (10 sec)
            reminder_count = [0]
            t = threading.Timer(
                10,
                _send_reminder,
                args=[send_message_fn, to_number, name, dosage,
                      frequency, reminder_count, interval_sec, max_reminders]
            )
            t.daemon = True
            t.start()

        print("  [MedScheduler] ✅ All reminders scheduled in background.\n", flush=True)

    except Exception as e:
        print(f"  [MedScheduler] ❌ Feature failed (pipeline continues): {e}", flush=True)


# ══════════════════════════════════════════════════════════════════════════════
# FEATURE 2 — PLAIN ENGLISH TRANSLATOR
# ══════════════════════════════════════════════════════════════════════════════

def translate_to_plain_english(
    doc_data: dict,
    transcript: str,
    to_number: str,
    send_message_fn,
) -> str:
    """
    Feature 2 — Plain English Translator
    --------------------------------------
    Extracts complex medical/technical terms from the transcript + doc_data
    and returns a simple patient-friendly explanation.
    Sends the result via WhatsApp.
    Returns the plain-text string (for terminal display).
    """
    try:
        # Build a compact representation of the doc for translation
        key_fields = {
            k: v for k, v in doc_data.items()
            if k in ["chief_complaint", "diagnosis", "treatment_plan",
                     "medications", "assessment", "follow_up"]
        }

        system = (
            "You are a patient-friendly medical translator. "
            "Your job is to rewrite complex medical information "
            "in plain English that a 12-year-old can understand. "
            "Use simple words, short sentences, bullet points. "
            "Do NOT use medical jargon. Be warm and reassuring."
        )

        user = f"""
The doctor said the following things during the consultation.
Please explain each part in simple, plain English for the patient.

MEDICAL SUMMARY:
{json.dumps(key_fields, indent=2)}

ORIGINAL CONVERSATION:
{transcript[:1000]}

Format your response like this:
🩺 WHAT THE DOCTOR FOUND: (1-2 simple sentences)
💊 YOUR MEDICINES: (list each medicine simply — what it's for, how to take it)
📋 WHAT YOU NEED TO DO: (simple steps)
📅 NEXT VISIT: (when and why)
⚠️ CALL THE DOCTOR IF: (warning signs in plain language)
"""

        plain_text = _ask_groq(system, user, temperature=0.3)

        print(f"\n\033[95m[PLAIN ENGLISH SUMMARY]\033[0m\n{plain_text}\n", flush=True)

        # Send via WhatsApp
        if send_message_fn and to_number:
            msg = f"📖 *Your Health Summary in Simple Words*\n\n{plain_text}\n\n_Powered by OmniVoice AI_"
            try:
                ok, result = send_message_fn(to_number, msg)
                status = "✅ sent" if ok else f"⚠️ {result}"
                print(f"  [PlainEnglish] WhatsApp: {status}", flush=True)
            except Exception as e:
                print(f"  [PlainEnglish] WhatsApp error: {e}", flush=True)

        return plain_text

    except Exception as e:
        print(f"  [PlainEnglish] ❌ Feature failed (pipeline continues): {e}", flush=True)
        return ""


# ══════════════════════════════════════════════════════════════════════════════
# FEATURE 3 — SENTIMENT ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════

def _render_sentiment_bar(score: int) -> str:
    """Renders a visual 1–10 sentiment bar in terminal."""
    filled   = "█" * score
    empty    = "░" * (10 - score)
    bar      = f"[{filled}{empty}]"

    if score <= 3:
        color = "\033[91m"   # red
        label = "DISTRESSED 🔴"
    elif score <= 5:
        color = "\033[93m"   # yellow
        label = "ANXIOUS 🟡"
    elif score <= 7:
        color = "\033[96m"   # cyan
        label = "NEUTRAL 🔵"
    else:
        color = "\033[92m"   # green
        label = "POSITIVE 🟢"

    reset = "\033[0m"
    return f"{color}{bar} {score}/10 — {label}{reset}"


def analyze_sentiment(
    transcript: str,
    to_number: str,
    send_message_fn,
    alert_threshold: int = 4,
) -> dict:
    """
    Feature 3 — Sentiment Analysis
    --------------------------------
    Analyses the patient's emotional tone in the transcript.
    Scores 1–10. Sends a WhatsApp alert if score <= alert_threshold.
    Returns a dict with score, label, summary.
    """
    try:
        system = (
            "You are a clinical sentiment analyser. "
            "Analyse the patient's tone and emotional state in the conversation. "
            "Return ONLY a JSON object — no explanation, no markdown."
        )

        user = f"""
Analyse the patient's emotional state in this medical conversation.

TRANSCRIPT:
{transcript}

Return ONLY this JSON:
{{
  "score": <integer 1-10 where 1=extremely distressed, 5=neutral, 10=very positive>,
  "label": "<one of: Distressed / Anxious / Concerned / Neutral / Calm / Positive>",
  "dominant_emotion": "<one word>",
  "key_signals": ["signal 1", "signal 2", "signal 3"],
  "summary": "<one sentence clinical summary of patient's emotional state>",
  "needs_immediate_attention": <true if score <= 3, else false>
}}
"""

        raw = _ask_groq(system, user, temperature=0.1)
        raw = raw.replace("```json", "").replace("```", "").strip()
        result = json.loads(raw)

        score = int(result.get("score", 5))
        label = result.get("label", "Neutral")
        summary = result.get("summary", "")
        signals = result.get("key_signals", [])

        # Terminal display
        print(f"\n\033[95m[SENTIMENT ANALYSIS]\033[0m", flush=True)
        print(f"  Scale : {_render_sentiment_bar(score)}", flush=True)
        print(f"  Label : {label}", flush=True)
        print(f"  Summary : {summary}", flush=True)
        if signals:
            print(f"  Key Signals : {', '.join(signals)}", flush=True)

        if score <= alert_threshold:
            print(f"\n  \033[91m⚠️  ALERT: Score {score}/10 — Patient may need immediate attention!\033[0m\n", flush=True)

        # WhatsApp notification
        if send_message_fn and to_number:
            emoji_bar = "🟥" * min(score, 3) + "🟨" * max(0, min(score - 3, 2)) + "🟩" * max(0, score - 5)
            wa_msg = (
                f"🧠 *Patient Sentiment Report*\n\n"
                f"Score: {score}/10  {emoji_bar}\n"
                f"Status: *{label}*\n"
                f"Summary: {summary}\n"
            )
            if score <= alert_threshold:
                wa_msg += "\n⚠️ *ALERT: Patient may need immediate follow-up consultation.*"

            try:
                ok, res = send_message_fn(to_number, wa_msg)
                print(f"  [Sentiment] WhatsApp: {'✅ sent' if ok else res}", flush=True)
            except Exception as e:
                print(f"  [Sentiment] WhatsApp error: {e}", flush=True)

        return result

    except Exception as e:
        print(f"  [Sentiment] ❌ Feature failed (pipeline continues): {e}", flush=True)
        return {"score": 5, "label": "Unknown", "summary": "Analysis unavailable"}


# ══════════════════════════════════════════════════════════════════════════════
# FEATURE 4 — LONGITUDINAL PATIENT SUMMARY
# ══════════════════════════════════════════════════════════════════════════════

PATIENT_STORE_DIR = Path("patient_records")


def _patient_file(patient_id: str) -> Path:
    PATIENT_STORE_DIR.mkdir(exist_ok=True)
    safe_id = re.sub(r"[^\w\-]", "_", patient_id)
    return PATIENT_STORE_DIR / f"{safe_id}.json"


def load_patient_history(patient_id: str) -> dict:
    """Load existing patient record. Returns empty structure if first visit."""
    try:
        pf = _patient_file(patient_id)
        if pf.exists():
            with open(pf, "r") as f:
                return json.load(f)
    except Exception as e:
        print(f"  [Longitudinal] Load error: {e}", flush=True)
    return {"patient_id": patient_id, "visits": []}


def save_patient_visit(patient_id: str, doc_data: dict, session_id: str, sentiment: dict):
    """Append current visit to patient's longitudinal record."""
    try:
        record = load_patient_history(patient_id)

        visit = {
            "session_id": session_id,
            "date": datetime.now().strftime("%d %B %Y %H:%M"),
            "diagnosis": doc_data.get("diagnosis", "N/A"),
            "chief_complaint": doc_data.get("chief_complaint", "N/A"),
            "symptoms": doc_data.get("symptoms", []),
            "medications": doc_data.get("medications", []),
            "follow_up": doc_data.get("follow_up", "N/A"),
            "sentiment_score": sentiment.get("score", 5),
            "sentiment_label": sentiment.get("label", "N/A"),
        }

        record["visits"].append(visit)
        record["last_visit"] = visit["date"]
        record["total_visits"] = len(record["visits"])

        pf = _patient_file(patient_id)
        with open(pf, "w") as f:
            json.dump(record, f, indent=2)

        print(f"  [Longitudinal] ✅ Visit #{record['total_visits']} saved for patient: {patient_id}", flush=True)
        return record

    except Exception as e:
        print(f"  [Longitudinal] Save error: {e}", flush=True)
        return {}


def display_longitudinal_summary(
    patient_id: str,
    to_number: str,
    send_message_fn,
) -> bool:
    """
    Feature 4 — Longitudinal Patient Summary
    ------------------------------------------
    Loads patient history. If returning patient, prints full history
    in terminal and sends WhatsApp summary.
    Returns True if returning patient, False if first visit.
    """
    try:
        record = load_patient_history(patient_id)
        visits = record.get("visits", [])

        if not visits:
            print(f"\n  [Longitudinal] 🆕 New patient: {patient_id} — no prior history.\n", flush=True)
            return False

        print(f"\n\033[95m[LONGITUDINAL PATIENT SUMMARY]\033[0m", flush=True)
        print(f"  Patient ID   : {patient_id}", flush=True)
        print(f"  Total Visits : {len(visits)}", flush=True)
        print(f"  Last Visit   : {record.get('last_visit', 'N/A')}", flush=True)
        print(f"  {'─'*50}", flush=True)

        for i, v in enumerate(visits[-5:], 1):   # show last 5 visits
            print(f"\n  Visit #{i} — {v['date']}", flush=True)
            print(f"    Complaint  : {v['chief_complaint']}", flush=True)
            print(f"    Diagnosis  : {v['diagnosis']}", flush=True)
            symptoms = ", ".join(v['symptoms']) if v['symptoms'] else "N/A"
            print(f"    Symptoms   : {symptoms}", flush=True)
            print(f"    Sentiment  : {v['sentiment_label']} ({v['sentiment_score']}/10)", flush=True)
            if v['medications']:
                for m in v['medications']:
                    if isinstance(m, dict):
                        print(f"    💊 {m.get('name','')} {m.get('dosage','')} — {m.get('frequency','')}", flush=True)

        # WhatsApp summary (last 3 visits)
        if send_message_fn and to_number and len(visits) > 1:
            lines = [f"📋 *Returning Patient — Visit History*\nPatient: {patient_id}\nTotal Visits: {len(visits)}\n"]
            for i, v in enumerate(visits[-3:], 1):
                lines.append(
                    f"*Visit {i} ({v['date']})*\n"
                    f"• Diagnosis: {v['diagnosis']}\n"
                    f"• Mood: {v['sentiment_label']} ({v['sentiment_score']}/10)\n"
                )
            wa_msg = "\n".join(lines) + "\n_OmniVoice Longitudinal Summary_"
            try:
                ok, res = send_message_fn(to_number, wa_msg)
                print(f"\n  [Longitudinal] WhatsApp: {'✅ sent' if ok else res}", flush=True)
            except Exception as e:
                print(f"  [Longitudinal] WhatsApp error: {e}", flush=True)

        return True

    except Exception as e:
        print(f"  [Longitudinal] ❌ Feature failed (pipeline continues): {e}", flush=True)
        return False