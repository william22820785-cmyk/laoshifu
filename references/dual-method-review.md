# 双法独立解读与定点复核

每次新的实质解读（含校盘断语、新问题或新增结论）先读本文件；纯资料问询、原文重呈现及旧订单恢复不等于新解读。方法细节按算人/算事读取，不重复装载全部资料。档案是私有工件，不发给用户。正式个案须先完成 [私有会谈确认](SESSION-PRIVACY.md)，所有输入投影、原盘、review/plan/response及图像均保存在该会谈内；这里的开发示范不替代明确测算意图和保存同意。

## 宿主执行协议

1. **固定输入与真实盘**：核对本题对象、期限、所问方面、用户已确认背景，以及历法、时区/时基、起卦或生辰参数。调用既有真实引擎一次；保留原始 chart.json/fusion.json 的字节，计算 SHA256 并冻结。不能为求一致换盘、重起、改等级或改写原结论。付费版先完成实际 uploadPreview 的明确上传确认，再取得同一资源；问题原文从本地 localContext 读取，不把“隐私问事”当核心问题。
2. **两次独立初读**：算人分配 bazi、ziwei；算事分配 liuyao、qimen。优先使用宿主原生两个隔离子代理。给双方完全相同的核心问题、已确认输入/背景、时间边界与 sourceSha256；各自只收到本法原盘投影、归属本法的证据表及本法方法说明。不给对方材料、初读或主代理拟稿，也不给原融合 agreement/conclusions 作为答案提示。raw methods.level/direction 只是旧摘要，不能压过本法完整证据；以真实字段和全部支持/反证独立解释，不改原盘。主代理保存原文件和投影来源映射，不改原件。
3. **如实记录模式**：确有两个原生子代理启动记录时用 mode=parallel；不支持时用 mode=sequential，按 A→封存 A→B 的顺序完成两次隔离解读。第二次只装载 B 的输入包，不携带 A 初读或合成草稿；使用宿主独立请求/上下文实现隔离，不能把同一段自问自答说成两个子代理。若只能做到任务范围隔离，运行记录如实写清上下文隔离局限；不能声称完成了严格独立初读。缺少任一本法初读就停止该升级交付，不伪造 spawn、审阅人或通过记录。
4. **主代理按命题调和**：先收齐并封存双方初读，再逐条按 subject/time/aspect 和适用条件对齐。时间或方面不同可互补，条件化必须引用真实条件证据；不得直接沿用 raw fusion.conclusions.conditions/guidance（如“先处理回头克”“先落成书面”）当最终调和条件。每项条件重新对照原盘证据与已确认事实，写明它支持哪一具体命题；用户事实保持输入来源，不伪装成盘面证据，也不凭空发明证据 ID。同主体、同时间、同方面的相反判断不能只改写为一致。检查材料是否真的支撑解释，不按年龄、体系名、强硬语气、证据条数或投票裁决。不以共识推出准确率。
5. **最多两轮定点复核**：只向涉及的解读者发送争点 claim ID、相关原证据、对齐范围和具体核对问题；此时才可展示对方相关命题。每轮只核对漏读、对象/时间错位、条件是否成立或解释是否越界。能依据原证据纠错才 corrected；不能凭空补条件。最多两轮；所有 resolution.rounds 记录实际轮数（0/1/2），不是每条争点另获两轮。两轮后仍真冲突用 unresolved，明确该局部未定，可保留其他有依据的结论；不能强迫双方同意。
6. **双方忠实性检查**：两位原解读者分别读最终拟稿、自己初读及涉及本法的 resolutions，只返回简短“通过/异议 + claim/resolution ID + 原证据 + 需改处”。核对有没有偷换范围、吞反证、擅加条件、升高确定性或歪曲本法。主代理记下两个实际回执与执行模式；这是宿主运行记录，不新增 review schema 字段。该检查不是第三轮辩论；异议只按原证据保守修正文稿/档案并再检查，仍需新论据才能解释的地方留 unresolved。任一回执缺失或存在未处理的忠实性异议，不能标完成。
7. **落盘与交付**：写 review.json、response.txt、需要的 public-notes.json；birth 的 consultation-plan.json.conclusions 与 review.conclusions 深度相等，其他计划字段保留。实际新解读都向校验器传 --review；付费 paid_client.py validate 也传 --review，并绑定这份档案哈希。校验失败不静默退回无 review 路径。图像和公开术语始终核对原盘；成功后主代理按详解标准做公开语义二读，只呈现统一判断、简短依据、支持的条件与具体未定处。机器检查不证明解释正确或预测应验。

