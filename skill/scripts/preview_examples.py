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

def language_tag(value):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z]{2}(?:-[A-Za-z0-9]{2,8})*', value):
        raise ValueError('Unsupported preview language; choose zh, en, es or pt')
    base = value.split('-')[0].lower()
    if base not in {'zh', 'en', 'es', 'pt'}:
        raise ValueError('Unsupported preview language; choose zh, en, es or pt')
    return base


def localized_catalog(root, lang):
    original = catalog(root)
    lang = language_tag(lang)
    try:
        manifest = json.loads(checked_file(root, 'translations/manifest.json', 16000))
        if not isinstance(manifest, dict) or manifest.get('schemaVersion') != 'laoshifu-translations.v1':
            raise ValueError('Invalid translation manifest')
        if manifest.get('sourceManifestSha256') != hashlib.sha256(checked_file(root, 'manifest.json', 16000)).hexdigest():
            raise ValueError('Translation source has changed; refresh the translation bundle')
        locales = manifest.get('locales')
        entry = locales.get(lang) if isinstance(locales, dict) else None
        if not isinstance(entry, dict) or not isinstance(entry.get('notice'), str) or not entry['notice'].strip():
            raise ValueError('Missing translation notice')
        rows = entry.get('examples')
        if not isinstance(rows, list) or len(rows) != 2 or {e.get('id') for e in rows if isinstance(e, dict)} != IDS:
            raise ValueError('Incomplete translated example catalog')
        for row in rows:
            expected = 'translations/' + lang + '/' + row['id'] + '.txt'
            if row.get('response') != expected or not isinstance(row.get('title'), str) or not row['title'].strip():
                raise ValueError('Invalid translated example path or title')
            digest = row.get('sha256')
            if not isinstance(digest, str) or not re.fullmatch('[a-f0-9]{64}', digest):
                raise ValueError('Invalid translated example checksum')
            if hashlib.sha256(checked_file(root, expected)).hexdigest() != digest:
                raise ValueError('Translated example integrity check failed')
        return entry['notice'], rows
    except (OSError, UnicodeError, TypeError, KeyError, json.JSONDecodeError) as error:
        raise ValueError('Cannot load translated examples; get a complete installation') from error


def render(root,key,lang='zh'):
    notice, rows = localized_catalog(root, lang)
    if key not in IDS:raise ValueError('没有这个示例，请选择 birth 或 contract')
    e=next(e for e in rows if e['id']==key)
    try:answer=checked_file(root,e['response']).decode('utf-8')
    except UnicodeError as error:raise ValueError('示例文本格式错误') from error
    return notice+'\n\n'+e['title']+'\n\n'+answer

def render_welcome(skill_root, lang='zh'):
    lang = language_tag(lang)
    try:
        text = checked_file(skill_root, 'references/CULTURAL-WELCOME.' + lang + '.md').decode('utf-8').replace('\r\n', '\n').replace('\r', '\n')
        audit = json.loads(checked_file(skill_root, 'references/cultural-noun-audits/' + lang + '.json', 150000))
        if not isinstance(audit, dict) or audit.get('schemaVersion') != 'laoshifu-noun-audit.v1' or audit.get('language') != lang:
            raise ValueError('Cultural welcome noun audit is invalid')
        if audit.get('textSha256') != hashlib.sha256(text.encode('utf-8')).hexdigest():
            raise ValueError('Cultural welcome changed; review its noun audit again')
        if audit.get('coverage') != 'all-noun-occurrences' or audit.get('reviewedBy') not in {'host-language-review', 'linguist-review', 'pos-tagger+review'}:
            raise ValueError('Cultural welcome needs reviewed noun annotations')
        nouns = audit.get('nouns')
        if not isinstance(nouns, list) or not nouns or len(nouns) > 10000:
            raise ValueError('Cultural welcome noun annotations are missing')
        previous = 0
        for noun in nouns:
            if not isinstance(noun, dict) or type(noun.get('start')) is not int or type(noun.get('end')) is not int:
                raise ValueError('Invalid noun span')
            start, end = noun['start'], noun['end']
            if start < previous or end <= start or end > len(text) or noun.get('pos') not in {'NOUN', 'PROPN'} or type(noun.get('technical')) is not bool:
                raise ValueError('Invalid noun annotations')
            previous = end
        if sum(noun['technical'] for noun in nouns) * 100 >= len(nouns) * 14:
            raise ValueError('Specialist nouns must be below 14% of all nouns')
        return text
    except (OSError, UnicodeError, TypeError, KeyError, json.JSONDecodeError) as error:
        raise ValueError('Cultural welcome unavailable; get a complete installation') from error


def main():
    p=argparse.ArgumentParser(description=__doc__);g=p.add_mutually_exclusive_group()
    g.add_argument('--list',action='store_true');g.add_argument('--example',choices=sorted(IDS))
    g.add_argument('--welcome', action='store_true', help='Explore Chinese culture before choosing a reading')
    p.add_argument('--lang', default='zh', help='Preview language: zh, en, es, pt (regional tags accepted)')
    a=p.parse_args()
    root=Path(__file__).resolve().parents[1]/'examples'
    try:
        if a.welcome:print(render_welcome(root.parent,a.lang), end='')
        elif a.example:print(render(root,a.example,a.lang))
        else:
            notice,rows=localized_catalog(root,a.lang);print(notice+'\n');print('\n'.join(e['id']+' — '+e['title'] for e in rows))
        return 0
    except ValueError as error:
        print('Preview not completed / 示例预览未完成: '+str(error),file=sys.stderr);return 1
if __name__=='__main__':
    if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf-8');sys.stderr.reconfigure(encoding='utf-8')
    raise SystemExit(main())
