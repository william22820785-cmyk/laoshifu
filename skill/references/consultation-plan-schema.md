# 内部会谈计划

每次实质性断语前，先执行 [dual-method-review.md](dual-method-review.md)，再生成本计划；conclusions 必须与 review.conclusions 深度相等，保留其他计划字段。它是后台工件，不得展示给用户。以下只演示结构，不是现成断语；日期、状态、判断和ID必须按实际输入与盘面重写。

```json
{
  "schemaVersion": "bazi-ziwei-consultation.v1",
  "stage": "calibration|reading|deepening|closure",
  "intent": "curiosity|comfort|decision|learning",
  "topic": "career",
  "focus": {
    "status": "resolved",
    "domain": "career",
    "coreQuestion": "今年主动换工作能不能成？",
    "answerNeed": "outcome",
    "knownContext": ["目前在职", "正在考虑主动换工作"],
    "blockingUnknowns": []
  },
  "calibrationState": {
    "rejectionStreak": 0,
    "confirmedFacts": [],
    "rejectedHypotheses": []
  },
  "calibration": [
    {
      "hypothesis_type": "past-event|current-status|timing|relationship-pattern|input-boundary",
      "statement": "你很能扛事，但责任一多就容易把自己压得太紧。",
      "question": "这几年工作上的责任明显压重了，对不对？",
      "evidence_ids": ["内部 ID"]
    }
  ],
  "conclusions": [
    {
      "id": "career-2026",
      "topic": "career",
      "verdict": "填写有实际依据的主判断，不保证具体事件必然发生。",
      "timing": "有时间依据才填写窗口，否则说明无法定时。",
      "conditions": ["主动整理合作边界，变化会更顺。"],
      "guidance": ["不要在旧承诺上继续加码。"],
      "bazi_evidence_ids": ["内部 bazi ID"],
      "ziwei_evidence_ids": ["内部 ziwei ID"],
      "counter_evidence_ids": [],
      "agreement": "same",
      "bazi_level": "high",
      "ziwei_level": "high",
      "delivery": "direct",
      "resolution_ids": ["本次复核档案内的ID"],
      "uncertainty": "填写本题实际解释边界，不得承诺应验。"
    }
  ],
  "soulNote": ""
}
```

## 字段规则

- `calibration` 每轮最多 1 条；不是所有轮次都需要。
- `conclusions` 每轮最多 4 条，优先只处理用户当前议题。
- `focus.status`：`calibrating|resolved`。校盘阶段可保留未知项；有实质结论时必须为 `resolved`。
- `focus.coreQuestion` 必须是可以直接回答的具体问题；“婚姻、事业、财运怎么样”不合格。
- `focus.answerNeed`：`outcome|timing|turning-point|cause|decision|overview`。
- `focus.knownContext` 在 `resolved` 时至少记录一项已经确认的现实事实；`calibrating` 时可以为空。
- 有实质结论时 `focus.blockingUnknowns` 必须为空；缺少会改变答案的事实就先追问。
- `calibration.hypothesis_type` 说明本轮核对的是过去事件、当前状态、时机、关系模式或输入边界。
- 校盘必须先陈述判断，再用“对不对、对吗、是不是这样”等确认式问句收尾，不得直接问用户现实状态。
- `calibrationState.rejectionStreak` 记录连续明确否认；“不记得、不确定”不增加。
- `rejectionStreak >= 2` 时禁止继续下结论，下一轮 `hypothesis_type` 必须为 `input-boundary`，核对日期、历法、时辰或出生地边界。
- `agreement`：`same` 同向，`complementary` 互补，`conflict` 冲突，`single` 单一体系。
- `*_level`：只能为 `high|medium|low|none`，必须由所列内部证据支持。
- `delivery`：`direct|firm|probable|tentative`。
新解读以 [dual-method-review.md](dual-method-review.md) 的宿主复核档案为准，所有实际新断语都传 --review；无档案入口只保留 legacy 回归/历史恢复。

- `direct/firm` 只用于原证据双高、同范围同向、无反证且没有 unresolved 的条目；主判断明确，条件与局限如实说明，不保证应验。
- `probable` 给有依据的主要倾向与余地；经真实证据说明的互补或条件化可以使用，不因存在被明确保留的反证就机械改成两套结局。原盘弱证据或仍不够支持时用 `tentative`。
- `tentative` 写明具体未定方面；真冲突用 unresolved 并保留双方证据。无需固定“两种可能”或冲突开场，不能隐藏未定处，也不靠一句免责掩盖必然断语。
- 每条结论都填 `resolution_ids` 和非空 `uncertainty`；正文包含最终判断、未定处，并交代已有的时间、条件及行动。事件各条等级保留原值，不能因达成共识升档。

- `counter_evidence_ids` 主动记录同题反证；同范围的真冲突不能标为 `same`。
- `soulNote` 为兼容保留的可选字段，默认留空或省略。不要为填字段另编点命金句；有必要的提醒直接融入正文。

V4.1：用户可见字段允许体系名与真实术语解释；内部ID和算法细节仍不外露。公开术语附独立public-notes.json，遵循 paid-consultation-standard.md。