初读任务可直接使用以下模板（主代理替换方括号，禁止混入另一法初读）：

> 仅按 [method] 解读本次 [focus]；共享输入/范围是 [confirmed input, subject/time/aspect]，源哈希 [sourceSha256]。使用随包给出的本法真实盘及本法证据。逐条返回 {id, proposition, evidence_ids, counter_evidence_ids, scope:{subject,time,aspect}, limits}；每条给有内容的简短解释命题，raw level/direction 仅作旧摘要，按完整证据判断；支持与反证都引用现存本法 ID；birth 注册表不能明确方法来源时，加 source_paths:[{path,value}]，逐项回指本法真实 /bazi 或 /ziwei 字段。列明不能判断的边界。不要读取另一法、原融合答案或拟稿，不重排，不编现实事实，不输出内部思维链。

定点复核任务：

> 第 [1/2] 轮，只核对 [claim IDs] 在 [subject/time/aspect] 上的 [具体争点]。原证据 [IDs/原值]，对方相关命题 [短摘要]。返回“保留/纠正/仍未定”、原证据 ID 与一句理由；纠错明确原 claim ID、原因与证据。不补造条件，不追求一致，不输出逐步内部推理。

## 精确 review.json 合同

schemaVersion 固定为 laoshifu-dual-review.v1；birth source_paths 按本次补充接口执行。下面字段必填；空数组允许但不能省略。只有 relation=corrected 时增加 correction。birth 方法来源不明时，claim 另必填 source_paths:[{path,value}]；event 的 system 来源明确时不要求此字段。JSON 示例中的文字是固定测试解释，不能复制成客户断语。

| 层级 | 字段与约束 |
|---|---|
| 根 | schemaVersion；kind=birth/event；sourceSha256=原文件字节 SHA256 的64位小写十六进制；mode=parallel/sequential；focus=非空具体核心问题；methods/resolutions/conclusions |
| methods | 恰好两项，birth 顺序 bazi/ziwei，event 顺序 liuyao/qimen；每项 {method,claims}，每法至少一个 grounded claim |
| claim | {id,proposition,evidence_ids,counter_evidence_ids,scope,limits,source_paths?}；id 全局唯一非空；proposition 是简短解释命题；支持证据非空；scope={subject,time,aspect} 均非空；limits 为字符串数组 |
| resolutions | 非空；每项 {id,left_claim_ids,right_claim_ids,relation,rationale,condition_evidence_ids,retained_counter_evidence_ids,rounds}；id 唯一；左右分别链接第一/第二法的非空 claim IDs，合计覆盖全部 claims；rationale 给实质理由；rounds 为0到2整数 |
| relation | same=同范围同向；complementary=可同时成立的不同方面；conditional=依真实条件成立；unresolved=真冲突/证据不足仍未定；corrected=原命题有证据支持的纠错。conditional 至少一个真实 condition_evidence_ids；corrected 必填 correction:{method,claim_id,reason,evidence_ids}，指向被纠正本法命题及真实证据 |
| conclusions | 沿用本法计划既有字段，另加 resolution_ids:[存在的 resolution IDs]、uncertainty:非空字符串；每条至少各引本轮两法一个证据。birth 使用 topic、bazi_evidence_ids/ziwei_evidence_ids、bazi_level/ziwei_level；event 使用 appliesTo、liuyao_evidence_ids/qimen_evidence_ids、liuyao_level/qimen_level；其余为 id/verdict/timing/conditions/guidance/counter_evidence_ids/agreement/delivery |

证据注册表：birth=chart.interpretation.evidence，event=fusion.evidence。event 按注册表 system（及明确的 method/source/id）判归属。birth 的 E001 类注册表只有 category/description/strength 时，不能仅凭描述或编号证明方法来源：每个此类 claim 必须加非空 source_paths:[{path,value}]，path 使用 JSON Pointer 指向该法真实 /bazi/... 或 /ziwei/... 字段，value 严格等于源字段（不做字符串化或类型转换）。路径与证据必须实质支撑命题；路径匹配只证明源绑定，不自动证明推断成立。不能用对方法路径证明本法，也不能用路径代替 evidence_ids。未知 ID、空命题、错归属、缺失 claim/结论/反证、越界轮数、哈希不符均失败。

