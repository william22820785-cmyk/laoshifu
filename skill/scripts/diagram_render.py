#!/usr/bin/env python3
"""Stable six-row PNG + line-by-line fallback; runtime uses Python standard library only."""
import argparse
import base64
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import struct
import sys
from urllib.parse import quote
import zlib

TRIGRAMS = {'乾':[1,1,1], '兑':[1,1,0], '离':[1,0,1], '震':[1,0,0],
            '巽':[0,1,1], '坎':[0,1,0], '艮':[0,0,1], '坤':[0,0,0]}
LABELS = {6:'上爻',5:'五爻',4:'四爻',3:'三爻',2:'二爻',1:'初爻'}
WIDTH, HEIGHT = 720, 960
ROW_TOP, ROW_STEP, BAR_OFFSET = 236, 104, 22
LEFT_BAR, RIGHT_BAR, BAR_WIDTH = 188, 466, 174
BG = (250,248,242)
INK = (38,45,42)
MUTED = (85,92,85)
ACCENT = (156,56,42)
FONT_FILE = Path(__file__).with_name('diagram-assets') / 'glyphs.json'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def label(value, max_length=8):
    require(isinstance(value,str) and 0<len(value)<=max_length and all('\u4e00'<=c<='\u9fff' for c in value), '非法或过长的卦图文字')
    return value


def relative(item, keys=('sixRelative','najiaDizhi','wuxing')):
    require(isinstance(item,dict), '六亲纳甲数据缺失')
    a,b,c=(item.get(k) for k in keys)
    require(a in ['父母','兄弟','子孙','妻财','官鬼'] and b in list('子丑寅卯辰巳午未申酉戌亥') and c in list('金木水火土'), '六亲纳甲数据非法')
    return a+b+c


def build_diagram_data(chart):
    """Project only display facts; never parse the old Markdown or re-cast the event."""
    require(isinstance(chart,dict) and chart.get('schemaVersion')=='aceworld-liuyao-chart.v1','需要真实六爻chart.v1')
    lines=chart.get('lines'); hx=chart.get('hexagrams')
    require(isinstance(lines,list) and len(lines)==6 and all(isinstance(x,dict) for x in lines),'需要完整六爻')
    require(all(type(x.get('position')) is int for x in lines) and sorted(x['position'] for x in lines)==[1,2,3,4,5,6], '爻位缺失或重复')
    require(isinstance(hx,dict), '卦名缺失')
    lines=sorted(lines,key=lambda x:x['position'])
    rows=[]
    hidden=chart.get('hiddenSpirits',[])
    require(isinstance(hidden,list) and len(hidden)<=6, '伏神数据非法')
    for h in hidden:
        require(isinstance(h,dict) and type(h.get('position')) is int and h['position'] in range(1,7),'伏神爻位非法')
        relative(h)
    require(len({h['position'] for h in hidden})==len(hidden), '伏神爻位重复')
    for line in lines:
        n=line['position']; v=line.get('rawValue');moving=line.get('isChanging')
        require(type(v) is int and v in (6,7,8,9),'原始爻值非法')
        require(type(moving) is bool and moving==(v in (6,9)), '动静与原始爻值不一致')
        require(line.get('yaoType')==('阳' if v%2 else '阴'), '阴阳与原始爻值不一致')
        require(all(type(line.get(k)) is bool for k in ('isWorld','isResponse')), '世应标记非法')
        require(not(line['isWorld'] and line['isResponse']), '一爻不能同时是世应')
        god=label(line.get('sixGod'),2)
        require(god in ['青龙','朱雀','勾陈','螣蛇','白虎','玄武'], '六神非法')
        changed=relative(line.get('changedYao'),('liuqin','dizhi','wuxing')) if moving else ''
        rows.append({'position':n,'primaryYang':bool(v%2),'changedYang':not bool(v%2) if moving else bool(v%2),
          'moving':moving,'sixGod':god,'relative':relative(line),
          'marker':'世' if line['isWorld'] else '应' if line['isResponse'] else '',
          'changedRelative':changed,'hidden':[relative(h) for h in hidden if h['position']==n]})
    actual=[r['position'] for r in rows if r['moving']]
    require(hx.get('movingLines')==actual,'动爻列表与爻值不一致')
    for side,key in [('primary','primaryYang'),('changed','changedYang')]:
        h=hx.get(side)
        require(isinstance(h,dict) and h.get('lower') in TRIGRAMS and h.get('upper') in TRIGRAMS,'上下卦缺失')
        require([int(r[key]) for r in rows]==TRIGRAMS[h['lower']]+TRIGRAMS[h['upper']], '上下卦与六爻阴阳不一致')
    data={'schemaVersion':'laoshifu-diagram.v1','primaryName':label(hx['primary'].get('name')),
          'changedName':label(hx['changed'].get('name')),'rows':list(reversed(rows))}
    validate_data(data)
    return data


