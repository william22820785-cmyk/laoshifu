#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Portable compatibility entry point for the authoritative Bazi chart.

V4 ships the authoritative JavaScript engine inside engine/calculator. This
legacy filename now delegates to that bundled engine rather than importing
lunar_python from the host environment.
"""
import argparse
from datetime import datetime
from chart_bazi_ziwei import build_chart


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--year', type=int, required=True)
    parser.add_argument('--month', type=int, required=True)
    parser.add_argument('--day', type=int, required=True)
    parser.add_argument('--hour', type=int, required=True)
    parser.add_argument('--minute', type=int, default=0)
    parser.add_argument('--gender', default='male')
    parser.add_argument('--calendar', default='solar')
    parser.add_argument('--timeZone', type=int, default=8)
    parser.add_argument('--currentYear', type=int, default=datetime.now().year)
    parser.add_argument('--longitude', type=float, default=None)
    parser.add_argument('--trueSolarTime', default='false')
    parser.add_argument('--verifyPillars', default=None)
    parser.add_argument('--output', default='chart.json')
    return parser.parse_args()


if __name__ == '__main__':
    # The bundled Bazi+Ziwei engine is the single source of truth in V4.
    build_chart(parse_args())