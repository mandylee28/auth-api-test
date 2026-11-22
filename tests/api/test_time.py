import re
from datetime import datetime
from zoneinfo import ZoneInfo

import pytest


# Midnight in Bangkok: 2026-11-22 00:00 +07:00.
MIDNIGHT_BANGKOK = int(datetime(2026, 11, 22, 0, 0, tzinfo=ZoneInfo("Asia/Bangkok")).timestamp())

# Half past midnight in Seoul: 2026-11-22 00:30 +09:00.
HALF_PAST_MIDNIGHT_SEOUL = int(
    datetime(2026, 11, 22, 0, 30, tzinfo=ZoneInfo("Asia/Seoul")).timestamp()
)


def test_midnight_bangkok_shows_new_day(client):
    resp = client.get_time("Asia/Bangkok", at=MIDNIGHT_BANGKOK)
    assert resp.status_code == 200
    body = resp.json()
    assert body["timezone"] == "Asia/Bangkok"
    assert body["country"] == "Thailand"
    assert body["message"] == "Thailand is now 11/22 00:00"


def test_same_instant_shows_different_times(client):
    expected = {
        "Asia/Bangkok": "Thailand is now 11/22 00:00",
        "Asia/Singapore": "Singapore is now 11/22 01:00",
        "Asia/Seoul": "South Korea is now 11/22 02:00",
    }
    for tz, message in expected.items():
        resp = client.get_time(tz, at=MIDNIGHT_BANGKOK)
        assert resp.status_code == 200
        assert resp.json()["message"] == message


def test_date_differs_across_timezones_at_midnight(client):
    resp = client.get_time("Asia/Bangkok", at=HALF_PAST_MIDNIGHT_SEOUL)
    assert resp.status_code == 200
    assert resp.json()["message"] == "Thailand is now 11/21 22:30"

    resp = client.get_time("Asia/Singapore", at=HALF_PAST_MIDNIGHT_SEOUL)
    assert resp.status_code == 200
    assert resp.json()["message"] == "Singapore is now 11/21 23:30"

    resp = client.get_time("Asia/Seoul", at=HALF_PAST_MIDNIGHT_SEOUL)
    assert resp.status_code == 200
    assert resp.json()["message"] == "South Korea is now 11/22 00:30"


def test_time_without_at_returns_current_time(client):
    resp = client.get_time("Asia/Singapore")
    assert resp.status_code == 200
    message = resp.json()["message"]

    # The clock keeps ticking between the server's answer and this check,
    # so only the format and the date are pinned down here; the exact
    # minute is covered by the fixed-time tests above.
    now = datetime.now(tz=ZoneInfo("Asia/Singapore"))
    assert re.fullmatch(r"Singapore is now \d+/\d+ \d{2}:\d{2}", message)
    assert message.startswith(f"Singapore is now {now.month}/{now.day}")


def test_unknown_timezone_returns_400(client):
    resp = client.get_time("Mars/Olympus")
    assert resp.status_code == 400
    assert resp.json()["detail"] == "unknown timezone"

    resp = client.get_time("Asia/Jakarta")
    assert resp.status_code == 400
    assert resp.json()["detail"] == "unknown timezone"

    resp = client.get_time("Mars/Olympus", lang="zh-CN")
    assert resp.status_code == 400
    assert resp.json()["detail"] == "未知时区"


@pytest.mark.parametrize(
    "lang,tz,country,message",
    [
        ("en", "Asia/Bangkok", "Thailand", "Thailand is now 11/22 00:00"),
        ("zh-CN", "Asia/Bangkok", "泰国", "泰国现在是11月22日00:00"),
        ("zh-TW", "Asia/Bangkok", "泰國", "泰國現在是11月22日00:00"),
        ("ms", "Asia/Bangkok", "Thailand", "Thailand sekarang 22/11 00:00"),
        ("en", "Asia/Singapore", "Singapore", "Singapore is now 11/22 01:00"),
        ("zh-CN", "Asia/Singapore", "新加坡", "新加坡现在是11月22日01:00"),
        ("zh-TW", "Asia/Singapore", "新加坡", "新加坡現在是11月22日01:00"),
        ("ms", "Asia/Singapore", "Singapura", "Singapura sekarang 22/11 01:00"),
        ("en", "Asia/Seoul", "South Korea", "South Korea is now 11/22 02:00"),
        ("zh-CN", "Asia/Seoul", "韩国", "韩国现在是11月22日02:00"),
        ("zh-TW", "Asia/Seoul", "韓國", "韓國現在是11月22日02:00"),
        ("ms", "Asia/Seoul", "Korea Selatan", "Korea Selatan sekarang 22/11 02:00"),
        ("en", "Asia/Tokyo", "Japan", "Japan is now 11/22 02:00"),
        ("zh-CN", "Asia/Tokyo", "日本", "日本现在是11月22日02:00"),
        ("zh-TW", "Asia/Tokyo", "日本", "日本現在是11月22日02:00"),
        ("ms", "Asia/Tokyo", "Jepun", "Jepun sekarang 22/11 02:00"),
        ("en", "Europe/London", "United Kingdom", "United Kingdom is now 11/21 17:00"),
        ("zh-CN", "Europe/London", "英国", "英国现在是11月21日17:00"),
        ("zh-TW", "Europe/London", "英國", "英國現在是11月21日17:00"),
        ("ms", "Europe/London", "United Kingdom", "United Kingdom sekarang 21/11 17:00"),
        ("en", "America/New_York", "United States", "United States is now 11/21 12:00"),
        ("zh-CN", "America/New_York", "美国", "美国现在是11月21日12:00"),
        ("zh-TW", "America/New_York", "美國", "美國現在是11月21日12:00"),
        ("ms", "America/New_York", "Amerika Syarikat", "Amerika Syarikat sekarang 21/11 12:00"),
    ],
)
def test_time_message_is_localized(client, lang, tz, country, message):
    resp = client.get_time(tz, at=MIDNIGHT_BANGKOK, lang=lang)
    assert resp.status_code == 200
    body = resp.json()
    assert body["country"] == country
    assert body["message"] == message
