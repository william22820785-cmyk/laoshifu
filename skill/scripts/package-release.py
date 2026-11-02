#!/usr/bin/env python3
"""Create a verified local release candidate; no publish/upload actions."""
import argparse, hashlib, json, re, shutil, zipfile
from datetime import datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
FILES=['SKILL.md','README.md','PRODUCT-COPY.md','CHANGELOG.md','LICENSE','NOTICE','skill-card.md','_meta.json','VOICE-SAMPLES.md']
TREES=['agents','references','scripts','engine']
BLOCK_PARTS={'.git','.clawhub','__pycache__','tests','_local'}
BLOCK_NAMES={'state.json','profile.json','auth.json','.env','fusion.json','chart.json','response.txt','package-lock.json','diagram.png','attachment.md','fallback.txt','manifest.json'}
def allowed(rel):
 return not (set(rel.parts)&BLOCK_PARTS or rel.name in BLOCK_NAMES or rel.suffix in ('.pyc','.pyo','.log','.tmp','.bak') or rel.name.startswith(('test_','test-')))
def build(out):
 if out.exists():raise ValueError('Output directory exists; use a new candidate path')
 version=json.loads((ROOT/'_meta.json').read_text(encoding='utf-8')).get('version')
 if not isinstance(version,str) or not re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+',version):raise ValueError('Invalid release version')
 out.mkdir(parents=True)
 dest=out/'laoshifu';dest.mkdir()
 files=[ROOT/f for f in FILES]
 for tree in TREES:files.extend(p for p in (ROOT/tree).rglob('*') if p.is_file())
 records=[]
 for src in files:
  rel=src.relative_to(ROOT)
  if not allowed(rel):continue
  target=dest/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,target)
  h=hashlib.sha256(src.read_bytes()).hexdigest()
  if hashlib.sha256(target.read_bytes()).hexdigest()!=h:raise ValueError('Copy hash mismatch')
  records.append({'path':rel.as_posix(),'sha256':h})
 for req in ['SKILL.md','scripts/presentation-policy.cjs','references/paid-consultation-standard.md','scripts/liuyao_qimen_fusion.py','engine/calculator/dist/run-chart.js','scripts/diagram_render.py','scripts/diagram-assets/glyphs.json','scripts/diagram-assets/OFL.txt']:
  if not (dest/req).is_file():raise ValueError('Missing '+req)
 if any(not allowed(p.relative_to(dest)) for p in dest.rglob('*') if p.is_file()):raise ValueError('Forbidden artifact in package')
 archive=out/f'laoshifu-{version}-candidate.zip'
 with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
  for p in dest.rglob('*'):
   if p.is_file():z.write(p,p.relative_to(out).as_posix())
 with zipfile.ZipFile(archive) as z:
  if z.testzip():raise ValueError('Archive CRC failed')
 manifest={'version':version,'createdAt':datetime.now().isoformat(),'files':records,'zipSha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'published':False}
 (out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps({'files':len(records),'zipMB':round(archive.stat().st_size/1048576,2),'zip':str(archive),'published':False},ensure_ascii=False))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);build(p.parse_args().out.resolve())
