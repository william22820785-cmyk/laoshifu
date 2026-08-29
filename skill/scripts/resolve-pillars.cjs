#!/usr/bin/env node
'use strict';

/**
 * 四柱反查：使用技能包内的 lunar-typescript 精确计算每个候选日期/时辰。
 * 不使用固定节气近似，因此正确处理立春换年和节气交接日。
 *
 * 用法：
 * node resolve-pillars.cjs --pillars="甲辰 丙寅 戊戌 甲子" \
 *   --startYear=2024 --endYear=2024 --output=candidates.json
 */
const fs = require('node:fs');
const path = require('node:path');

function loadLunar() {
  const bundled = path.join(__dirname, '..', 'engine', 'calculator', 'node_modules', 'lunar-typescript');
  try {
    return require(bundled);
  } catch (bundledError) {
    try {
      return require('lunar-typescript');
    } catch (hostError) {
      throw new Error(`找不到内置 lunar-typescript：${bundledError.message}; 主机依赖也不可用：${hostError.message}`);
    }
  }
}

const { Solar } = loadLunar();
const BRANCHES = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥'];
const HOUR_SAMPLES = [
  { branch: '子', hour: 0, minute: 30, range: '23:00-01:00' },
  // 子时跨越自然日；23:00 样本必须单独扫描，以正确处理日柱换日。
  { branch: '子', hour: 23, minute: 30, range: '23:00-01:00' },
  { branch: '丑', hour: 1, minute: 30, range: '01:00-03:00' },
  { branch: '寅', hour: 3, minute: 30, range: '03:00-05:00' },
  { branch: '卯', hour: 5, minute: 30, range: '05:00-07:00' },
  { branch: '辰', hour: 7, minute: 30, range: '07:00-09:00' },
  { branch: '巳', hour: 9, minute: 30, range: '09:00-11:00' },
  { branch: '午', hour: 11, minute: 30, range: '11:00-13:00' },
  { branch: '未', hour: 13, minute: 30, range: '13:00-15:00' },
  { branch: '申', hour: 15, minute: 30, range: '15:00-17:00' },
  { branch: '酉', hour: 17, minute: 30, range: '17:00-19:00' },
  { branch: '戌', hour: 19, minute: 30, range: '19:00-21:00' },
  { branch: '亥', hour: 21, minute: 30, range: '21:00-23:00' },
];

function parseArgs(argv = process.argv.slice(2)) {
  const out = {};
  for (const arg of argv) {
    const match = arg.match(/^--([^=]+)=(.*)$/s);
    if (match) out[match[1]] = match[2];
  }
  return out;
}

function fail(message) {
  throw new Error(message);
}

function parseYear(value, label) {
  if (!/^\d{4}$/.test(String(value || ''))) fail(`${label} 必须是四位年份`);
  const year = Number(value);
  if (year < 1 || year > 9999) fail(`${label} 超出范围`);
  return year;
}

function formatDate(year, month, day) {
  return `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
}

function daysInMonth(year, month) {
  return new Date(Date.UTC(year, month, 0)).getUTCDate();
}

function fourPillarsAt(year, month, day, sample) {
  const solar = Solar.fromYmdHms(year, month, day, sample.hour, sample.minute, 0);
  const eight = solar.getLunar().getEightChar();
  return {
    formatted: `${eight.getYear()} ${eight.getMonth()} ${eight.getDay()} ${eight.getTime()}`,
    year: eight.getYear(), month: eight.getMonth(), day: eight.getDay(), hour: eight.getTime(),
  };
}

function main() {
  const args = parseArgs();
  if (!args.pillars || !args.startYear || !args.endYear || !args.output) {
    fail('用法: node resolve-pillars.cjs --pillars="甲辰 丙寅 戊戌 甲子" --startYear=2024 --endYear=2024 --output=candidates.json');
  }
  const targetPillars = args.pillars.trim().replace(/\s+/g, ' ');
  const parts = targetPillars.split(' ');
  if (parts.length !== 4 || parts.some(value => !/^.[^\s]$/u.test(value))) fail('--pillars 必须是四个两字符干支，以空格分隔');
  const startYear = parseYear(args.startYear, '--startYear');
  const endYear = parseYear(args.endYear, '--endYear');
  if (endYear < startYear) fail('--endYear 不能早于 --startYear');
  const output = path.resolve(args.output);

  const candidates = [];
  const seen = new Set();
  for (let year = startYear; year <= endYear; year += 1) {
    for (let month = 1; month <= 12; month += 1) {
      for (let day = 1; day <= daysInMonth(year, month); day += 1) {
        for (const sample of HOUR_SAMPLES) {
          const pillars = fourPillarsAt(year, month, day, sample);
          if (pillars.formatted !== targetPillars) continue;
          const date = formatDate(year, month, day);
          const key = `${date}-${sample.branch}`;
          if (seen.has(key)) continue;
          seen.add(key);
          candidates.push({
            date,
            pillars: pillars.formatted,
            range: sample.range,
            hourBranch: sample.branch,
            sampleHour: sample.hour,
            sampleTime: `${date} ${String(sample.hour).padStart(2, '0')}:${String(sample.minute).padStart(2, '0')}`,
          });
        }
      }
    }
  }

  const result = {
    query: { pillars: targetPillars, startYear, endYear },
    engine: { name: 'lunar-typescript', mode: 'exact-solar-term', handlesLichunYearBoundary: true },
    count: candidates.length,
    candidates,
  };
  fs.writeFileSync(output, JSON.stringify(result, null, 2), 'utf8');
  if (candidates.length === 0) {
    console.log(`[WARN] No candidates found for "${targetPillars}" (${startYear}-${endYear})`);
    process.exitCode = 1;
  } else if (candidates.length === 1) {
    console.log(`[OK] 1 unique candidate: ${candidates[0].date} (${candidates[0].range})`);
  } else {
    console.log(`[OK] ${candidates.length} candidates found`);
  }
}

try {
  main();
} catch (error) {
  console.error(`[FAIL] ${error instanceof Error ? error.message : String(error)}`);
  process.exitCode = 1;
}