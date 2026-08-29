#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Four-pillar boundary audit using the bundled lunar-typescript runtime."""
import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NODE = os.environ.get('NODE') or shutil.which('node') or '/usr/local/lib/python3.11/site-packages/playwright/driver/node'
LUNAR = ROOT / 'engine' / 'calculator' / 'node_modules' / 'lunar-typescript'
SAMPLES = [
    (2000, 1, 1, 12), (2000, 2, 4, 12), (2000, 2, 5, 12),
    (2024, 2, 3, 12), (2024, 2, 4, 12), (2024, 2, 10, 12),
    (1988, 1, 1, 12), (1988, 3, 15, 8), (2025, 12, 31, 23),
]

script = r'''
const { Solar } = require(process.argv[1]);
const samples = JSON.parse(process.argv[2]);
const result = samples.map(([y,m,d,h]) => {
  const e = Solar.fromYmdHms(y,m,d,h,0,0).getLunar().getEightChar();
  return {date: `${y}-${String(m).padStart(2,'0')}-${String(d).padStart(2,'0')} ${String(h).padStart(2,'0')}:00`,
    year:e.getYear(), month:e.getMonth(), day:e.getDay(), hour:e.getTime()};
});
process.stdout.write(JSON.stringify(result));
'''

result = subprocess.run([NODE, '-e', script, str(LUNAR), json.dumps(SAMPLES, ensure_ascii=False)],
                        capture_output=True, text=True, encoding='utf-8', errors='replace')
if result.returncode:
    raise SystemExit(result.stderr or 'bundled calendar audit failed')
print(f"{'公历':<18}{'年柱':<8}{'月柱':<8}{'日柱':<8}{'时柱':<8}")
print('=' * 52)
for row in json.loads(result.stdout):
    print(f"{row['date']:<18}{row['year']:<8}{row['month']:<8}{row['day']:<8}{row['hour']:<8}")