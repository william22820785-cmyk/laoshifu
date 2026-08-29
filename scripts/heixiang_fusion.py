#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Compatibility wrapper for the bundled dual-divination fusion engine.

The old implementation imported private packages from an author's Linux home
folder. V4 keeps this legacy entry point, but routes it through the portable
`liuyao_qimen_fusion.py` implementation instead.
"""
from datetime import datetime
import json
import os
import tempfile

from liuyao_qimen_fusion import fuse, paipan_liuyao, paipan_qimen


class HeixiangFusion:
    """Backward-compatible API backed by the self-contained V4 engines."""

    def __init__(self, time_zone=8, category='general'):
        self.time_zone = time_zone
        self.category = category
        self._last_raw = {}

    def divine(self, question: str, dt: datetime = None) -> dict:
        if not isinstance(question, str) or not question.strip():
            raise ValueError('question 不能为空')
        dt = dt or datetime.now()
        liuyao = paipan_liuyao(dt, time_zone=self.time_zone, category=self.category, question=question)
        qimen = paipan_qimen(dt.year, dt.month, dt.day, dt.hour, dt.minute, question,
                              time_zone=self.time_zone, category=self.category)
        result = fuse(question, liuyao, qimen, category=self.category)
        self._last_raw = {'question': question, 'datetime': dt.isoformat(), 'liuyao': liuyao, 'qimen': qimen}
        return result