# 卦图显示：不再靠字符对齐

4.1.2以`fusion.diagramData`为显示真源。它在排盘时由本次原始六爻数据直接生成，包含上爻到初爻六行、阴阳、动静、世应、六神、六亲纳甲、变爻与伏神。`fusion.diagram`仍保留供旧版审计，不是新版用户界面。

## 支持图片的本地对话

1. 在本次会谈目录运行`python <skill-root>/scripts/diagram_render.py --fusion=fusion.json --out=diagram-output`。输出目录必须不存在，避免静默覆盖已有卦图。
2. 查看生成的`diagram.png`：固定1440×1920像素，本卦、变卦共享六行坐标，阳爻是实心矩形，阴爻是中间留白的两段矩形。动爻同时用文字和颜色标识；不靠颜色独自传达信息。位图字形已随包附带，不加载网络字体，也不需要宿主安装Pillow或浏览器。
3. 读取`attachment.md`，原样复制到`response.txt`开头，再写断语。里面是实际图片的绝对路径Markdown嵌入，不是普通文件链接。路径中的空格和括号已经编码，勿擅自改写。
4. 校验：`node <skill-root>/scripts/validate-liuyao-qimen-consultation.cjs --fusion=fusion.json --review=review.json --response=response.txt --diagramMode=image --diagramBundle=diagram-output/manifest.json`。正文有术语时按原规则加publicNotes；不因图片里的标签另凑解释记录。
5. 将核验后的内容发出。不能只说“图已生成”或只贴磁盘路径。生成成功不等于当前渠道必然已显示成功；看不到时改用下面的文字方式。

## 纯文字渠道、图片失败或无障碍阅读

运行`python <skill-root>/scripts/diagram_render.py --fusion=fusion.json --text`。输出逐爻描述：每条独立标明上爻/五爻/四爻/三爻/二爻/初爻、六神、六亲纳甲、世应、阴阳变化、变爻和伏神；换行后也不需要与相邻列对齐。

将输出原样放在`response.txt`开头，再接正文，以`--diagramMode=text`校验，不传diagramBundle。这条路径不加载字形资源，生成图片失败不妨碍文字交付。不要回退成Unicode横线、代码块、HTML表格或Markdown横排表格。

## 跨平台发送与隐私

本地图片路径只用于能够访问该文件的宿主，不能贴给远程用户冒充可见附件。外部渠道优先使用经授权的附件能力；若只有Markdown文本或当前校验无法核实最终附件对应关系，使用逐爻文字。不要为了显示图片擅自上传卦图或问题到图床。

PNG不写入用户问题、生辰、内部评分、融合过程或奇门九宫。manifest含本次fusion指纹，不是用户要读的报告；不同问题即使碰巧同卦，也不能混用旧manifest。会谈产物放私有运行目录，不放skill代码或分发包。

## 旧结果

没有diagramData的旧fusion仍可做历史校验，但新界面不应继续照旧表格显示。若保存了同次原始六爻chart，可以用`build_diagram_data(chart)`生成显示数据并核对原卦名、动爻与世应。没有原始数据时，不从字符间距猜阴阳，也不按当前时间重新起卦来假装是旧卦；说明旧记录不足，并只展示能确认的文字信息。

## 校验范围

校验器比对本次fusion指纹、图片文件哈希，并重新渲染像素字节比较；修改PNG后重算manifest哈希也不能冒充正确图片。原样六行文字和图片标签不计正文长度，正文继续接受术语来源、承诺与内部信息检查。图片核验只证明图与输入数据一致，不证明预测准确，也不保证第三方聊天软件会展示本地附件。
