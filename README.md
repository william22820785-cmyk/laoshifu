# 老师傅算命测事

这是一个神奇的skill。采用真实排盘与双法独立解读，看命用八字+紫微斗数，看事用六爻+奇门遁甲。命运、婚恋、事业、问事成败与时机；支持公历、农历、四柱反查及时间或三数起卦。先问清资料，调用真实排盘，再把相关依据讲给你听。说话直，但不吓人；需要细讲再展开。

商品介绍见 [PRODUCT-COPY.md](PRODUCT-COPY.md)，对话试读见 [VOICE-SAMPLES.md](VOICE-SAMPLES.md)。

## 4.3.0：独立解读与按命题复核

同一真实盘先由两法隔离初读，再由主代理按主体、时间、方面与真实条件调和，最多两轮定点复核，双方检查合成稿是否忠实。优先宿主原生两个子代理；不能支持时如实记录 sequential 两次隔离解读，不冒称已 spawn。每次实际新解读必须带 `--review=review.json` 校验，birth 计划 conclusions 与 review 相同；原盘字节、反证和图文来源保留。

完整运行协议、birth `source_paths` 归属核对及固定测试资料 JSON 范例见 [双法复核协议](references/dual-method-review.md)。只在新解读时读取；纯资料问询和原文重呈现不重复解读。引擎仍为4.2.0，legacy 恢复继续保留，不增加准确率承诺。

## 历史4.1.2：卦图不再错列

默认生成固定坐标PNG，本卦与变卦的六爻共用行坐标；图片不依赖宿主字体或Markdown表格排版。图片无法显示时，逐爻文字保留全部信息，不拼列。

```text
python scripts/diagram_render.py --fusion=fusion.json --out=diagram-output
```

读取attachment.md嵌入本地图片，再带`--diagramMode=image --diagramBundle=diagram-output/manifest.json`校验。纯文字渠道用`--text`取得逐爻读法，以`--diagramMode=text`校验。详见[卦图显示规则](references/diagram-display.md)。运行只需既有Python标准库和Node，无需新装Pillow、浏览器或字体。字体衍生位图按OFL许可随包分发。

这次只新增显示数据与渲染/核验，不改起卦算法和融合结论；旧Markdown字段保留作历史兼容。

## 4.1.1改了哪里

- 显示名不再带“详解版”，调用名仍为`laoshifu`。
- 重写口吻：不固定开场、分段、金句收尾，不配比文言，不虚构资历。
- 保留详解能力，取消写作目标字数和术语数量；完整问题讲透，后续只补新问题。
- 保留真实排盘、标准卦图、术语来源核对与长度上限校验。两法同向不等于保证应验。
- 普通聊天不念产品流程；被问身份、记忆或故障时如实回答。

这次没有改排盘算法，也没有改福灵桌宠。写作示范不是模型独立实测；自动测试只能证明被检查的程序约束，不能证明语言已完全自然或预测准确。

## 本地使用

需Node.js和Python运行环境，包含既有排盘与问事依赖。Python脚本推荐3.10+。`SKILL.md`是入口，包含调用例子。

- 算人：`scripts/chart_bazi_ziwei.py`。
- 四柱反查：`scripts/resolve-pillars.cjs`。
- 算事：`scripts/liuyao_qimen_fusion.py`。
- 表达与来源要求：[references/paid-consultation-standard.md](references/paid-consultation-standard.md)。

不需要另装福伯或福灵桌面程序。任意时区的节气本地化尚未实现，非东八区边界情况须另核，不宣传全球时区精确换算。

## 验证与打包

```text
node tests/test_v41_presentation.cjs
python tests/test_v41_chart.py
python tests/test_v4_bugfix.py
python tests/test_release_package.py
python tests/test_diagram_render.py
python tests/test_diagram_integration.py
python scripts/package-release.py --out <新的本地候选目录>
```

仓库根目录是维护源，`skill/`是既有ClawHub镜像，打包前同步。`_local/`为本地备份、测试和会谈产物，不进包。包版本读取`_meta.json`，不在打包器里写死。

当前只做本地更新，未推送GitHub、未发布ClawHub、未提交支付宝，未新增会员权限。既有推送可能触发发布工作流，不应把本地验收当作上传授权。

## 边界与隐私

AI传统文化角色，不是真人执业资历或准确率承诺，不替代医疗、法律和投资决定。排盘本地运行不代表对话全程离线。不要把生辰、私事和生成文件随包分发。许可与第三方声明沿用LICENSE及NOTICE。
