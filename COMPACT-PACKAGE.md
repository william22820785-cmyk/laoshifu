# Compact channel package / 文件数量限制适配包

Content version: 4.2.0. Packaging revision: compact.1. Maximum uploaded files: 200.

本包用于文件数量受限的Skill上传场景。实际内容和主技能仍为4.2.0，打包适配本身不是新的排盘算法或准确率升级。

- 六爻入口及CLI不变，算法库和可达JavaScript依赖合并为`scripts/node_modules/@aceworld/liuyao-algorithm/dist/index.js`。
- 两份历法库保留原有CommonJS运行文件、包入口及许可证，路径不变，继续支持农历转换、四柱反查与奇门。
- 移除未被运行引用的映射文件、类型声明、开发配置和未使用的模块；原文档、Python排盘及卦图字形均保留。
- 依赖许可证全文集中保留于THIRD-PARTY-LICENSES.txt；中文位图字形继续遵循scripts/diagram-assets/OFL.txt。
- 合并后的JavaScript为可阅读源码，没有混淆或加密。包内没有嵌套压缩包，没有首次运行解压步骤，也不需要npm install或在线下载依赖。
- 只需与原版相同的Python和Node运行环境。合并工具仅用于开发，不随商品交付。

上传时选择本目录laoshifu或对应ZIP。不要选择外层_build、测试证据或开发仓库。不要让执行测试生成的缓存、会谈资料进入上传目录。

NOTICE中旧依赖路径表示上游归属；已合并依赖的位置以本说明为准。其他市场的商品ID/ownerId不在此包中指定。
