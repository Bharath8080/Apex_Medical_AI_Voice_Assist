import datetime
import httpx
from src import config

BASE_URL = "https://api.cal.com/v2"


def _get_headers() -> dict:
    return {
        "Authorization": f"Bearer {config.CALCOM_API_KEY}",
        "cal-api-version": "2024-08-13",
        "Content-Type": "application/json",
    }


def get_available_slots(start_time: str = "", end_time: str = "") -> str:
    """Fetch open appointment slots from Cal.com for the requested date/time window."""
    try:
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

        r = httpx.get(
            f"{BASE_URL}/slots/available",
            headers=_get_headers(),
            params=params,
            timeout=10.0,
        )

        if r.status_code != 200:
            return f"Unable to fetch available slots right now. (Status {r.status_code})"

        data = r.json().get("data", {})
        slots_by_date = data.get("slots", {})

        if not slots_by_date:
            return "There are no available appointment slots in the requested time window."

        # Format readable slots (up to 6 slots)
        formatted_slots = []
        for date_str, slot_list in list(slots_by_date.items())[:3]:
            times = [s.get("time") for s in slot_list if s.get("time")]
            if times:
                formatted_times = ", ".join(times[:4])
                formatted_slots.append(f"Date {date_str}: [{formatted_times}]")

        return "Available appointment slots:\n" + "\n".join(formatted_slots)
    except Exception as e:
        return f"Error fetching appointment availability: {str(e)}"


def book_appointment(
    start_time: str, name: str, email: str, time_zone: str = "Asia/Kolkata"
) -> str:
    """Book a new doctor appointment on Cal.com."""
    try:
        payload = {
            "start": start_time,
            "eventTypeId": config.CALCOM_EVENT_TYPE_ID,
            "attendee": {
                "name": name.strip(),
                "email": email.strip(),
                "timeZone": time_zone.strip() or "Asia/Kolkata",
            },
        }

        r = httpx.post(
            f"{BASE_URL}/bookings",
            headers=_get_headers(),
            json=payload,
            timeout=10.0,
        )

        if r.status_code in (200, 201):
            data = r.json().get("data", {})
            meeting_url = data.get("meetingUrl") or data.get("location") or ""
            return (
                f"Appointment successfully confirmed for {name} on {start_time}. "
                f"A calendar invite and confirmation has been sent to {email}."
            )
        else:
            err_msg = r.text
            try:
                err_msg = r.json().get("error", {}).get("message") or r.text
            except Exception:
                pass
            return f"Failed to book appointment: {err_msg}"
    except Exception as e:
        return f"Error booking appointment: {str(e)}"
