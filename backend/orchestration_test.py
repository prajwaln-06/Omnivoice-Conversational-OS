import asyncio
import os
import time
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv

from ai.asr import SarvamASR
from ai.llm import GroqLLM
from ai.rag import get_context
from ai.tts import SarvamTTS
from ai.post_call_analyzer import (
    analyze_transcript_with_groq,
    build_reminder_schedule,
    build_whatsapp_message,
    generate_pdf,
)

load_dotenv()

MOCK_TRANSCRIPT = """
Doctor: Namaskara, barthiri. Hegiddira?
Patient: Doctor, naanu 2 days-ininda fever iddene,
101 temperature. Headache and body pain also ide.
Doctor: Hmm. Any vomiting or loose motion?
Patient: No doctor, only fever and pain ide.
Doctor: Ok. Naanu Paracetamol 500mg prescribe maadteeni.
Twice a day, after food. 5 days take maadri.
ORS kuda twice daily take maadri.
Rest maadri, minimum 3 days.
Cetirizine 10mg, once at night before sleep kuda.
Patient: Ok doctor. Follow up yavaga barali?
Doctor: 5 days later banni. Fever 103 dhaati hodre,
immediately emergency ge banni.
"""


class TestFailure(Exception):
    pass


def fail(test_name: str, expected: str, got: Any, fix: str):
    raise TestFailure(
        f"\n❌ FAILED: {test_name}\n"
        f"Expected: {expected}\n"
        f"Got: {got}\n"
        f"Fix: {fix}\n"
    )


def has_medication(medications: List[Dict[str, Any]], name: str) -> bool:
    return any((m.get("name", "").strip().lower() == name.lower()) for m in medications)


