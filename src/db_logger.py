import json
from groq import Groq
import httpx
from pydantic import BaseModel, Field
from src import config

groq_client = Groq(api_key=config.GROQ_API_KEY)


class CallRecord(BaseModel):
    patient_name: str = Field(default="Unknown", description="Patient full name")
    patient_email: str = Field(default="", description="Patient email address")
    patient_phone: str = Field(default="", description="Patient phone number")
    insurance_provider: str = Field(default="", description="Insurance provider name")
    chief_complaint: str = Field(default="", description="Primary symptoms or reason for visit")
    appointment_time: str = Field(default="", description="Agreed date and time of appointment")
    booking_status: str = Field(default="Inquiry Only", description="Booked or Inquiry Only")
    call_summary: str = Field(default="", description="Concise call summary")
    call_outcome: str = Field(default="", description="High level outcome of the call")
    raw_transcript: str = Field(default="", description="Full conversation transcript text")


def save_call_record(record: CallRecord) -> None:
    """
    Save structured Pydantic CallRecord directly into Supabase table `call_logs`.
    """
    supabase_url = config.SUPABASE_URL
    supabase_key = config.SUPABASE_KEY

    if not supabase_url or not supabase_key:
        return

    try:
        endpoint = f"{supabase_url.rstrip('/')}/rest/v1/call_logs"
        headers = {
            "apikey": supabase_key,
            "Authorization": f"Bearer {supabase_key}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal",
        }

        httpx.post(
            endpoint,
            headers=headers,
            json=record.model_dump(),
            timeout=10.0,
        )
    except Exception:
        pass


def extract_and_log_call(messages: list[dict]) -> None:
    """
    Extract structured intake fields and summary from the call transcript using Groq
    and save directly to Supabase.
    """
    if not messages:
        return

    transcript_entries = []
    for msg in messages:
        role_name = msg.get("role", "").upper()
        content_text = msg.get("text", "").strip()
        if content_text:
            transcript_entries.append(f"{role_name}: {content_text}")

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

    try:
        completion = groq_client.chat.completions.create(
            model=config.GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": f"Transcript:\n{full_transcript}"},
            ],
            temperature=0.0,
            response_format={"type": "json_object"},
        )

        response_content = completion.choices[0].message.content
        parsed_data = json.loads(response_content)

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

    except Exception:
        pass