所有 claim 及原 event conclusions 的反证必须在对应 resolution.retained_counter_evidence_ids 留存，最终结论的反证也不能丢失。原 event 的全部结论 ID 必须逐一保留；不把 timing 等条目省掉，只改经过复核的内存有效结论与 agreement，原文件不写回。event 每条 *_level 与原对应条目完全相同；birth 等级仍按原 schema/证据定义，不能借共识升级。

原结论存在冲突、弱证据、反证，或所引 resolution 为 unresolved 时，不得升成 firm/direct。有依据的 complementary/conditional 可以用 probable，并说明余地及有证据支持的适用条件；仍不够则 tentative。unresolved 必须 tentative，uncertainty 写出准确未定之处。无需固定写“两种可能”或“两个体系直接冲突”；也不能把真冲突藏掉。条件中的每一项盘面断言都要有真实证据映射；现实核实项与行动建议单独标成“需现实核实”或“行动建议”（可放 guidance），不得当作盘面已经存在的事实、签约必要条件或调和冲突的证据。“回头克”是盘面关系，不能要求用户现实中“先处理回头克”；未确认的书面流程也不能说成签约的必要条件。没有条件依据就不要编条件。正文包含每条最终 verdict 和 uncertainty，并实质交代已有的 timing/conditions/guidance，不用列内部字段名。

旧无 --review 路径只保留 legacy 回归/历史恢复，不能作为新解读的快捷方式。旧 prepay 状态仍走原订单恢复，不补造新请求、付款或复核回执；新 postpay 交付必须复核。缺少来源或结构无效时停止，不能转静态文字“补算”。

## 可运行的固定资料范例

以下仅是本地协议示范，不是客户资料、应验案例或已执行子代理证明。mode=sequential 仅示范正确填值，实际使用必须完成上述两次隔离初读及双方检查。不能拿范例代替真实执行。

### birth

开发目录的固定原件为 qa/proof-chart.json（合成出生输入经真实引擎排盘，不是客户），完整按字节复制为 birth.json。原输入命令如下，供无原件时重算（免费包有引擎；付费客户端可离线复核，无需调用服务）：

```text
python <free-skill-root>/scripts/chart_bazi_ziwei.py --year=1990 --month=6 --day=15 --hour=10 --minute=30 --gender=male --calendar=solar --timeZone=8 --currentYear=2026 --output=birth.json
```

此固定输入实算得到 E001（日主辛金，果断刚毅，重规矩）和 E006（紫微命宫己丑，太阳/太阴，辅星天魁/天刑）。以下完整 JSON 的哈希对应 qa/proof-chart.json 原件；generatedAt 会变化，重跑后必须按后面的命令改为你实际文件的字节哈希，不能照抄哈希。

```json
{
  "schemaVersion": "laoshifu-dual-review.v1",
  "kind": "birth",
  "sourceSha256": "6fa0726f94c348eb7b34837ffe54e4fefce6a373ee74cd0df731043fc5d1fdbd",
  "mode": "sequential",
  "focus": "这份固定测试盘能够支持怎样的性格描述，有哪些边界？",
  "methods": [
    {"method":"bazi","claims":[{"id":"bz-personality","proposition":"日主辛金的已有判据提示重规矩、处事较果断，不能由此推断具体职业或经历。","evidence_ids":["E001"],"counter_evidence_ids":[],"scope":{"subject":"固定出生测试盘","time":"一般结构，不指定年份","aspect":"性格解释"},"limits":["单一判据不构成人格定型或现实事实。"],"source_paths":[{"path":"/bazi/dayMaster","value":"辛"}]}]},
    {"method":"ziwei","claims":[{"id":"zw-personality","proposition":"命宫太阳、太阴同列，性格解释需看组合，不能简化成单一强硬或柔和。","evidence_ids":["E006"],"counter_evidence_ids":[],"scope":{"subject":"固定出生测试盘","time":"一般结构，不指定年份","aspect":"性格解释"},"limits":["星曜组合只供传统性格解释，不等于经验证的人格或经历。"],"source_paths":[{"path":"/ziwei/gongs/0/gong","value":"命宫"},{"path":"/ziwei/gongs/0/mainStars/0","value":"太阳"},{"path":"/ziwei/gongs/0/mainStars/1","value":"太阴"}]}]}
  ],
  "resolutions": [
    {"id":"r-personality","left_claim_ids":["bz-personality"],"right_claim_ids":["zw-personality"],"relation":"complementary","rationale":"八字提示重规矩、果断，紫微组合提醒表达方式不能只按单一强硬或柔和理解；二者可并存，不推出职业、收入或过去经历。","condition_evidence_ids":[],"retained_counter_evidence_ids":[],"rounds":0}
  ],
  "conclusions": [
    {"id":"personality","topic":"personality","verdict":"你做事可能较重规矩、倾向把事情理清，但表达方式不宜简单定成只有强硬或只有柔和，还需结合具体处境核对。","timing":"本条只谈一般结构，不能据此确定事件时间。","conditions":[],"guidance":["把这条描述与实际处事方式核对，不据此决定职业。"],"bazi_evidence_ids":["E001"],"ziwei_evidence_ids":["E006"],"counter_evidence_ids":[],"agreement":"complementary","bazi_level":"medium","ziwei_level":"medium","delivery":"tentative","resolution_ids":["r-personality"],"uncertainty":"这只是待现实核对的传统性格解释，不能据此认定个人经历或固定人格。"}
  ]
}
```

