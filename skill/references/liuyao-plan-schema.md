# 六爻+奇门双法会谈计划 (V2.0)

起卦后、答复前从 fusion.json 读取内部数据。本文件定义 V2.0 的 schema。

```json
{
  "schemaVersion": "aceworld-liuyao-qimen-fusion.v2",
  "stage": "reading",
  "question": {
    "text": "这个月底前，甲方会不会签下这份合同？",
    "category": "career",
    "answerNeed": "outcome",
    "desiredOutcome": "确认月底前能否签约",
    "knownContext": ["合同已经发给甲方", "用户正在等待签署"]
  },
  "methods": {
    "liuyao": {
      "本卦": "水山蹇",
      "变卦": "水地比",
      "动爻": [...],
      "世爻": {...},
      "应爻": {...}
    },
    "qimen": {
      "局数": "阴遁4局",
      "节气": "大暑下元",
      "值符": "天冲(落8宫)",
      "值使": "伤门(落8宫)",
      "空亡": "申、酉"
    }
  },
  "agreement": {
    "overall": "same|complementary|conflict",
    "points": [
      {
        "dimension": "总体吉凶",
        "verdict": "偏凶",
        "delivery": "firm",
        "detail": "两法方向一致，均示偏凶之象"
      }
    ],
    "conflicts": [
      {
        "dimension": "方向",
        "liuyao": "南",
        "qimen": "坎一宫(北)",
        "resolution": "两个方向都建议查看"
      }
    ]
  },
  "conclusions": [
    {
      "id": "outcome-1",
      "appliesTo": "月底前甲方签署这份合同",
      "verdict": "直接回答能不能、成不成",
      "timing": "时间窗口",
      "conditions": ["促成条件"],
      "guidance": ["行动建议"],
      "delivery": "firm|probable|tentative",
      "liuyao_evidence_ids": [],
      "qimen_evidence_ids": [],
      "counter_evidence_ids": [],
      "liuyao_level": "high|medium|low",
      "qimen_level": "high|medium|low",
      "agreement": "same|complementary|conflict"
    }
  ],
  "diagram": "标准六爻卦图Markdown（来自六爻排盘）",
  "soulNote": "有些事不是不能成，只是催错了门。"
}
```

## V2.0 新规则

### 双法同断 (六爻+奇门 替代原单六爻规则)

- `agreement.overall = "same"` 且某 conclusion 的 `delivery = "firm"`：强制使用直接断言，删除所有概率词
- `agreement.overall = "conflict"` 或 `agreement.conflicts` 非空：如实说明两种可能，不强行统一
- `liuyao_level = "high"` 且 `qimen_level = "high"` 且无 `counter_evidence_ids`：`delivery` 可为 `firm`
- `liuyao_level` 或 `qimen_level` 任一为 `low`：`delivery` 至少为 `probable`
- 有 `counter_evidence_ids`：降为 `tentative`

### 保留 V1.3 规则

- `question.text` 与起卦时一致，不偷换问题
- `knownContext` 只写用户明确说过的现实
- `appliesTo` 明确每条判断对应的人、事、期限或结果
- `delivery = "firm"` 在方向清楚、无同级反证时使用
- 时间只来自盘内应期边界，不编具体日期
- `soulNote` 不超过断事正文四分之一

### 前台黑盒 (二重强化)

- 用户只看到 `diagram`（标准六爻卦图）+ 统一断语
- 奇门九宫格局、用神定位、空亡宫位永不向用户展示
- 内部字段（evidence_ids、level、methods等JSON键）永不显露
- 正文不出现"六爻"或"奇门"两个词
- 正文不出现用神、旺衰、世应、六亲、六神等六爻术语
- 正文不出现九宫、九星、八门、值符值使等奇门术语
