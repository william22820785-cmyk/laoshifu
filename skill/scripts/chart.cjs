/**
 * chart.cjs — 八字紫微排盘脚本
 * 
 * 接收用户出生信息，输出 chart.json 包含八字四柱、大运流年、基本命盘解释。
 * 
 * 用法:
 *   node chart.cjs --year=2000 --month=1 --day=1 --hour=12 --minute=0 \
 *     --gender=male --calendar=solar --timeZone=8 \
 *     --currentYear=2026 --output=chart.json
 * 
 * 可选:
 *   --verifyPillars="己卯 丙子 戊午 戊午"
 *   --trueSolarTime=true --longitude=114.0579
 *   --currentYear=2026
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

// 天干地支常量
const TIAN_GAN = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸'];
const DI_ZHI = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥'];
const SHENG_XIAO = ['鼠', '牛', '虎', '兔', '龙', '蛇', '马', '羊', '猴', '鸡', '狗', '猪'];

// 五行映射
const WU_XING = {
  '甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土',
  '己': '土', '庚': '金', '辛': '金', '壬': '水', '癸': '水',
};

// 节气（简化，月柱分界）
const JIEQI = [
  { name: '立春', month: 2, day: 4, zhiIndex: 2 },
  { name: '惊蛰', month: 3, day: 6, zhiIndex: 3 },
  { name: '清明', month: 4, day: 5, zhiIndex: 4 },
  { name: '立夏', month: 5, day: 6, zhiIndex: 5 },
  { name: '芒种', month: 6, day: 6, zhiIndex: 6 },
  { name: '小暑', month: 7, day: 7, zhiIndex: 7 },
  { name: '立秋', month: 8, day: 7, zhiIndex: 8 },
  { name: '白露', month: 9, day: 8, zhiIndex: 9 },
  { name: '寒露', month: 10, day: 8, zhiIndex: 10 },
  { name: '立冬', month: 11, day: 7, zhiIndex: 11 },
  { name: '大雪', month: 12, day: 7, zhiIndex: 0 },
  { name: '小寒', month: 1, day: 6, zhiIndex: 1 },
];

// 地支藏干
const CANG_GAN = {
  '子': ['癸'],
  '丑': ['己', '癸', '辛'],
  '寅': ['甲', '丙', '戊'],
  '卯': ['乙'],
  '辰': ['戊', '乙', '癸'],
  '巳': ['丙', '庚', '戊'],
  '午': ['丁', '己'],
  '未': ['己', '丁', '乙'],
  '申': ['庚', '壬', '戊'],
  '酉': ['辛'],
  '戌': ['戊', '辛', '丁'],
  '亥': ['壬', '甲'],
};

// 月支对应月序（非节气月）
function getMonthZhiIndex(month, day) {
  for (let i = JIEQI.length - 1; i >= 0; i--) {
    const jq = JIEQI[i];
    if (month > jq.month || (month === jq.month && day >= jq.day)) {
      return jq.zhiIndex;
    }
  }
  return 1; // 丑月
}

function getYearGanZhi(year) {
  const offset = year - 1864;
  return { gan: ((offset % 10) + 10) % 10, zhi: ((offset % 12) + 12) % 12 };
}

function getDayGanZhi(year, month, day) {
  const base = new Date(1900, 0, 1);
  const target = new Date(year, month - 1, day);
  const diff = Math.floor((target - base) / 86400000);
  // 权威基准：1900-01-01 = 甲戌日（tg=0 甲, dz=10 戌）。
  // 天干：diff%10（甲=0 正确）；地支：1900-01-01 应返回戌=10，故 diff=0 时 dz=10，即 (diff+10)%12。
  return { gan: ((diff % 10) + 10) % 10, zhi: ((diff + 10) % 12 + 12) % 12 };
}

function getMonthGan(yearGanIdx, monthZhiIdx) {
  const starts = [2, 4, 6, 8, 0, 2, 4, 6, 8, 0];
  return (starts[yearGanIdx] + monthZhiIdx - 2 + 10) % 10;
}

function getHourGan(dayGanIdx, hourZhiIdx) {
  const starts = [0, 2, 4, 6, 8, 0, 2, 4, 6, 8];
  return (starts[dayGanIdx] + hourZhiIdx) % 10;
}

function getHourZhi(hour, minute) {
  // 23-0:59 子时, 1-2:59 丑时, ...
  const totalMinutes = hour * 60 + minute;
  if (totalMinutes >= 1380 || totalMinutes < 60) return 0; // 23:00-00:59 子
  return Math.floor((totalMinutes - 60) / 120) + 1;
}

function getDayun(gender, yearGanIdx, monthZhiIdx) {
  // 阳年阳男/阴年阴女顺排，否则逆排
  const isYang = yearGanIdx % 2 === 0;
  const isMale = gender === 'male';
  const forward = (isYang && isMale) || (!isYang && !isMale);
  
  const dayuns = [];
  let currentZhi = monthZhiIdx;
  let yearGanStart = yearGanIdx;
  
  for (let i = 0; i < 8; i++) {
    const step = forward ? (i + 1) : -(i + 1);
    const zhiIdx = ((currentZhi + step) % 12 + 12) % 12;
    const ganIdx = ((yearGanStart + 2 + step + 12) % 10);
    
    dayuns.push({
      order: i + 1,
      ganZhi: `${TIAN_GAN[ganIdx % 10]}${DI_ZHI[zhiIdx]}`,
      startAge: 2 + i * 10, // 简化：约2岁起运，每10年一步
      endAge: 12 + i * 10,
    });
  }
  
  return dayuns;
}

function getShiShen(dayGan, targetGan) {
  const ganIdx = TIAN_GAN.indexOf(targetGan);
  const dayIdx = TIAN_GAN.indexOf(dayGan);
  const diff = (ganIdx - dayIdx + 10) % 10;
  
  const names = ['比肩', '劫财', '食神', '伤官', '偏财', '正财', '偏官', '正官', '偏印', '正印'];
  if (ganIdx === dayIdx) return '比肩';
  if (ganIdx % 2 === dayIdx % 2) {
    return diff === 2 ? '食神' : diff === 4 ? '偏财' : diff === 6 ? '偏官' : '偏印';
  } else {
    return diff === 1 ? '劫财' : diff === 3 ? '伤官' : diff === 5 ? '正财' : diff === 7 ? '正官' : '正印';
  }
}

// 生成基本命盘解释 evidence
function generateEvidence(yearGz, monthGz, dayGz, hourGz) {
  const evidence = [];
  let id = 1;
  
  // 基本信息
  const dayElement = WU_XING[dayGz.gan];
  evidence.push({
    id: `E${String(id++).padStart(3, '0')}`,
    category: 'personality',
    description: `日主${dayGz.gan}${dayElement}，${dayElement === '木' ? '为人正直仁德' : dayElement === '火' ? '热情开朗有礼' : dayElement === '土' ? '稳重踏实诚信' : dayElement === '金' ? '果断刚毅讲义气' : '聪慧灵活善变'}`,
    strength: 'high',
  });
  
  // 日主旺衰简评
  const monthZhi = DI_ZHI[monthGz.zhi];
  const supportCount = CANG_GAN[monthZhi].filter(g => WU_XING[g] === dayElement).length;
  const strength = supportCount > 0 ? '中等偏旺' : '中等偏弱';
  evidence.push({
    id: `E${String(id++).padStart(3, '0')}`,
    category: 'profile',
    description: `日主生于${monthGz.gan}${monthZhi}月，${strength}`,
    strength: 'medium',
  });
  
  // 财星简评
  const wealthElement = dayElement === '木' ? '土' : dayElement === '火' ? '金' : dayElement === '土' ? '水' : dayElement === '金' ? '木' : '火';
  const hasWealth = [yearGz.zhi, monthGz.zhi, dayGz.zhi, hourGz.zhi].some(zi => {
    return CANG_GAN[DI_ZHI[zi]] && CANG_GAN[DI_ZHI[zi]].some(g => WU_XING[g] === wealthElement);
  });
  if (hasWealth) {
    evidence.push({
      id: `E${String(id++).padStart(3, '0')}`,
      category: 'wealth',
      description: '命带财库，一生财源不枯',
      strength: 'high',
    });
  }
  
  // 感情简述
  evidence.push({
    id: `E${String(id++).padStart(3, '0')}`,
    category: 'relationship',
    description: '感情路上有波折但终得良缘',
    strength: 'medium',
  });
  
  return evidence;
}

function main() {
  const args = parseArgs();
  
  const year = parseInt(args.year);
  const month = parseInt(args.month);
  const day = parseInt(args.day);
  const hour = parseInt(args.hour);
  const minute = parseInt(args.minute || 0);
  const gender = args.gender || 'male';
  const calendar = args.calendar || 'solar';
  const timeZone = parseInt(args.timeZone || 8);
  const currentYear = parseInt(args.currentYear || new Date().getFullYear());
  const output = args.output || 'chart.json';
  
  if (!year || !month || !day || isNaN(hour)) {
    console.error('Missing required parameters: --year, --month, --day, --hour');
    process.exit(1);
  }
  
  // 农历转公历简化处理（实际应用需完整农历库）
  // 这里简化假设输入已是公历
  const solarYear = calendar === 'lunar' ? year : year;
  const solarMonth = calendar === 'lunar' ? month : month;
  const solarDay = calendar === 'lunar' ? day : day;
  
  // 排四柱
  const ygz = getYearGanZhi(solarYear);
  const mzi = getMonthZhiIndex(solarMonth, solarDay);
  const mgan = getMonthGan(ygz.gan, mzi);
  const dgz = getDayGanZhi(solarYear, solarMonth, solarDay);
  const hzi = getHourZhi(hour, minute);
  const hgan = getHourGan(dgz.gan, hzi);
  
  const pillars = {
    year: { gan: TIAN_GAN[ygz.gan], zhi: DI_ZHI[ygz.zhi] },
    month: { gan: TIAN_GAN[mgan], zhi: DI_ZHI[mzi] },
    day: { gan: TIAN_GAN[dgz.gan], zhi: DI_ZHI[dgz.zhi] },
    hour: { gan: TIAN_GAN[hgan], zhi: DI_ZHI[hzi] },
    formatted: `${TIAN_GAN[ygz.gan]}${DI_ZHI[ygz.zhi]} ${TIAN_GAN[mgan]}${DI_ZHI[mzi]} ${TIAN_GAN[dgz.gan]}${DI_ZHI[dgz.zhi]} ${TIAN_GAN[hgan]}${DI_ZHI[hzi]}`,
  };
  
  // 校验四柱
  if (args.verifyPillars) {
    const verify = args.verifyPillars.trim();
    if (pillars.formatted !== verify) {
      console.log(`[WARN] Pillars mismatch: calculated="${pillars.formatted}", expected="${verify}"`);
    } else {
      console.log(`[OK] Pillars verified: ${pillars.formatted}`);
    }
  }
  
  // 排大运
  const dayuns = getDayun(gender, ygz.gan, mzi);
  
  // 十神
  const shiShen = {
    year: getShiShen(pillars.day.gan, pillars.year.gan),
    month: getShiShen(pillars.day.gan, pillars.month.gan),
    hour: getShiShen(pillars.day.gan, pillars.hour.gan),
  };
  
  // 生成 evidence
  const evidence = generateEvidence(ygz, { gan: mgan, zhi: mzi }, dgz, { gan: hgan, zhi: hzi });
  
  const chart = {
    meta: {
      generatedAt: new Date().toISOString(),
      calendar,
      timeZone,
      gender,
      input: { year, month, day, hour, minute },
      solarConverted: calendar === 'lunar' ? { year: solarYear, month: solarMonth, day: solarDay } : null,
    },
    pillars,
    shiShen,
    dayun: dayuns,
    currentYear: {
      year: currentYear,
      age: currentYear - solarYear,
      liunian: `${TIAN_GAN[((currentYear - 1864) % 10 + 10) % 10]}${DI_ZHI[((currentYear - 1864) % 12 + 12) % 12]}`,
    },
    interpretation: {
      evidence,
      summary: `日主${pillars.day.gan}${WU_XING[pillars.day.gan]}，生于${pillars.month.gan}${pillars.month.zhi}月`,
    },
  };
  
  fs.writeFileSync(output, JSON.stringify(chart, null, 2), 'utf8');
  console.log(`[OK] Chart saved to ${output}`);
  console.log(`     四柱: ${pillars.formatted}`);
  console.log(`     日主: ${pillars.day.gan}${WU_XING[pillars.day.gan]} (${TIAN_GAN[ygz.zhi]}年生，属${SHENG_XIAO[ygz.zhi]})`);
}

main();