把 JSON 保存 birth-review.json，再按当前生成文件计算哈希（仅设置这份示例档案的 hash，不改原盘）：

```text
node -e "const f=require('fs'),c=require('crypto'),r=JSON.parse(f.readFileSync('birth-review.json','utf8'));r.sourceSha256=c.createHash('sha256').update(f.readFileSync('birth.json')).digest('hex');f.writeFileSync('birth-review.json',JSON.stringify(r,null,2));"
```

将其 conclusions 原样放进已满足 focus/calibrationState 等约束的 consultation-plan.json（不要覆盖其他字段），答复写出 verdict/uncertainty 等内容，再运行：

```text
node <skill-root>/scripts/validate-consultation.cjs --chart=birth.json --plan=consultation-plan.json --review=birth-review.json --response=response.txt --detail=standard
```

新盘重算的证据值或 ID 若不同，必须重读，不得仅换哈希掩盖差异。正式会谈应先冻结源文件再制作档案，不得在源文件改变后自动“刷新”档案哈希。

### event

固定原件是开发测试资料 qa/proof-fusion.json，完整复制为 fusion.json，不能重新序列化；free/tests/fixtures/diagram-fusion-v3.json 和 paid/tests/fixtures/real-fusion.json 不是同一份字节文件，不得混用哈希。安装包不保证携带测试目录；无固定原件就另取自己有来源的真实测试盘，并重做独立解读，不捏造证据。本例覆盖原 outcome 与 timing 两条结论，逐条保留等级及全部 ly-09/10/11 反证。

