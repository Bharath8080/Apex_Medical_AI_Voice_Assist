import json
import httpx
from groq import Groq
from pydantic import BaseModel
from src import config

groq_client = Groq(api_key=config.GROQ_API_KEY)


class CallRecord(BaseModel):
    patient_name: str = "Unknown"
    patient_email: str = ""
    patient_phone: str = ""
    insurance_provider: str = ""
    chief_complaint: str = ""
    appointment_time: str = ""
    booking_status: str = "Inquiry Only"
    call_summary: str = ""
    call_outcome: str = ""
    raw_transcript: str = ""


def save_call_record(record: CallRecord) -> None:
    if not config.SUPABASE_URL or not config.SUPABASE_KEY:
        return

    endpoint = f"{config.SUPABASE_URL.rstrip('/')}/rest/v1/call_logs"
    headers = {
        "apikey": config.SUPABASE_KEY,
        "Authorization": f"Bearer {config.SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }

    httpx.post(endpoint, headers=headers, json=record.model_dump(), timeout=10.0)


def extract_and_log_call(messages: list[dict]) -> None:
    if not messages:
        return

    transcript_entries = []
    for msg in messages:
        role = msg.get("role", "").upper()
        text = msg.get("text", "").strip()
        if text:
            transcript_entries.append(f"{role}: {text}")

    if not transcript_entries:
        return

    full_transcript = "\n".join(transcript_entries)

    system_instruction = (
        "You are an expert medical transcriptionist for Apex Care Hospital.\n"
        "Extract structured JSON matching these keys:\n"
        "- patient_name (string)\n"
        "- patient_email (string)\n"
        "- patient_phone (string)\n"
        "- insurance_provider (string)\n"
        "- chief_complaint (string)\n"
        "- appointment_time (string)\n"
        "- booking_status (Booked | Inquiry Only)\n"
        "- call_summary (concise 2-3 sentences)\n"
        "- call_outcome (Appointment Booked | General Inquiry | Insurance Inquiry | Emergency)\n"
        "Output ONLY valid JSON."
    )

    completion = groq_client.chat.completions.create(
        model=config.GROQ_MODEL,
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": f"Transcript:\n{full_transcript}"},
        ],
        temperature=0.0,
        response_format={"type": "json_object"},
    )

    parsed_data = json.loads(completion.choices[0].message.content)

    call_record = CallRecord(
        patient_name=parsed_data.get("patient_name", "Unknown"),
        patient_email=parsed_data.get("patient_email", ""),
        patient_phone=parsed_data.get("patient_phone", ""),
        insurance_provider=parsed_data.get("insurance_provider", ""),
        chief_complaint=parsed_data.get("chief_complaint", ""),
        appointment_time=parsed_data.get("appointment_time", ""),
        booking_status=parsed_data.get("booking_status", "Inquiry Only"),
        call_summary=parsed_data.get("call_summary", ""),
        call_outcome=parsed_data.get("call_outcome", ""),
        raw_transcript=full_transcript,
    )

    save_call_record(call_record)
