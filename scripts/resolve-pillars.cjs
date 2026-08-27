/**
 * resolve-pillars.cjs — 四柱反查
 * 
 * 从给定的四柱和年份范围反查出可能的出生日期候选。
 * 四柱每60天一周期，同一组四柱可能在某个年份范围内出现多次。
 * 
 * 用法:
 *   node resolve-pillars.cjs --pillars="己卯 丙子 戊午 戊午" --startYear=1999 --endYear=2000 --output=candidates.json
 * 
 * 输出 candidates.json:
 *   {
 *     "query": { "pillars": "己卯 丙子 戊午 戊午", "startYear": 1999, "endYear": 2000 },
 *     "count": 2,
 *     "candidates": [
 *       { "date": "2000-01-15", "pillars": "己卯 丙子 戊午 戊午", "range": "03:00-05:00" },
 *       ...
 *     ]
 *   }
 */

const fs = require('fs');
const path = require('path');

function parseArgs() {
  const args = {};
  process.argv.slice(2).forEach(arg => {
    const m = arg.match(/^--(\w+)=(.+)$/);
    if (m) args[m[1]] = m[2];
  });
  return args;
}

// 天干地支
const TIAN_GAN = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸'];
const DI_ZHI = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥'];

// 时辰对应地支
const HOUR_TO_DIZHI = [
  '子', '子', '丑', '丑', '寅', '寅', '卯', '卯',
  '辰', '辰', '巳', '巳', '午', '午', '未', '未',
  '申', '申', '酉', '酉', '戌', '戌', '亥', '亥',
];

// 节气简化版（精确到日，用于月柱推算）
// 立春约 2/4，惊蛰 3/6，清明 4/5，立夏 5/6，芒种 6/6，小暑 7/7，立秋 8/7，白露 9/8，
// 寒露 10/8，立冬 11/7，大雪 12/7，小寒 1/6
const JIEQI_MONTH_START = [
  { name: '立春', month: 2, day: 4, dzIndex: 2 },   // 寅月
  { name: '惊蛰', month: 3, day: 6, dzIndex: 3 },   // 卯月
  { name: '清明', month: 4, day: 5, dzIndex: 4 },   // 辰月
  { name: '立夏', month: 5, day: 6, dzIndex: 5 },   // 巳月
  { name: '芒种', month: 6, day: 6, dzIndex: 6 },   // 午月
  { name: '小暑', month: 7, day: 7, dzIndex: 7 },   // 未月
  { name: '立秋', month: 8, day: 7, dzIndex: 8 },   // 申月
  { name: '白露', month: 9, day: 8, dzIndex: 9 },   // 酉月
  { name: '寒露', month: 10, day: 8, dzIndex: 10 }, // 戌月
  { name: '立冬', month: 11, day: 7, dzIndex: 11 }, // 亥月
  { name: '大雪', month: 12, day: 7, dzIndex: 0 },  // 子月
  { name: '小寒', month: 1, day: 6, dzIndex: 1 },   // 丑月
];

// 基准日期: 1900-01-01 = 甲戌日 (天干[0]=甲, 地支[10]=戌)
// 实际上需要更精确的计算，这里用简化算法
function getDayGanZhi(year, month, day) {
  // 简化版：基于公历日序计算日柱
  const baseDate = new Date(1900, 0, 1);
  const targetDate = new Date(year, month - 1, day);
  const diffDays = Math.floor((targetDate - baseDate) / (1000 * 60 * 60 * 24));
  
  // 权威基准：1900-01-01 = 甲戌日 (tg=0, dz=10)。
  // 天干：diff%10（甲=0 正确）；地支：1900-01-01 应返回戌=10，故 diff=0 时 dz=10，即 (diff+10)%12。
  const tgIndex = ((diffDays % 10) + 10) % 10;
  const dzIndex = ((diffDays + 10) % 12 + 12) % 12;
  
  return { gan: TIAN_GAN[tgIndex], zhi: DI_ZHI[dzIndex], tgIndex, dzIndex };
}

function getMonthZhiIndex(month, day) {
  // 根据节气确定月支
  for (let i = JIEQI_MONTH_START.length - 1; i >= 0; i--) {
    const jq = JIEQI_MONTH_START[i];
    if (month > jq.month || (month === jq.month && day >= jq.day)) {
      return jq.dzIndex;
    }
  }
  return 1; // 丑月 (小寒到立春前)
}

function getYearGanZhi(year) {
  // 1864 = 甲子年
  const offset = year - 1864;
  const tgIndex = ((offset % 10) + 10) % 10;
  const dzIndex = ((offset % 12) + 12) % 12;
  return { gan: TIAN_GAN[tgIndex], zhi: DI_ZHI[dzIndex], tgIndex, dzIndex };
}