```json
{
  "schemaVersion": "laoshifu-dual-review.v1",
  "kind": "event",
  "sourceSha256": "765243bf39f052fd2cd8875cc27f3500839307289dd97b563bc434ef0eb6f8f8",
  "mode": "sequential",
  "focus": "这份合作能否在本月底前签约？",
  "methods": [
    {
      "method": "liuyao",
      "claims": [
        {
          "id": "ly-outcome",
          "proposition": "临应与暗动提供接触或活动线索，但入墓、回头克及文书空亡限制推进，不能坐实月底顺利签约。",
          "evidence_ids": [
            "ly-02",
            "ly-05",
            "ly-03"
          ],
          "counter_evidence_ids": [
            "ly-09",
            "ly-10",
            "ly-11"
          ],
          "scope": {
            "subject": "固定测试合作签约",
            "time": "题设月底前",
            "aspect": "推进结果"
          },
          "limits": [
            "六爻原结论为low，接触点不等于成功。"
          ]
        },
        {
          "id": "ly-timing",
          "proposition": "动爻变化可作观察触发，不能据此锁定某一天。",
          "evidence_ids": [
            "ly-12"
          ],
          "counter_evidence_ids": [],
          "scope": {
            "subject": "固定测试合作签约",
            "time": "题设月底前",
            "aspect": "时机"
          },
          "limits": [
            "没有精确日期依据。"
          ]
        }
      ]
    },
    {
      "method": "qimen",
      "claims": [
        {
          "id": "qm-outcome",
          "proposition": "泛化格局同时含是非阻力与辨明是非的相反线索；没有合同用神落宫及生克对应，不能独立裁决本月底签约成败。",
          "evidence_ids": [
            "qm-01",
            "qm-03",
            "qm-09"
          ],
          "counter_evidence_ids": [
            "qm-03"
          ],
          "scope": {
            "subject": "固定测试合作签约",
            "time": "题设月底前",
            "aspect": "推进结果"
          },
          "limits": [
            "未建立格局与本合同的具体关联，正负线索均不能直接当成现实阻碍或成功。"
          ]
        },
        {
          "id": "qm-timing",
          "proposition": "原盘记录申酉空亡，但没有展示它与合同用神的对应，不能认定本合同因此延期或指定签约日期。",
          "evidence_ids": [
            "qm-09",
            "qm-10"
          ],
          "counter_evidence_ids": [],
          "scope": {
            "subject": "固定测试合作签约",
            "time": "题设月底前",
            "aspect": "时机"
          },
          "limits": [
            "不能从泛化空亡提示推出本合同的必要成事条件或具体应期。"
          ]
        }
      ]
    }
  ],
  "resolutions": [
    {
      "id": "r-outcome",
      "left_claim_ids": [
        "ly-outcome"
      ],
      "right_claim_ids": [
        "qm-outcome"
      ],
      "relation": "unresolved",
      "rationale": "六爻有推进线索也有具体反证；奇门的泛化正负文本缺少合同定位，不能独立确认或反驳月底结果。保留推进空间与六爻阻力，不把另一法材料不足强行调成同向。",
      "condition_evidence_ids": [],
      "retained_counter_evidence_ids": [
        "ly-09",
        "ly-10",
        "ly-11",
        "qm-03"
      ],
      "rounds": 0
    },
    {
      "id": "r-timing",
      "left_claim_ids": [
        "ly-timing"
      ],
      "right_claim_ids": [
        "qm-timing"
      ],
      "relation": "unresolved",
      "rationale": "六爻动变是待观察线索，奇门未建立合同用神与空亡的关联；双方均不能锁定签约日期，不把空亡伪装成已证实的合同条件。",
      "condition_evidence_ids": [],
      "retained_counter_evidence_ids": [],
      "rounds": 0
    }
  ],
  "conclusions": [
    {
      "id": "outcome",
      "appliesTo": "本月底前签约",
      "verdict": "合作有推进线索，但月底前能否真正签成还不能明确判断，落实过程需留意反复。",
      "timing": "本月底前的结果未定。",
      "conditions": [],
      "guidance": [
        "实际核对双方确认进度并保留替代安排；这是现实建议，不代表已知故障。"
      ],
      "delivery": "tentative",
      "liuyao_evidence_ids": [
        "ly-02",
        "ly-05",
        "ly-03"
      ],
      "qimen_evidence_ids": [
        "qm-01",
        "qm-03",
        "qm-09"
      ],
      "counter_evidence_ids": [
        "ly-09",
        "ly-10",
        "ly-11",
        "qm-03"
      ],
      "liuyao_level": "low",
      "qimen_level": "medium",
      "agreement": "conflict",
      "resolution_ids": [
        "r-outcome"
      ],
      "uncertainty": "具体阻力主要来自六爻材料，辅助材料不足以独立形成月底成败判断，不能据此断定最终失败。"
    },
    {
      "id": "timing",
      "appliesTo": "本月底前签约",
      "verdict": "目前不能指定具体签约日期，也不能把出现动向当成月底必然落笔。",
      "timing": "没有充分依据给出某日或月底必成的时间裁决。",
      "conditions": [],
      "guidance": [
        "后续按实际进展重新核对，不将盘面线索当成日历承诺。"
      ],
      "delivery": "tentative",
      "liuyao_evidence_ids": [
        "ly-12"
      ],
      "qimen_evidence_ids": [
        "qm-09",
        "qm-10"
      ],
      "counter_evidence_ids": [],
      "liuyao_level": "medium",
      "qimen_level": "medium",
      "agreement": "conflict",
      "resolution_ids": [
        "r-timing"
      ],
      "uncertainty": "原盘没有建立合同事项与相关时机线索的完整对应，具体期限仍未定。"
    }
  ]
}
```

保存 event-review.json；图像仍从原 fusion.json 生成（文字渠道用 --text 和 --diagramMode=text）：

```text
python <free-skill-root>/scripts/diagram_render.py --fusion=fusion.json --out=diagram-output
node <skill-root>/scripts/validate-liuyao-qimen-consultation.cjs --fusion=fusion.json --review=event-review.json --response=response.txt --detail=standard --diagramMode=image --diagramBundle=diagram-output/manifest.json
```

按需要准备真实术语的 public-notes.json，并给上面命令加 --publicNotes=public-notes.json。付费正式交付最终仍须 paid_client.py validate --state <原状态目录> --review <review.json> --response <response.txt>，birth 同时传 --plan；单跑底层校验不建立客户端 validated 状态。完整呈现后才可 present；只有用户明确表示基本准确并同意结算，才可 settle，金额仍为1.99元。上传确认和 legacy 恢复见本包支付/交付说明。