def validate_data(data):
    require(isinstance(data,dict) and data.get('schemaVersion')=='laoshifu-diagram.v1','缺少新版结构化卦图；不要从旧表格猜爻象')
    label(data.get('primaryName'));label(data.get('changedName'))
    rows=data.get('rows')
    require(isinstance(rows,list) and len(rows)==6 and all(isinstance(r,dict) for r in rows), '卦图必须有六行')
    require([r.get('position') for r in rows]==[6,5,4,3,2,1] and all(type(r.get('position')) is int for r in rows), '卦图须从上爻到初爻')
    for r in rows:
        require(all(type(r.get(k)) is bool for k in ['primaryYang','changedYang','moving']), '阴阳动静必须为布尔值')
        require((r['primaryYang']!=r['changedYang'])==r['moving'], '变卦阴阳不匹配')
        label(r.get('sixGod'),2);label(r.get('relative'),4)
        require(r.get('marker') in ('','世','应'), '世应标记非法')
        if r['moving']:label(r.get('changedRelative'),4)
        else:require(r.get('changedRelative')=='','静爻不能伪造变爻纳甲')
        require(isinstance(r.get('hidden'),list) and len(r['hidden'])<=1,'伏神字段非法')
        for text in r['hidden']:label(text,4)
    require(sum(r['marker']=='世' for r in rows)==1 and sum(r['marker']=='应' for r in rows)==1,'必须有一世一应')
    world=next(r['position'] for r in rows if r['marker']=='世');response=next(r['position'] for r in rows if r['marker']=='应')
    require(abs(world-response)==3,'世应位置应相隔三爻')


def validate_fusion_data(fusion):
    require(isinstance(fusion,dict), 'fusion必须为对象')
    validate_data(fusion.get('diagramData'))
    require(fusion.get('stage') not in ['restricted','rejected'], '受限或拒答不得生成卦图')
    # Check duplicated summary fields too; a valid image must not contradict the reading.
    if 'methods' not in fusion:
        return  # Standalone display fixture, not an event-validator admission.
    methods=fusion['methods']
    require(isinstance(methods,dict) and isinstance(methods.get('liuyao'),dict),'缺少六爻摘要')
    summary=methods['liuyao'];data=fusion['diagramData'];rows=data['rows']
    require(summary.get('本卦')==data['primaryName'] and summary.get('变卦')==data['changedName'],'卦图卦名与本次摘要不一致')
    for marker,key in [('世','世爻'),('应','应爻')]:
        row=next(r for r in rows if r['marker']==marker);item=summary.get(key)
        require(isinstance(item,dict) and item.get('爻位')==row['position'],'卦图世应与本次摘要不一致')
        require(relative(item,('六亲','纳支','五行'))==row['relative'] and item.get('六神')==row['sixGod'],'卦图六亲六神与本次摘要不一致')
    moving=summary.get('动爻')
    require(isinstance(moving,list) and all(isinstance(x,dict) for x in moving),'动爻摘要缺失')
    require(sorted(x.get('爻位',0) for x in moving)==sorted(r['position'] for r in rows if r['moving']),'卦图动爻与本次摘要不一致')
    for item in moving:
        row=next(r for r in rows if r['position']==item['爻位'])
        require(relative(item,('六亲','纳支','五行'))==row['relative'] and item.get('六神')==row['sixGod'],'动爻信息与摘要不一致')


def fallback_text(data):
    validate_data(data)
    lines=[f"本卦：{data['primaryName']}；变卦：{data['changedName']}。",'逐爻读法（从上到下）：']
    for r in data['rows']:
        a='阳' if r['primaryYang'] else '阴';b='阳' if r['changedYang'] else '阴'
        change=f'{a}转{b}，动爻' if r['moving'] else f'{a}爻，静爻'
        parts=[LABELS[r['position']],r['sixGod'],r['relative']]
        if r['marker']:parts.append(r['marker'])
        parts.append(change)
        if r['changedRelative']:parts.append('化'+r['changedRelative'])
        parts.extend('伏神'+h for h in r['hidden'])
        lines.append('；'.join(parts)+'。')
    return '\n\n'.join(lines)


