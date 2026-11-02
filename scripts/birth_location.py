#!/usr/bin/env python3
"""Resolve an overseas birthplace into timezone, longitude and true solar time."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import math
import re
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


@dataclass(frozen=True)
class BirthLocation:
    place: str
    timezone_id: str
    longitude: float
    latitude: float | None = None


ALIASES = {
    "beijing china": BirthLocation("Beijing, China", "Asia/Shanghai", 116.4074, 39.9042),
    "北京 中国": BirthLocation("Beijing, China", "Asia/Shanghai", 116.4074, 39.9042),
    "shenzhen china": BirthLocation("Shenzhen, China", "Asia/Shanghai", 114.0579, 22.5431),
    "深圳 中国": BirthLocation("Shenzhen, China", "Asia/Shanghai", 114.0579, 22.5431),
    "sao paulo brazil": BirthLocation("São Paulo, Brazil", "America/Sao_Paulo", -46.6333, -23.5505),
    "são paulo brazil": BirthLocation("São Paulo, Brazil", "America/Sao_Paulo", -46.6333, -23.5505),
    "sao paulo brasil": BirthLocation("São Paulo, Brazil", "America/Sao_Paulo", -46.6333, -23.5505),
    "são paulo brasil": BirthLocation("São Paulo, Brazil", "America/Sao_Paulo", -46.6333, -23.5505),
    "rio de janeiro brazil": BirthLocation("Rio de Janeiro, Brazil", "America/Sao_Paulo", -43.1729, -22.9068),
    "rio de janeiro brasil": BirthLocation("Rio de Janeiro, Brazil", "America/Sao_Paulo", -43.1729, -22.9068),
    "brasilia brazil": BirthLocation("Brasília, Brazil", "America/Sao_Paulo", -47.8825, -15.7942),
    "brasília brazil": BirthLocation("Brasília, Brazil", "America/Sao_Paulo", -47.8825, -15.7942),
    "new york usa": BirthLocation("New York, USA", "America/New_York", -74.0060, 40.7128),
    "new york united states": BirthLocation("New York, USA", "America/New_York", -74.0060, 40.7128),
    "los angeles usa": BirthLocation("Los Angeles, USA", "America/Los_Angeles", -118.2437, 34.0522),
    "london uk": BirthLocation("London, UK", "Europe/London", -0.1276, 51.5072),
    "london united kingdom": BirthLocation("London, UK", "Europe/London", -0.1276, 51.5072),
    "paris france": BirthLocation("Paris, France", "Europe/Paris", 2.3522, 48.8566),
    "lisbon portugal": BirthLocation("Lisbon, Portugal", "Europe/Lisbon", -9.1393, 38.7223),
    "tokyo japan": BirthLocation("Tokyo, Japan", "Asia/Tokyo", 139.6917, 35.6895),
    "sydney australia": BirthLocation("Sydney, Australia", "Australia/Sydney", 151.2093, -33.8688),
}


def _key(value: str) -> str:
    value = value.strip().casefold().replace(",", " ")
    value = re.sub(r"\s+", " ", value)
    return value


def resolve_birthplace(place: str, timezone_id: str | None = None,
                       longitude: float | None = None,
                       latitude: float | None = None) -> BirthLocation:
    if not place or not place.strip():
        raise ValueError("海外算命必须先提供出生地")
    if longitude is not None:
        if not -180 <= longitude <= 180:
            raise ValueError("出生地经度必须在 -180..180")
        if not timezone_id:
            raise ValueError("手动提供经度时必须同时提供 IANA 时区，例如 America/Sao_Paulo")
        try:
            ZoneInfo(timezone_id)
        except ZoneInfoNotFoundError as exc:
            raise ValueError(f"无法识别出生地时区: {timezone_id}") from exc
        return BirthLocation(place.strip(), timezone_id, float(longitude), latitude)

    profile = ALIASES.get(_key(place))
    if profile is None:
        raise ValueError(
            f"未能离线解析出生地「{place}」。请补充城市、国家，以及该地 IANA 时区和经度；"
            "未解析前不得继续海外命盘。"
        )
    return profile


def utc_offset_hours(local_time: datetime, location: BirthLocation) -> float:
    aware = local_time.replace(tzinfo=ZoneInfo(location.timezone_id))
    offset = aware.utcoffset()
    if offset is None:
        raise ValueError("无法取得出生地在该日期的历史时区偏移")
    return offset.total_seconds() / 3600


def equation_of_time_minutes(local_time: datetime) -> float:
    day_of_year = local_time.timetuple().tm_yday
    fractional_day = (
        local_time.hour + local_time.minute / 60 + local_time.second / 3600
    )
    n = day_of_year + (fractional_day - 12) / 24
    b = math.radians((360 / 365.24) * (n - 81))
    return 9.87 * math.sin(2 * b) - 7.53 * math.cos(b) - 1.5 * math.sin(b)


def true_solar_time(local_time: datetime, location: BirthLocation) -> tuple[datetime, dict]:
    offset_hours = utc_offset_hours(local_time, location)
    standard_meridian = offset_hours * 15
    longitude_correction = (location.longitude - standard_meridian) * 4
    equation = equation_of_time_minutes(local_time)
    correction = longitude_correction + equation
    adjusted = local_time + timedelta(minutes=correction)
    return adjusted, {
        "timezoneId": location.timezone_id,
        "utcOffsetHours": offset_hours,
        "longitude": location.longitude,
        "latitude": location.latitude,
        "standardMeridian": standard_meridian,
        "longitudeCorrectionMinutes": longitude_correction,
        "equationOfTimeMinutes": equation,
        "trueSolarCorrectionMinutes": correction,
        "civilLocalTime": local_time.isoformat(),
        "trueSolarLocalTime": adjusted.isoformat(),
    }