function getMonthGan(yearGanIndex, monthZhiIndex) {
  // 年上起月法（五虎遁）: 甲己之年丙作首
  const monthGanStarts = [2, 4, 6, 8, 0, 2, 4, 6, 8, 0]; // 甲年开始丙寅(索引2)
  const baseGan = monthGanStarts[yearGanIndex];
  const ganIndex = (baseGan + monthZhiIndex - 2 + 12) % 12;
  return TIAN_GAN[ganIndex % 10]; // 地支索引可能超过10，取模
}

function getHourGan(dayGanIndex, hourZhiIndex) {
  // 日上起时法（五鼠遁）: 甲己还加甲
  const hourGanStarts = [0, 2, 4, 6, 8, 0, 2, 4, 6, 8];
  const baseGan = hourGanStarts[dayGanIndex];
  return TIAN_GAN[(baseGan + hourZhiIndex) % 10];
}

function formatPillars(yearPillar, monthPillar, dayPillar, hourPillar) {
  return `${yearPillar.gan}${yearPillar.zhi} ${monthPillar.gan}${monthPillar.zhi} ${dayPillar.gan}${dayPillar.zhi} ${hourPillar.gan}${hourPillar.zhi}`;
}

function getHourRange(hourZhiIndex) {
  const ranges = [
    '23:00-01:00', '01:00-03:00', '03:00-05:00', '05:00-07:00',
    '07:00-09:00', '09:00-11:00', '11:00-13:00', '13:00-15:00',
    '15:00-17:00', '17:00-19:00', '19:00-21:00', '21:00-23:00',
  ];
  return ranges[hourZhiIndex];
}

function main() {
  const args = parseArgs();
  
  if (!args.pillars || !args.startYear || !args.endYear || !args.output) {
    console.error('Usage: node resolve-pillars.cjs --pillars="己卯 丙子 戊午 戊午" --startYear=1999 --endYear=2000 --output=candidates.json');
    process.exit(1);
  }

  const targetPillars = args.pillars.trim();
  const startYear = parseInt(args.startYear);
  const endYear = parseInt(args.endYear);
  const output = args.output;

  const candidates = [];
  const seenDates = new Set();

  for (let year = startYear; year <= endYear; year++) {
    const yearPillar = getYearGanZhi(year);
    
    for (let month = 1; month <= 12; month++) {
      const monthZhiIndex = getMonthZhiIndex(month, 1);
      const monthGan = getMonthGan(yearPillar.tgIndex, monthZhiIndex);
      const monthPillar = { gan: monthGan, zhi: DI_ZHI[monthZhiIndex] };
      
      const daysInMonth = new Date(year, month, 0).getDate();
      
      for (let day = 1; day <= daysInMonth; day++) {
        const dayPillar = getDayGanZhi(year, month, day);
        
        for (let hourDzIdx = 0; hourDzIdx < 12; hourDzIdx++) {
          const hourGan = getHourGan(dayPillar.tgIndex, hourDzIdx);
          const hourPillar = { gan: hourGan, zhi: DI_ZHI[hourDzIdx] };
          
          const fullPillars = formatPillars(yearPillar, monthPillar, dayPillar, hourPillar);
          
          if (fullPillars === targetPillars) {
            const dateStr = `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
            const key = `${dateStr}-${hourDzIdx}`;
            
            if (!seenDates.has(key)) {
              seenDates.add(key);
              candidates.push({
                date: dateStr,
                pillars: fullPillars,
                range: getHourRange(hourDzIdx),
                hourZhiIndex: hourDzIdx,
              });
            }
          }
        }
      }
    }
  }

  const result = {
    query: {
      pillars: targetPillars,
      startYear,
      endYear,
    },
    count: candidates.length,
    candidates: candidates.sort((a, b) => a.date.localeCompare(b.date) || a.hourZhiIndex - b.hourZhiIndex),
  };

  fs.writeFileSync(output, JSON.stringify(result, null, 2), 'utf8');
  
  if (candidates.length === 0) {
    console.log(`[WARN] No candidates found for "${targetPillars}" (${startYear}-${endYear})`);
    console.log('Please verify the pillars or expand the year range.');
    process.exit(1);
  } else if (candidates.length === 1) {
    console.log(`[OK] 1 unique candidate: ${candidates[0].date} (${candidates[0].range})`);
  } else {
    console.log(`[OK] ${candidates.length} candidates found:`);
    candidates.forEach(c => console.log(`  ${c.date} (${c.range})`));
  }
}

main();