@lru_cache(maxsize=1)
def font():
    data=json.loads(FONT_FILE.read_text(encoding='utf-8'))
    require(data.get('schemaVersion')=='laoshifu-glyphs.v1','卦图字形资源损坏')
    return data


def chunk(kind,data):
    return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)


def encode_png(width,height,pixels):
    raw=b''.join(b'\x00'+pixels[y*width*3:(y+1)*width*3] for y in range(height))
    return (b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',width,height,8,2,0,0,0))+
            chunk(b'IDAT',zlib.compress(raw,9))+chunk(b'IEND',b''))


class Canvas:
    """Fixed 2x geometry; CJK glyph masks are bundled, not host fonts or Unicode bars."""
    def __init__(self):
        self.width=WIDTH*2;self.height=HEIGHT*2
        self.pixels=bytearray(bytes(BG)*(self.width*self.height))

    def rect(self,x,y,w,h,color):
        x,y,w,h=(int(v*2) for v in (x,y,w,h))
        require(0<=x and 0<=y and x+w<=self.width and y+h<=self.height,'绘制超出画布')
        row=bytes(color)*w
        for yy in range(y,y+h):
            offset=(yy*self.width+x)*3;self.pixels[offset:offset+w*3]=row

    def text(self,x,y,text,size=24,color=INK,center=False):
        atlas=font();base=atlas['size'];gw=atlas['width'];gh=atlas['height']
        # CJK monospace advance; do not depend on terminal or browser font metrics.
        if center:x-=len(text)*size/2
        xx=int(x*2);yy=int(y*2);s=size*2/base
        for char in text:
            require(char in atlas['glyphs'], '卦图字形缺失，请用逐爻文字备用显示')
            mask=zlib.decompress(base64.b64decode(atlas['glyphs'][char]))
            require(len(mask)==gw*gh,'卦图字形资源损坏')
            dw=round(gw*s);dh=round(gh*s)
            for dy in range(dh):
                py=yy+dy
                require(0<=py<self.height,'文字超出画布')
                for dx in range(dw):
                    alpha=mask[min(gh-1,int(dy/s))*gw+min(gw-1,int(dx/s))]
                    if not alpha:continue
                    px=xx+dx
                    require(0<=px<self.width,'文字超出画布')
                    offset=(py*self.width+px)*3
                    for c in range(3):
                        self.pixels[offset+c]=(color[c]*alpha+self.pixels[offset+c]*(255-alpha)+127)//255
            xx+=round(size*2)

    def bar(self,x,y,yang,color):
        if yang:self.rect(x,y-5,BAR_WIDTH,10,color)
        else:
            side=(BAR_WIDTH-30)//2
            self.rect(x,y-5,side,10,color);self.rect(x+BAR_WIDTH-side,y-5,side,10,color)


def render_png(data):
    validate_data(data)
    c=Canvas()
    c.text(28,15,'六爻卦图',32)
    c.text(28,69,'自上而下：上爻至初爻',20,MUTED)
    c.text(LEFT_BAR+BAR_WIDTH/2,117,'本卦',22,MUTED,True)
    c.text(RIGHT_BAR+BAR_WIDTH/2,117,'变卦',22,MUTED,True)
    c.text(LEFT_BAR+BAR_WIDTH/2,154,data['primaryName'],28,INK,True)
    c.text(RIGHT_BAR+BAR_WIDTH/2,154,data['changedName'],28,INK,True)
    for i,r in enumerate(data['rows']):
        y=ROW_TOP+i*ROW_STEP
        c.rect(28,y-10,664,1,(219,219,208))
        c.text(28,y-3,LABELS[r['position']],24)
        c.text(28,y+31,r['sixGod'],22,MUTED)
        if r['marker']:
            c.text(111,y+4,r['marker'],24,ACCENT)
        color=ACCENT if r['moving'] else INK
        c.bar(LEFT_BAR,y+BAR_OFFSET,r['primaryYang'],color)
        c.bar(RIGHT_BAR,y+BAR_OFFSET,r['changedYang'],color)
        c.text(LEFT_BAR+BAR_WIDTH/2,y+37,r['relative'],22,INK,True)
        c.text(RIGHT_BAR+BAR_WIDTH/2,y+37,'化'+r['changedRelative'] if r['moving'] else '不变',22,color,True)
        if r['moving']:c.text(396,y+2,'动',22,ACCENT)
        for hidden in r['hidden']:c.text(LEFT_BAR,y+68,'伏'+hidden,18,MUTED)
    c.rect(28,864,664,1,(219,219,208))
    c.text(28,875,'实线为阳，断线为阴；动爻以动字标明',18,MUTED)
    c.text(28,908,'世、应标在本卦；伏神写在所属爻下方',18,MUTED)
    return encode_png(c.width,c.height,c.pixels)


