#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');
const { Solar } = require('lunar-typescript');

const CATEGORIES = new Set(['general', 'relationship', 'career', 'wealth', 'health', 'legal', 'study', 'travel', 'property']);

function parseArgs(argv) {
  const out = {};
  for (const arg of argv) {
    const match = arg.match(/^--([^=]+)=(.*)$/s);
    if (match) out[match[1]] = match[2];
  }
  return out;
}

function requiredNumber(args, key) {
  if (!(key in args) || args[key] === '') throw new Error(`缺少参数: --${key}`);
  const value = Number(args[key]);
  if (!Number.isFinite(value)) throw new Error(`--${key} 必须是数字`);
  return value;
}

function pad(value) {
  return String(value).padStart(2, '0');
}

function partsAtOffset(utcMs, offsetHours) {
  const d = new Date(utcMs + offsetHours * 3600000);
  return {
    year: d.getUTCFullYear(), month: d.getUTCMonth() + 1, day: d.getUTCDate(),
    hour: d.getUTCHours(), minute: d.getUTCMinutes(), second: d.getUTCSeconds(),
  };
}

function isoWithOffset(parts, offsetHours) {
  const sign = offsetHours >= 0 ? '+' : '-';
  const abs = Math.abs(offsetHours);
  const h = Math.floor(abs);
  const m = Math.round((abs - h) * 60);
  return `${parts.year}-${pad(parts.month)}-${pad(parts.day)}T${pad(parts.hour)}:${pad(parts.minute)}:${pad(parts.second || 0)}${sign}${pad(h)}:${pad(m)}`;
}

function calendarData(parts) {
  const solar = Solar.fromYmdHms(parts.year, parts.month, parts.day, parts.hour, parts.minute, parts.second || 0);
  const lunar = solar.getLunar();
  const eight = lunar.getEightChar();
  const pillars = {
    year: eight.getYear(), month: eight.getMonth(), day: eight.getDay(), hour: eight.getTime(),
  };
  const prev = lunar.getPrevJieQi(false);
  const exact = lunar.getJieQi();
  const currentJieQi = exact || (prev ? prev.getName() : '');
  const tiangan = ['甲','乙','丙','丁','戊','己','庚','辛','壬','癸'];
  const dizhi = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥'];
  const jiazi = Array.from({ length: 60 }, (_, i) => tiangan[i % 10] + dizhi[i % 12]);
  const dayIdx = jiazi.indexOf(pillars.day);
  if (dayIdx < 0 || !currentJieQi) throw new Error('无法校准奇门历法数据');
  return {
    year_gan: pillars.year[0], year_zhi: pillars.year[1],
    month_gan: pillars.month[0], month_zhi: pillars.month[1],
    day_gan: pillars.day[0], day_zhi: pillars.day[1],
    hour_gan: pillars.hour[0], hour_zhi: pillars.hour[1],
    day_idx_60: dayIdx,
    current_jieqi: currentJieQi,
    source: 'lunar-typescript@1.8.6',
    previous_jieqi_at: prev ? prev.getSolar().toYmdHms() : '',
  };
}

function runPython(script, payload) {
  const candidates = [];
  if (process.env.PYTHON) candidates.push({ command: process.env.PYTHON, prefix: [] });
  candidates.push({ command: 'python', prefix: [] });
  if (process.platform === 'win32') candidates.push({ command: 'py', prefix: ['-3'] });
  const failures = [];
  for (const candidate of candidates) {
    const result = spawnSync(candidate.command, [...candidate.prefix, script], {
      input: JSON.stringify(payload), encoding: 'utf8', maxBuffer: 16 * 1024 * 1024,
      windowsHide: true,
    });
    if (result.error && result.error.code === 'ENOENT') {
      failures.push(`${candidate.command}: not found`);
      continue;
    }
    if (result.status !== 0) {
      failures.push(`${candidate.command}: ${(result.stderr || result.stdout || 'unknown error').trim()}`);
      continue;
    }
    return result.stdout;
  }
  throw new Error(`奇门 Python 引擎启动失败：${failures.join(' | ')}`);
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  if (!args.question || !args.question.trim()) throw new Error('缺少参数: --question=具体事项');
  if (args.question.trim().length > 500) throw new Error('--question 不得超过 500 字');
  if (!args.output) throw new Error('缺少参数: --output=qimen-chart.json');
  const category = (args.category || 'general').trim();
  if (!CATEGORIES.has(category)) throw new Error('--category 无效');
  const year = requiredNumber(args, 'year');
  const month = requiredNumber(args, 'month');
  const day = requiredNumber(args, 'day');
  const hour = requiredNumber(args, 'hour');
  const minute = requiredNumber(args, 'minute');
  const timeZone = requiredNumber(args, 'timeZone');
  if (!Number.isInteger(year) || year < 1900 || year > 2100) throw new Error('--year 必须在 1900..2100');
  if (!Number.isInteger(month) || month < 1 || month > 12) throw new Error('--month 必须在 1..12');
  if (!Number.isInteger(day) || day < 1 || day > 31) throw new Error('--day 必须在 1..31');
  if (!Number.isInteger(hour) || hour < 0 || hour > 23) throw new Error('--hour 必须在 0..23');
  if (!Number.isInteger(minute) || minute < 0 || minute > 59) throw new Error('--minute 必须在 0..59');
  if (timeZone < -12 || timeZone > 14) throw new Error('--timeZone 必须在 -12..14');
  if (Math.abs(timeZone * 4 - Math.round(timeZone * 4)) > 1e-9) throw new Error('--timeZone 必须以 15 分钟为单位');

  const naiveMs = Date.UTC(year, month - 1, day, hour, minute, 0);
  const check = new Date(naiveMs);
  if (check.getUTCFullYear() !== year || check.getUTCMonth() + 1 !== month || check.getUTCDate() !== day) {
    throw new Error('日期无效');
  }
  const eventUtcMs = naiveMs - timeZone * 3600000;
  const local = { year, month, day, hour, minute, second: 0 };
  const beijing = partsAtOffset(eventUtcMs, 8);
  const calendar = calendarData(beijing);
  const payload = {
    question: args.question.trim(),
    qimenLocalTime: beijing,
    calendar,
  };
  const bridge = path.join(__dirname, 'qimen_core', 'bridge.py');
  const inner = JSON.parse(runPython(bridge, payload));
  const document = {
    schemaVersion: 'laoshifu-qimen-chart.v2',
    question: { text: args.question.trim(), category },
    eventTime: {
      local: isoWithOffset(local, timeZone),
      timeZone,
      utc: new Date(eventUtcMs).toISOString(),
      qimenBeijing: isoWithOffset(beijing, 8),
    },
    calendar: {
      source: calendar.source,
      currentJieQi: calendar.current_jieqi,
      previousJieQiAt: calendar.previous_jieqi_at,
    },
    ...inner,
  };
  fs.writeFileSync(path.resolve(args.output), JSON.stringify(document, null, 2), 'utf8');
  process.stdout.write(`奇门排盘完成：${document.pan.jushu['阴阳遁']}${document.pan.jushu['局数']}局 ${document.pan.jushu['节气']}${document.pan.jushu['元']}\n`);
}

try {
  main();
} catch (error) {
  process.stderr.write(`奇门排盘失败：${error instanceof Error ? error.message : String(error)}\n`);
  process.exitCode = 1;
}
