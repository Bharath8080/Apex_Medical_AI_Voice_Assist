import datetime
import httpx
from pydantic import BaseModel, Field
from src import config

BASE_URL = "https://api.cal.com/v2"


class BookingPayload(BaseModel):
    start_time: str
    name: str
    email: str
    insurance_provider: str = ""
    reason_for_visit: str = ""
    time_zone: str = "Asia/Kolkata"


def get_headers() -> dict:
    return {
        "Authorization": f"Bearer {config.CALCOM_API_KEY}",
        "cal-api-version": "2024-08-13",
        "Content-Type": "application/json",
    }


def get_available_slots(start_time: str = "", end_time: str = "") -> str:
    """
    Fetch open appointment slots from Cal.com for a given date window.
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    
    if not start_time:
        start_time = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        
    if not end_time:
        end_time = (now + datetime.timedelta(days=3)).strftime("%Y-%m-%dT23:59:59Z")

    params = {
        "startTime": start_time,
        "endTime": end_time,
        "eventTypeId": config.CALCOM_EVENT_TYPE_ID,
    }

    try:
        response = httpx.get(
            f"{BASE_URL}/slots/available",
            headers=get_headers(),
            params=params,
            timeout=10.0,
        )
        
        response_data = response.json()
        slots_data = response_data.get("data", {}).get("slots", {})

        if not slots_data:
            return "No open appointment slots found for the requested time window."

        slot_lines = []
        for date_key, slot_list in list(slots_data.items())[:3]:
            available_times = []
            for slot in slot_list:
                time_val = slot.get("time")
                if time_val:
                    available_times.append(time_val)
                    
            if available_times:
                time_string = ", ".join(available_times[:4])
                slot_lines.append(f"Date {date_key}: [{time_string}]")

        formatted_result = "Available appointment slots:\n" + "\n".join(slot_lines)
        return formatted_result

    except Exception as error:
        return f"Could not fetch available slots: {str(error)}"


def book_appointment(
    start_time: str,
    name: str,
    email: str,
    insurance_provider: str = "",
    reason_for_visit: str = "",
    time_zone: str = "Asia/Kolkata",
) -> str:
    """
    Confirm a new doctor consultation booking on Cal.com with patient intake notes.
    """
    booking = BookingPayload(
        start_time=start_time,
        name=name,
        email=email,
        insurance_provider=insurance_provider,
        reason_for_visit=reason_for_visit,
        time_zone=time_zone,
    )

    notes_parts = []
    if booking.insurance_provider:
        notes_parts.append(f"Insurance: {booking.insurance_provider}")
    if booking.reason_for_visit:
        notes_parts.append(f"Chief Complaint: {booking.reason_for_visit}")

    booking_payload = {
        "start": booking.start_time.strip(),
        "eventTypeId": config.CALCOM_EVENT_TYPE_ID,
        "attendee": {
            "name": booking.name.strip(),
            "email": booking.email.strip(),
            "timeZone": booking.time_zone.strip() or "Asia/Kolkata",
        },
    }

    if notes_parts:
        combined_notes = " | ".join(notes_parts)
        booking_payload["bookingFieldsResponses"] = {"notes": combined_notes}

    try:
        response = httpx.post(
            f"{BASE_URL}/bookings",
            headers=get_headers(),
            json=booking_payload,
            timeout=10.0,
        )

        if response.status_code in (200, 201):
            return (
                f"Appointment successfully confirmed for {booking.name} on {booking.start_time}. "
                f"A calendar confirmation has been sent to {booking.email}. "
                f"Please arrive 10 minutes early to complete check-in paperwork."
            )

        error_message = response.text
        return f"Unable to complete booking: {error_message}"

    except Exception as error:
        return f"Error booking appointment: {str(error)}"


