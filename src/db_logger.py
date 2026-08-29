import json
import os
import sqlite3
from groq import Groq
import httpx
from pydantic import BaseModel, Field
from src import config

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "patient_records.db")
groq_client = Groq(api_key=config.GROQ_API_KEY)


class CallRecord(BaseModel):
    patient_name: str = Field(default="Unknown", description="Patient full name")
    patient_email: str = Field(default="", description="Patient email address")
    patient_phone: str = Field(default="", description="Patient phone number")
    insurance_provider: str = Field(default="", description="Insurance provider name")
    chief_complaint: str = Field(default="", description="Primary symptoms or reason for visit")
    appointment_time: str = Field(default="", description="Agreed date and time of appointment")
    booking_status: str = Field(default="Inquiry Only", description="Booked, Inquiry Only, or Looked Up")
    call_summary: str = Field(default="", description="2 to 3 sentence concise call summary")
    call_outcome: str = Field(default="", description="High level outcome of the call")
    raw_transcript: str = Field(default="", description="Full conversation transcript text")


def init_database() -> None:
    """
    Initialize SQLite database table for storing patient records and call summaries.
    """
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS call_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            patient_name TEXT,
            patient_email TEXT,
            patient_phone TEXT,
            insurance_provider TEXT,
            chief_complaint TEXT,
            appointment_time TEXT,
            booking_status TEXT,
            call_summary TEXT,
            call_outcome TEXT,
            raw_transcript TEXT
        )
        """
    )

    connection.commit()
    connection.close()


init_database()


def save_call_record(record: CallRecord) -> None:
    """
    Save structured Pydantic CallRecord into SQLite and optionally sync to Supabase.
    """
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    insert_query = """
        INSERT INTO call_logs (
            patient_name,
            patient_email,
            patient_phone,
            insurance_provider,
            chief_complaint,
            appointment_time,
            booking_status,
            call_summary,
            call_outcome,
            raw_transcript
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    values = (
        record.patient_name,
        record.patient_email,
        record.patient_phone,
        record.insurance_provider,
        record.chief_complaint,
        record.appointment_time,
        record.booking_status,
        record.call_summary,
        record.call_outcome,
        record.raw_transcript,
    )

    cursor.execute(insert_query, values)
    connection.commit()
    connection.close()

    # Optional Supabase sync if credentials exist
    supabase_url = os.getenv("SUPABASE_URL", "").strip()
    supabase_key = (
        os.getenv("SUPABASE_KEY", "").strip()
        or os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    )

    if supabase_url and supabase_key:
        try:
            endpoint = f"{supabase_url.rstrip('/')}/rest/v1/call_logs"
            headers = {
                "apikey": supabase_key,
                "Authorization": f"Bearer {supabase_key}",
                "Content-Type": "application/json",
            }
            httpx.post(
                endpoint,
                headers=headers,
                json=record.model_dump(),
                timeout=5.0,
            )
        except Exception:
            pass


def extract_and_log_call(messages: list[dict]) -> None:
    """
    Extract structured intake fields and summary from the call transcript using Groq.
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
        "- booking_status (Booked | Inquiry Only | Looked Up)\n"
        "- call_summary (concise 2-3 sentences)\n"
        "- call_outcome (Appointment Booked | General Inquiry | Insurance Inquiry | Appointment Lookup | Emergency)\n"
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