def source_hash(fusion):
    return hashlib.sha256(json.dumps(fusion,ensure_ascii=True,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def image_snippet(out):
    # URL-escape spaces, parentheses and other Markdown delimiters in local paths.
    return '![六爻卦图]('+quote((out/'diagram.png').resolve().as_posix(),safe='/:')+')'


def create_bundle(fusion,out):
    out=Path(out).resolve()
    require(not out.exists(),'输出目录已存在，请使用新目录，避免覆盖旧卦图')
    validate_fusion_data(fusion)
    data=fusion['diagramData']
    png=render_png(data);text=fallback_text(data)
    out.mkdir(parents=True)
    (out/'diagram.png').write_bytes(png)
    (out/'fallback.txt').write_text(text+'\n',encoding='utf-8')
    (out/'attachment.md').write_text(image_snippet(out)+'\n',encoding='utf-8')
    manifest={'schemaVersion':'laoshifu-diagram-bundle.v1','rendererVersion':1,
              'sourceSha256':source_hash(fusion),'imageSha256':hashlib.sha256(png).hexdigest(),
              'width':WIDTH*2,'height':HEIGHT*2}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    return manifest


def verify_delivery(fusion,response,mode,bundle=None):
    validate_fusion_data(fusion)
    response=response.replace('\r\n','\n').replace('\r','\n')
    if mode=='text':
        snippet=fallback_text(fusion['diagramData'])
    elif mode=='image':
        require(bundle is not None,'图片模式需要 --diagramBundle')
        manifest_path=Path(bundle).resolve();out=manifest_path.parent
        require(manifest_path.name=='manifest.json','必须指定卦图manifest.json')
        manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
        require(isinstance(manifest,dict) and manifest.get('schemaVersion')=='laoshifu-diagram-bundle.v1','卦图manifest非法')
        require(manifest.get('rendererVersion')==1 and manifest.get('sourceSha256')==source_hash(fusion),'图片不是本次fusion对应的卦图')
        image=out/'diagram.png'
        require(image.is_file() and image.stat().st_size<=2_000_000,'卦图不存在或过大')
        png=image.read_bytes()
        require(hashlib.sha256(png).hexdigest()==manifest.get('imageSha256'),'卦图图片被修改')
        require(png==render_png(fusion['diagramData']),'卦图与六爻数据不一致')
        snippet=image_snippet(out)
    else:
        raise ValueError('diagramMode必须为image或text')
    require(response.startswith(snippet) and response.count(snippet)==1,'答复须先交付本次完整卦图，不得只写文件路径或旧表格')
    prose=response[len(snippet):]
    # Any extra image could contradict the verified one. Revalidate after attaching media.
    require('![' not in prose,'卦图后不得另附未经核对的图片')
    return prose


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--fusion',required=True,type=Path)
    p.add_argument('--out',type=Path)
    p.add_argument('--verify',action='store_true')
    p.add_argument('--response',type=Path)
    p.add_argument('--bundle',type=Path)
    p.add_argument('--mode',choices=['image','text'],default='image')
    p.add_argument('--text',action='store_true')
    a=p.parse_args()
    try:
        require(a.fusion.stat().st_size<=5_000_000,'fusion过大')
        f=json.loads(a.fusion.read_text(encoding='utf-8-sig'))
        if a.verify:
            require(a.response is not None,'需要response')
            prose=verify_delivery(f,a.response.read_text(encoding='utf-8-sig'),a.mode,a.bundle)
            print(json.dumps({'prose':prose},ensure_ascii=False))
        elif a.text:
            validate_fusion_data(f);print(fallback_text(f['diagramData']))
        else:
            require(a.out is not None,'需要out')
            create_bundle(f,a.out);print(str(a.out.resolve()/'attachment.md'))
    except (ValueError,OSError,KeyError,TypeError,zlib.error) as exc:
        print('[FAIL] '+str(exc),file=sys.stderr);return 1
    return 0

if __name__=='__main__':
    if hasattr(sys.stdout,'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8');sys.stderr.reconfigure(encoding='utf-8')
    sys.exit(main())
