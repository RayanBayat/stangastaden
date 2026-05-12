import hashlib
import time
from urllib.parse import parse_qs, urlparse

import requests
from mcp.server.fastmcp import FastMCP

WP = "https://www.stangastaden.se/wp-json/stud/v1"
BOOK = "https://boendeappbackend.stangastaden.se/api"
APP_ID = "DBA877FF-4FAD-4C7E-B1B2-BAECB8B6DC8C"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:149.0) Gecko/20100101 Firefox/149.0"

mcp = FastMCP(
    "stangastaden",
    host="0.0.0.0",
    port=8000,
    stateless_http=True,
    json_response=True,
)

_sessions: dict[str, dict] = {}


def _login(username: str, password: str) -> dict:
    key = hashlib.sha256(f"{username}:{password}".encode()).hexdigest()
    cached = _sessions.get(key)
    if cached and time.time() < cached["exp"]:
        return cached

    s = requests.Session()
    s.headers["User-Agent"] = UA
    s.post(
        f"{WP}/loginguest",
        json={"username": username, "password": password},
    ).raise_for_status()
    loc = s.get(
        "https://www.stangastaden.se/minasidor/mitt-boende/?redirect=booking",
        allow_redirects=False,
    ).headers["Location"]
    tok = parse_qs(urlparse(loc).query)["externalToken"][0]
    jwt = s.post(
        f"{BOOK}/token/external/verify",
        json={
            "externalToken": tok,
            "loginLocation": "External",
            "applicationId": APP_ID,
        },
        headers={
            "Origin": "https://lokalbokning.stangastaden.se",
            "X-APP-VERSION": "4.2.5",
        },
    ).json()["token"]

    entry = {"wp": s, "jwt": jwt, "exp": time.time() + 3500}
    _sessions[key] = entry
    return entry


def _auth_headers(username: str, password: str) -> dict:
    entry = _login(username, password)
    return {
        "Authorization": entry["jwt"],
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "sv",
        "Origin": "https://lokalbokning.stangastaden.se",
        "Referer": "https://lokalbokning.stangastaden.se/",
        "X-APP-VERSION": "4.2.5",
        "User-Agent": UA,
    }


@mcp.tool()
def get_user_profile(username: str, password: str) -> dict:
    """Fetch your Stångåstaden profile (name, address, contact info, settings).

    Args:
        username: Your Stångåstaden guest username (e.g. "28E0400A021").
        password: Your Stångåstaden password.
    """
    return requests.get(
        f"{BOOK}/users/current", headers=_auth_headers(username, password)
    ).json()


@mcp.tool()
def list_my_bookings(username: str, password: str) -> list:
    """List your current and upcoming bookings across all categories (laundry, etc).

    Args:
        username: Your Stångåstaden guest username.
        password: Your Stångåstaden password.
    """
    return requests.get(
        f"{BOOK}/bookings/customerbookings",
        headers=_auth_headers(username, password),
    ).json()


@mcp.tool()
def list_booking_categories(username: str, password: str) -> list:
    """List available booking categories for you (typically Laundry).

    Args:
        username: Your Stångåstaden guest username.
        password: Your Stångåstaden password.
    """
    return requests.get(
        f"{BOOK}/bookings/categories",
        headers=_auth_headers(username, password),
    ).json()


@mcp.tool()
def list_available_slots(
    username: str, password: str, start_date: str, end_date: str
) -> list:
    """List available laundry time slots between two dates.

    Args:
        username: Your Stångåstaden guest username.
        password: Your Stångåstaden password.
        start_date: YYYY-MM-DD (e.g. "2026-04-25").
        end_date: YYYY-MM-DD (e.g. "2026-04-30").
    """
    return requests.get(
        f"{BOOK}/bookings/objects/Laundry/{start_date}/{end_date}",
        headers=_auth_headers(username, password),
    ).json()


@mcp.tool()
def book_slot(
    username: str,
    password: str,
    booking_object_id: str,
    start_timestamp: str,
    length_minutes: int = 180,
) -> dict:
    """Book a laundry slot.

    Args:
        username: Your Stångåstaden guest username.
        password: Your Stångåstaden password.
        booking_object_id: Value from `list_available_slots` (e.g. "66").
        start_timestamp: ISO-8601 with timezone, e.g. "2026-04-25T07:00:00+02:00".
        length_minutes: Slot length in minutes (default 180).
    """
    r = requests.post(
        f"{BOOK}/bookings",
        json={
            "BookingObjectId": str(booking_object_id),
            "StartTimeStamp": start_timestamp,
            "LengthInMinutes": length_minutes,
            "Language": "sv",
        },
        headers={
            **_auth_headers(username, password),
            "Content-Type": "application/json",
        },
    )
    try:
        return r.json()
    except Exception:
        return {"status": r.status_code, "body": r.text}


@mcp.tool()
def cancel_booking(username: str, password: str, booking_id: str) -> str:
    """Cancel an existing booking by ID (from `list_my_bookings`).

    Args:
        username: Your Stångåstaden guest username.
        password: Your Stångåstaden password.
        booking_id: The ID of the booking to cancel.
    """
    r = requests.delete(
        f"{BOOK}/bookings/{booking_id}",
        headers=_auth_headers(username, password),
    )
    if r.ok:
        return f"Cancelled booking {booking_id}."
    return f"Failed to cancel ({r.status_code}): {r.text}"


@mcp.tool()
def list_booking_menu(username: str, password: str) -> list:
    """List the booking category menu items shown in the lokalbokning UI.

    Args:
        username: Your Stångåstaden guest username.
        password: Your Stångåstaden password.
    """
    return requests.get(
        f"{BOOK}/bookings/bookingCategoryMenuItems",
        headers=_auth_headers(username, password),
    ).json()


@mcp.tool()
def area_contacts(username: str, password: str) -> list:
    """Get emergency/area contact info (property manager, phone, email) for your area.

    Args:
        username: Your Stångåstaden guest username.
        password: Your Stångåstaden password.
    """
    entry = _login(username, password)
    return entry["wp"].get(f"{WP}/mypages/areacontacts").json()


@mcp.tool()
def area_news(username: str, password: str, limit: int = 5) -> list:
    """Get recent news/notices for your area.

    Args:
        username: Your Stångåstaden guest username.
        password: Your Stångåstaden password.
        limit: Maximum number of news items to return (default 5).
    """
    entry = _login(username, password)
    return entry["wp"].get(f"{WP}/mypages/areanews", params={"limit": limit}).json()


def main() -> None:
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
