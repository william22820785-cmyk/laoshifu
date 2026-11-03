#!/usr/bin/env python3
"""Read fixed, verified examples locally. No input collection, network, state or payment."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys

IDS={'birth','contract'}
NOTICE='固定模拟资料经真实排盘程序生成，解释作效果展示；不是客户应验、准确率证据或对你本人的测算。预览本地读取，不上传个人资料，不发起付款。'

def checked_file(root,name,maximum=250000):
    if not isinstance(name,str) or not name or '\\' in name:raise ValueError('示例文件路径无效')
    parts=PurePosixPath(name)
    if parts.is_absolute() or any(p in ('.','..') for p in parts.parts):raise ValueError('示例文件路径无效')
    root=Path(root).resolve();p=root.joinpath(*parts.parts)
    if any(parent.is_symlink() for parent in [p,*p.parents] if parent!=root and parent.is_relative_to(root)):raise ValueError('示例不允许链接文件')
    if not p.resolve().is_relative_to(root) or not p.is_file() or p.stat().st_size>maximum:raise ValueError('示例文件缺失或过大')
    return p.read_bytes()

def catalog(root):
    try:
        m=json.loads(checked_file(root,'manifest.json',16000))
        if not isinstance(m,dict) or m.get('schemaVersion')!='laoshifu-examples.v1':raise ValueError('示例清单格式不符')
        rows=m.get('examples')
        if not isinstance(rows,list) or len(rows)!=2 or {e.get('id') for e in rows if isinstance(e,dict)}!=IDS:raise ValueError('示例清单不完整')
        for e in rows:
            key=e['id'];expected={key+'/source.json',key+'/review.json',key+'/response.txt'}
            if key=='birth':expected.add(key+'/plan.json')
            if e.get('inputType')!='synthetic-fixed' or e.get('response')!=key+'/response.txt':raise ValueError('示例来源标记不符')
            files=e.get('files')
            if not isinstance(files,list) or len(files)!=len(expected) or {f.get('path') for f in files if isinstance(f,dict)}!=expected:raise ValueError('示例文件清单不完整')
            for f in files:
                digest=f.get('sha256')
                if not isinstance(digest,str) or not re.fullmatch('[a-f0-9]{64}',digest):raise ValueError('示例校验值无效')
                if hashlib.sha256(checked_file(root,f['path'])).hexdigest()!=digest:raise ValueError('示例完整性检查失败')
        return rows
    except (OSError,UnicodeError,TypeError,KeyError,json.JSONDecodeError) as error:
        raise ValueError('无法读取完整示例，请重新获取安装包') from error

def render(root,key):
    rows=catalog(root)
    if key not in IDS:raise ValueError('没有这个示例，请选择 birth 或 contract')
    e=next(e for e in rows if e['id']==key)
    try:answer=checked_file(root,e['response']).decode('utf-8')
    except UnicodeError as error:raise ValueError('示例文本格式错误') from error
    return NOTICE+'\n\n'+e['title']+'\n\n'+answer

def main():
    p=argparse.ArgumentParser(description=__doc__);g=p.add_mutually_exclusive_group()
    g.add_argument('--list',action='store_true');g.add_argument('--example',choices=sorted(IDS));a=p.parse_args()
    root=Path(__file__).resolve().parents[1]/'examples'
    try:
        if a.example:print(render(root,a.example))
        else:
            rows=catalog(root);print(NOTICE+'\n');print('\n'.join(e['id']+' — '+e['title'] for e in rows))
        return 0
    except ValueError as error:
        print('示例预览未完成：'+str(error),file=sys.stderr);return 1
if __name__=='__main__':
    if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf-8');sys.stderr.reconfigure(encoding='utf-8')
    raise SystemExit(main())
