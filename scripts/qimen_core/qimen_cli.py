#!/usr/bin/env python3
"""奇门遁甲对话式排盘解盘入口"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from datetime import datetime

def paipan(year=None, month=None, day=None, hour=None, minute=0):
    from engine import QimenEngine
    if year is None:
        now = datetime.now()
        year, month, day, hour, minute = now.year, now.month, now.day, now.hour, now.minute
    return QimenEngine().paipan(year, month, day, hour, minute)

def duanju_text(pan, question="综合"):
    from duanju import DuanjuEngine
    return DuanjuEngine().duanju_text(pan, question)

if __name__ == "__main__":
    q = sys.argv[1] if len(sys.argv) > 1 else "综合"
    now = datetime.now()
    pan = paipan(now.year, now.month, now.day, now.hour, now.minute)
    print(duanju_text(pan, q))
