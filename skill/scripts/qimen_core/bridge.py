#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Internal bridge for the laoshifu V2 dual-chart event workflow."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from engine import QimenEngine
from duanju import DuanjuEngine

POSITIVE = ("偏吉", "可为", "有望", "顺利", "良好", "有利", "可放心", "能掌控", "尚在", "转机")
NEGATIVE = ("偏凶", "不利", "受阻", "难以", "难度较大", "延期", "停滞", "反复", "不宜", "虚象")


def derive_signals(report):
    text = report.get("综合结论", "")
    pos = sum(text.count(token) for token in POSITIVE)
    neg = sum(text.count(token) for token in NEGATIVE)
    if pos >= neg + 2:
        direction = "favorable"
    elif neg >= pos + 2:
        direction = "unfavorable"
    else:
        direction = "mixed"
    strength = "high" if abs(pos - neg) >= 3 else "medium" if abs(pos - neg) >= 1 else "low"
    warnings = []
    for state in report.get("特殊状态", []):
        warnings.extend(state.get("问题", []))
    return {
        "direction": direction,
        "strength": strength,
        "positiveMarkers": pos,
        "negativeMarkers": neg,
        "warnings": warnings[:12],
        "keyConclusions": [line.strip("• 🔴") for line in text.splitlines() if line.strip()][:12],
    }


def main():
    request = json.loads(sys.stdin.buffer.read().decode("utf-8"))
    local = request["qimenLocalTime"]
    calendar_data = request["calendar"]
    pan = QimenEngine().paipan(
        int(local["year"]), int(local["month"]), int(local["day"]),
        int(local["hour"]), int(local.get("minute", 0)),
        calendar_data=calendar_data,
    )
    report = DuanjuEngine().duanju(pan, request["question"])
    payload = {
        "pan": pan.to_dict(),
        "interpretation": report,
        "signals": derive_signals(report),
    }
    sys.stdout.buffer.write(json.dumps(payload, ensure_ascii=False, separators=(",", ":"), default=str).encode("utf-8"))


if __name__ == "__main__":
    main()