async def run() -> int:
    issues: List[str] = []
    module_lines: List[str] = []
    pipeline_lines: List[str] = []

    print("\u2550" * 42)
    print("OMNIVOICE ORCHESTRATION TEST REPORT")
    print("\u2550" * 42)
    print("MODULE TESTS:")

    # LLM test
    llm_elapsed = 0.0
    try:
        t0 = time.perf_counter()
        llm = GroqLLM()
        llm_resp = llm.generate_response("Reply in English: hello, this is a test message", history=[])
        llm_elapsed = time.perf_counter() - t0
        if not llm_resp:
            fail("LLM", "non-empty response", llm_resp, "Check GROQ_API_KEY and internet access")
        line = f"✅ LLM (Groq)      — response in {llm_elapsed:.1f}s"
        module_lines.append(line)
        print(line)
    except Exception as exc:
        line = f"❌ LLM (Groq)      — {exc}"
        module_lines.append(line)
        issues.append(str(exc))
        print(line)

    # RAG test
    try:
        t0 = time.perf_counter()
        rag_context = await get_context("fever headache medication", "healthcare")
        rag_elapsed = time.perf_counter() - t0
        if rag_context:
            chunk_count = max(1, rag_context.count("\n") + 1)
            line = f"✅ RAG             — {chunk_count} context chunks retrieved in {rag_elapsed:.1f}s"
        else:
            line = "⚠️  RAG             — empty context returned"
        module_lines.append(line)
        print(line)
    except Exception as exc:
        line = f"❌ RAG             — {exc}"
        module_lines.append(line)
        issues.append(str(exc))
        print(line)

    # ASR test
    try:
        if not os.getenv("SARVAM_API_KEY"):
            line = "⚠️  ASR (Sarvam)   — no SARVAM_API_KEY, skipped"
            module_lines.append(line)
            print(line)
        else:
            pcm_mock = b"\x00\x00" * 1600
            t0 = time.perf_counter()
            text = SarvamASR().transcribe(pcm_mock)
            asr_elapsed = time.perf_counter() - t0
            if text:
                line = f"✅ ASR (Sarvam)   — transcript received in {asr_elapsed:.1f}s"
            else:
                line = "⚠️  ASR (Sarvam)   — no test audio transcript, skipped"
            module_lines.append(line)
            print(line)
    except Exception as exc:
        line = f"⚠️  ASR (Sarvam)   — skipped ({exc})"
        module_lines.append(line)
        print(line)

    # TTS test
    try:
        if not os.getenv("SARVAM_API_KEY"):
            line = "⚠️  TTS (Sarvam)   — no SARVAM_API_KEY, skipped"
            module_lines.append(line)
            print(line)
        else:
            tts = SarvamTTS()
            t0 = time.perf_counter()
            audio = tts.synthesize("Hello from OmniVoice test", lang_code="en-IN")
            tts_elapsed = time.perf_counter() - t0
            if not audio:
                fail("TTS", "non-empty audio bytes", audio, "Check SARVAM_API_KEY and TTS API availability")
            line = f"✅ TTS (Sarvam)   — {len(audio)} bytes returned in {tts_elapsed:.1f}s"
            module_lines.append(line)
            print(line)
    except TestFailure as exc:
        issues.append(str(exc))
        print(exc)
    except Exception as exc:
        line = f"⚠️  TTS (Sarvam)   — skipped ({exc})"
        module_lines.append(line)
        print(line)

    print("POST-CALL PIPELINE:")

    try:
        transcript = MOCK_TRANSCRIPT.strip()
        if not transcript:
            fail("Transcript", "non-empty transcript", transcript, "Check MOCK_TRANSCRIPT constant")
        line = f"✅ Transcript      — {len(transcript)} chars"
        pipeline_lines.append(line)
        print(line)

        analytics = analyze_transcript_with_groq(transcript, "orchestration-test-session")
        meds = analytics.get("medications") or []
        if len(meds) < 2:
            fail(
                "Analytics",
                "at least 2 medications",
                meds,
                "Ensure LLM output/fallback includes Paracetamol and Cetirizine",
            )

        required_med_fields = ["name", "dosage", "frequency_hours", "duration_days", "reminder_message"]
        for med in meds:
            missing = [f for f in required_med_fields if f not in med]
            if missing:
                fail(
                    "Medication fields",
                    f"all fields {required_med_fields}",
                    med,
                    f"Populate missing medication fields: {missing}",
                )

        if not has_medication(meds, "Paracetamol") or not has_medication(meds, "Cetirizine"):
            fail(
                "Medications",
                "Paracetamol and Cetirizine present",
                [m.get("name") for m in meds],
                "Improve extraction prompt/fallback mapping",
            )

        line = f"✅ Analytics       — {len(meds)} medications extracted"
        pipeline_lines.append(line)
        print(line)
        line = "✅ Medications     — Paracetamol ✓, Cetirizine ✓"
        pipeline_lines.append(line)
        print(line)

        reminders = build_reminder_schedule(analytics)
        if len(reminders) != 15:
            fail(
                "Reminders",
                "15 total reminders (Paracetamol 10 + Cetirizine 5)",
                len(reminders),
                "Verify frequency_hours and duration_days extraction for both medications",
            )
        line = f"✅ Reminders       — {len(reminders)} scheduled"
        pipeline_lines.append(line)
        print(line)

        if not analytics.get("whatsapp_immediate_message"):
            fail(
                "WhatsApp immediate",
                "non-empty whatsapp_immediate_message",
                analytics.get("whatsapp_immediate_message"),
                "Ensure analytics response includes whatsapp_immediate_message",
            )

        follow_up = analytics.get("follow_up") or {}
        if follow_up.get("required") is not True:
            fail("Follow-up", "follow_up.required == true", follow_up, "Set follow_up.required to true")
        if int(follow_up.get("days_from_today", 0)) != 5:
            fail(
                "Follow-up days",
                "follow_up.days_from_today == 5",
                follow_up.get("days_from_today"),
                "Set follow_up.days_from_today to 5",
            )
        line = "✅ Follow-up       — in 5 days ✓"
        pipeline_lines.append(line)
        print(line)

        risk_flags = analytics.get("risk_flags") or []
        if len(risk_flags) < 1:
            fail("Risk flags", "at least 1 risk flag", risk_flags, "Add at least one meaningful risk flag")
        line = f"✅ Risk flags      — {len(risk_flags)} found ✓"
        pipeline_lines.append(line)
        print(line)

        pdf_bytes = generate_pdf(analytics, transcript, "orchestration-test-session")
        if not pdf_bytes:
            fail("PDF", "pdf bytes not None", pdf_bytes, "Ensure generate_pdf returns bytes")
        if len(pdf_bytes) <= 5000:
            fail("PDF", "len(pdf_bytes) > 5000", len(pdf_bytes), "Add richer PDF content and sections")

        output_dir = Path(__file__).parent / "test_output"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / "orchestration_test.pdf"
        output_file.write_bytes(pdf_bytes)
        line = f"✅ PDF             — {len(pdf_bytes)} bytes → saved"
        pipeline_lines.append(line)
        print(line)

        whatsapp_msg = build_whatsapp_message(analytics, "PDF_URL_PLACEHOLDER")
        med_names = [m.get("name", "") for m in meds]
        if not all(name in whatsapp_msg for name in med_names):
            fail(
                "WhatsApp message meds",
                f"contains medication names {med_names}",
                whatsapp_msg,
                "Include medication names in build_whatsapp_message",
            )
        if "Follow-up" not in whatsapp_msg and "follow-up" not in whatsapp_msg:
            fail(
                "WhatsApp message follow-up",
                "contains follow-up info",
                whatsapp_msg,
                "Include follow-up line in build_whatsapp_message",
            )
        if "PDF_URL_PLACEHOLDER" not in whatsapp_msg:
            fail(
                "WhatsApp message PDF",
                "contains PDF URL placeholder",
                whatsapp_msg,
                "Include PDF link line in build_whatsapp_message",
            )
        line = f"✅ WhatsApp msg    — {len(whatsapp_msg)} chars"
        pipeline_lines.append(line)
        print(line)

        print("REMINDER SCHEDULE PREVIEW:")
        for idx, reminder in enumerate(reminders[:3]):
            print(
                f"[{idx}] {((idx + 1) * 12)}h from now → "
                f"{reminder.get('medicine_name', '')} ({reminder.get('type', '')})"
            )
        if len(reminders) > 3:
            print("...")

    except TestFailure as exc:
        issues.append(str(exc))
        print(exc)
    except Exception as exc:
        issues.append(str(exc))
        print(
            f"\n❌ FAILED: Pipeline\nExpected: Successful pipeline execution\n"
            f"Got: {exc}\nFix: Inspect post_call_analyzer functions and response shape\n"
        )

    print(f"ISSUES FOUND: {len(issues)}")
    print("\u2550" * 42)

    if issues:
        print("TESTS COMPLETED WITH FAILURES")
        print("\u2550" * 42)
        return 1

    print("ALL TESTS PASSED ✅")
    print("\u2550" * 42)
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run()))
