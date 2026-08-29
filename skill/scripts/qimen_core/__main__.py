"""
CLI 入口：python -m qimen_core [year month day hour [minute]]

不带参数则使用当前时间。
"""
import sys
import json
from datetime import datetime

import QimenEngine, format_pan


def main():
    engine = QimenEngine(method="拆补")

    if len(sys.argv) >= 5:
        y = int(sys.argv[1])
        m = int(sys.argv[2])
        d = int(sys.argv[3])
        h = int(sys.argv[4])
        mi = int(sys.argv[5]) if len(sys.argv) >= 6 else 0
    else:
        now = datetime.now()
        y, m, d, h, mi = now.year, now.month, now.day, now.hour, now.minute

    pan = engine.paipan(y, m, d, h, mi)

    # 文本输出
    print(format_pan(pan))
    print()

    # JSON 输出
    print("=== JSON ===")
    print(pan.to_json())


if __name__ == "__main__":
    main()
