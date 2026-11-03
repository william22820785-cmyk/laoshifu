#!/usr/bin/env python3
"""Owner-private consultation sessions; explicit consent and bounded artifact cleanup."""
import argparse
import base64
from contextlib import contextmanager
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
import time
import uuid

ROOT_MARKER='.laoshifu-root.json'
SESSION_MARKER='.laoshifu-session.json'
ROOT_SCHEMA='laoshifu-private-root.v1'
SESSION_SCHEMA='laoshifu-private-session.v1'
ID=re.compile(r's-[a-f0-9]{32}\Z')
SCRIPTS=Path(__file__).resolve().parent
KNOWN={SESSION_MARKER,'chart.json','fusion.json','response.txt','review.json','consultation-plan.json','public-notes.json','candidates.json'}
class SessionError(ValueError):pass

def _now(value=None):
    value=time.time() if value is None else value
    if type(value) not in (int,float) or not math.isfinite(value) or not 0<=value<=4102444800:raise SessionError('时间参数无效')
    return value

def _hash(value):
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def _plain_path(value, exists=True):
    p=Path(value)
    if not p.is_absolute() or '..' in p.parts:raise SessionError('必须使用不含上级跳转的绝对路径')
    for part in [*reversed(p.parents),p]:
        try:s=part.lstat()
        except FileNotFoundError:
            if part==p and not exists:continue
            raise SessionError('目录不存在') from None
        if stat.S_ISLNK(s.st_mode) or getattr(s,'st_file_attributes',0)&0x400:raise SessionError('路径不允许符号链接或重解析点')
    if exists and not p.exists():raise SessionError('路径不存在')
    return p

def _powershell(script,paths):
    executable=Path(os.environ.get('SystemRoot',r'C:\Windows'))/'System32/WindowsPowerShell/v1.0/powershell.exe'
    env=dict(os.environ);env['LAOSHIFU_ACL_PATHS']=json.dumps([str(p) for p in paths])
    command=base64.b64encode(script.encode('utf-16-le')).decode()
    p=subprocess.run([str(executable),'-NoProfile','-NonInteractive','-EncodedCommand',command],env=env,capture_output=True,text=True,encoding='utf-8',timeout=30,shell=False)
    if p.returncode!=0:raise SessionError('无法设置或验证当前用户私有权限')
    return p.stdout.strip()

ACL_SCRIPT=r"""$ErrorActionPreference='Stop'
[Console]::OutputEncoding=[Text.UTF8Encoding]::new()
$me=[Security.Principal.WindowsIdentity]::GetCurrent().User
$system=[Security.Principal.SecurityIdentifier]::new('S-1-5-18')
$paths=ConvertFrom-Json $env:LAOSHIFU_ACL_PATHS
foreach($p in $paths){
 if($env:LAOSHIFU_ACL_SET -eq '1'){
  $acl=[Security.AccessControl.DirectorySecurity]::new()
  $acl.SetOwner($me);$acl.SetAccessRuleProtection($true,$false)
  foreach($id in @($me,$system)){
   $rule=[Security.AccessControl.FileSystemAccessRule]::new($id,'FullControl','ContainerInherit,ObjectInherit','None','Allow')
   $acl.AddAccessRule($rule)
  }
  [IO.Directory]::SetAccessControl($p,$acl)
 }
 $actual=[IO.Directory]::GetAccessControl($p)
 if($actual.GetOwner([Security.Principal.SecurityIdentifier]).Value -ne $me.Value){throw 'Wrong owner'}
 foreach($rule in $actual.Access){
  $sid=$rule.IdentityReference.Translate([Security.Principal.SecurityIdentifier]).Value
  if($rule.AccessControlType -eq 'Allow' -and $sid -notin @($me.Value,$system.Value)){throw 'Public ACL'}
 }
 if(-not $actual.AreAccessRulesProtected){throw 'Unprotected ACL'}
}
$me.Value
"""

def _permissions(paths,secure=False):
    if os.name=='nt':
        # Do not repurpose global environment state across concurrent operations.
        script=ACL_SCRIPT.replace("$env:LAOSHIFU_ACL_SET -eq '1'",'$true' if secure else '$false')
        if secure:_powershell(script,paths)
        import importlib.util
        spec=importlib.util.spec_from_file_location('laoshifu_private_acl',Path(__file__).with_name('private_acl.py'))
        acl=importlib.util.module_from_spec(spec);spec.loader.exec_module(acl)
        owner=None
        for path in paths:owner=acl.verify_private(path,is_directory=path.is_dir())
        return owner
    for p in paths:
        if secure:os.chmod(p,0o700)
        s=p.stat()
        if s.st_uid!=os.getuid() or s.st_mode&0o077:raise SessionError('会谈目录不是当前用户私有目录')
    return str(os.getuid())

def _regular(path,max_size=10000000):
    _plain_path(path);s=path.lstat()
    if not stat.S_ISREG(s.st_mode) or s.st_nlink!=1 or s.st_size>max_size:raise SessionError('文件类型、链接数或大小不符合会谈规则')
    if os.name=='nt':_permissions([path])
    elif s.st_uid!=os.getuid() or s.st_mode&0o077:raise SessionError('文件权限过宽')
    return s

def _read(path,max_size=65536):
    before=_regular(path,max_size)
    flags=os.O_RDONLY|getattr(os,'O_NOFOLLOW',0)|getattr(os,'O_BINARY',0)
    with os.fdopen(os.open(path,flags),'rb') as f:
        after=os.fstat(f.fileno())
        if (before.st_dev,before.st_ino)!=(after.st_dev,after.st_ino):raise SessionError('文件在操作中变化')
        data=f.read(max_size+1)
    if len(data)>max_size:raise SessionError('文件过大')
    return data

def _json(path):
    try:value=json.loads(_read(path))
    except (OSError,UnicodeError,json.JSONDecodeError) as e:raise SessionError('会谈标记无效') from e
    if not isinstance(value,dict):raise SessionError('会谈标记无效')
    return value

def _write(path,value):
    if path.exists():_regular(path)
    data=json.dumps(value,ensure_ascii=False,indent=2).encode()
    temp=path.with_name('.'+uuid.uuid4().hex+'.tmp')
    with os.fdopen(os.open(temp,os.O_WRONLY|os.O_CREAT|os.O_EXCL|getattr(os,'O_BINARY',0),0o600),'wb') as f:f.write(data)
    os.replace(temp,path)

def _root(base):
    base=_plain_path(base)
    if not base.is_dir():raise SessionError('管理根目录无效')
    owner=_permissions([base]);m=_json(base/ROOT_MARKER)
    if m.get('schemaVersion')!=ROOT_SCHEMA or m.get('path')!=str(base) or m.get('owner')!=owner or not re.fullmatch('[a-f0-9]{32}',str(m.get('rootId',''))):raise SessionError('不是有效的私有会谈根目录')
    return base,m

@contextmanager
def _lock(base):
    p=base/'.laoshifu-lock'
    _plain_path(p,exists=False)
    flags=os.O_RDWR|getattr(os,'O_NOFOLLOW',0)|getattr(os,'O_BINARY',0)
    try:
        fd=os.open(p,flags|os.O_CREAT|os.O_EXCL,0o600)
    except FileExistsError:
        _regular(p,1024)
        # Existing locks must never use O_CREAT: a dangling link cannot create
        # an outside target on platforms without O_NOFOLLOW (Windows).
        fd=os.open(p,flags)
    acquired=False
    try:
        before=_regular(p,1024);opened=os.fstat(fd)
        if (before.st_dev,before.st_ino)!=(opened.st_dev,opened.st_ino):raise SessionError('锁文件在操作中变化')
        if opened.st_size==0:os.write(fd,b'0')
        os.lseek(fd,0,0)
        try:
            if os.name=='nt':
                import msvcrt
                msvcrt.locking(fd,msvcrt.LK_NBLCK,1)
            else:
                import fcntl
                fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
            acquired=True
        except OSError:raise SessionError('会谈有操作进行中，请稍后再试') from None
        yield
    finally:
        if acquired:
            if os.name=='nt':
                import msvcrt
                os.lseek(fd,0,0);msvcrt.locking(fd,msvcrt.LK_UNLCK,1)
            else:
                import fcntl
                fcntl.flock(fd,fcntl.LOCK_UN)
        os.close(fd)

def init_root(base):
    base=_plain_path(base,exists=False)
    if base.exists():
        return _root(base)[1]
    if base==SCRIPTS.parent or base.is_relative_to(SCRIPTS.parent):raise SessionError('会谈根目录不能位于技能代码内')
    for parent in base.parents:
        if (parent/'.git').exists():raise SessionError('会谈根目录不能位于Git仓库内')
    base.mkdir(mode=0o700)
    owner=_permissions([base],secure=True)
    marker={'schemaVersion':ROOT_SCHEMA,'rootId':uuid.uuid4().hex,'path':str(base),'owner':owner}
    _write(base/ROOT_MARKER,marker)
    return marker

def _notice(m):
    return ('这次是你明确请求的传统测算。生辰或问题、盘面、答复、复核和图像将保存在本机私有目录：'+m['path']+'。有效期至 '+time.strftime('%Y-%m-%d %H:%M:%S UTC',time.gmtime(m['expiresAt']))+'。到期后不能继续运行本会谈；没有后台定时删除，需运行清理预览并确认后清理，未执行前文件仍可能在磁盘。你也可以提前请求清理，或把要保留的最终答复另行导出到该目录之外；导出、聊天平台记录及备份不由本工具删除。固定示例不需要这些个人资料。是否同意按此方式保存并继续？')

def _notice_hash(m):
    return _hash({'notice':_notice(m),'id':m['id'],'rootId':m['rootId'],'path':m['path'],'createdAt':m['createdAt'],'expiresAt':m['expiresAt']})

def _load(session,require_consent=True,now=None,allow_expired=False):
    session=_plain_path(session)
    if not ID.fullmatch(session.name) or not session.is_dir():raise SessionError('会谈标识无效')
    base,root=_root(session.parent);_permissions([session]);m=_json(session/SESSION_MARKER)
    if m.get('schemaVersion')!=SESSION_SCHEMA or m.get('id')!=session.name or m.get('path')!=str(session) or m.get('rootId')!=root['rootId']:raise SessionError('会谈标记不匹配')
    start,end=m.get('createdAt'),m.get('expiresAt')
    if type(start) not in (int,float) or type(end) not in (int,float) or not math.isfinite(start) or not math.isfinite(end) or not 3600<=end-start<=168*3600:raise SessionError('会谈期限无效')
    if m.get('noticeSha256')!=_notice_hash(m):raise SessionError('会谈告知被改动')
    if require_consent and m.get('consented') is not True:raise SessionError('还没有明确同意保存及测算')
    if not allow_expired and _now(now)>=end:raise SessionError('会谈已到期，请预览并清理，或经新告知另开会谈')
    return m

def load_session(session,require_consent=True,now=None):
    return _load(session,require_consent,now)

def prepare(base,hours=24,now=None):
    if type(hours) is not int or not 1<=hours<=168:raise SessionError('会谈有效期须为1到168小时')
    base,root=_root(base);now=_now(now)
    with _lock(base):
        session=base/('s-'+uuid.uuid4().hex);session.mkdir(mode=0o700);_permissions([session],secure=True)
        m={'schemaVersion':SESSION_SCHEMA,'id':session.name,'rootId':root['rootId'],'path':str(session),'createdAt':now,'expiresAt':now+hours*3600,'consented':False}
        m['noticeSha256']=_notice_hash(m);_write(session/SESSION_MARKER,m)
    return {'session':str(session),'notice':_notice(m),'noticeSha256':m['noticeSha256'],'expiresAt':m['expiresAt']}

def confirm(session,notice_sha256,explicit_request=False,now=None):
    session=_plain_path(session);base,_=_root(session.parent)
    with _lock(base):
        m=_load(session,False,now)
        if explicit_request is not True or notice_sha256!=m['noticeSha256']:raise SessionError('需要明确测算请求及本次保存告知的确认')
        m['consented']=True;_write(session/SESSION_MARKER,m)
    return {'session':str(session),'confirmed':True,'expiresAt':m['expiresAt']}

def run(session,kind,arguments,now=None):
    session=_plain_path(session);base,_=_root(session.parent)
    if kind not in ('birth','event') or not isinstance(arguments,list) or any(not isinstance(a,str) for a in arguments):raise SessionError('只支持本包固定排盘入口')
    allowed={'year','month','day','hour','minute','gender','calendar','isLeapMonth','verifyPillars','timeZone','market','birthPlace','birthTimezone','longitude','latitude','trueSolarTime','currentYear'} if kind=='birth' else {'question','category','method','numbers','year','month','day','hour','minute','timeZone','timeBasis','desiredOutcome','knownContext'}
    if any(not a or (a.startswith('--') and a[2:].split('=',1)[0] not in allowed) for a in arguments):raise SessionError('排盘参数未获准；输出位置由私有会谈固定')
    with _lock(base):
        _load(session,True,now)
        output=session/('chart.json' if kind=='birth' else 'fusion.json')
        if output.exists() or output.is_symlink():raise SessionError('本轮已有盘面，追问请沿用原盘，不覆盖重起')
        script=SCRIPTS/('chart_bazi_ziwei.py' if kind=='birth' else 'liuyao_qimen_fusion.py')
        old=os.umask(0o077) if os.name!='nt' else None
        try:p=subprocess.run([sys.executable,str(script),*arguments,'--output='+str(output)],cwd=session,capture_output=True,text=True,encoding='utf-8',timeout=120,shell=False)
        finally:
            if old is not None:os.umask(old)
        if p.returncode!=0:raise SessionError('本次排盘未成功；保留私有目录核对，不重新起卦或发起付款')
        _regular(output)
        return {'ok':True,'session':str(session),'output':str(output),'expiresAt':_load(session,True,now)['expiresAt']}

def _inventory(session):
    files=[];dirs=[]
    def visit(folder):
        _plain_path(folder)
        for p in sorted(folder.iterdir()):
            s=p.lstat();rel=p.relative_to(session).as_posix()
            if stat.S_ISLNK(s.st_mode) or getattr(s,'st_file_attributes',0)&0x400:raise SessionError('存在链接或重解析点，保留整个会谈')
            if stat.S_ISDIR(s.st_mode):
                if rel!='diagram-output':raise SessionError('存在未登记目录，保留整个会谈')
                dirs.append(rel);visit(p)
            elif stat.S_ISREG(s.st_mode):
                if rel not in KNOWN and not (rel in {'diagram-output/diagram.png','diagram-output/fallback.txt','diagram-output/attachment.md','diagram-output/manifest.json'}):raise SessionError('存在用户文件或订单状态，保留整个会谈')
                data=_read(p,10000000);files.append({'path':rel,'sha256':hashlib.sha256(data).hexdigest(),'size':len(data)})
                if len(files)>512:raise SessionError('会谈文件过多')
            else:raise SessionError('存在特殊文件，保留整个会谈')
    visit(session)
    if sum(f['size'] for f in files)>20000000:raise SessionError('会谈过大，需单独处理')
    return files,sorted(dirs,key=lambda x:len(PurePosixPath(x).parts),reverse=True)

def _plan(base,session_id,include_active,now):
    base,root=_root(base);now=_now(now)
    if type(include_active) is not bool:raise SessionError('清理模式无效')
    if include_active and not session_id:raise SessionError('提前清理必须明确指定一个会谈')
    if session_id is not None and (not isinstance(session_id,str) or not ID.fullmatch(session_id)):raise SessionError('会谈标识无效')
    selected=[base/session_id] if session_id else sorted(p for p in base.iterdir() if ID.fullmatch(p.name))
    items=[];skipped=[]
    for session in selected:
        try:
            m=_load(session,False,now,allow_expired=True)
            if not include_active and now<m['expiresAt']:continue
            files,dirs=_inventory(session);items.append({'id':session.name,'files':files,'directories':dirs})
        except (OSError,ValueError) as e:skipped.append({'id':session.name,'reason':str(e)})
    payload={'schemaVersion':'laoshifu-cleanup-plan.v1','base':str(base),'rootId':root['rootId'],'sessionId':session_id,'includeActive':include_active,'sessions':items,'skipped':skipped}
    payload['planSha256']=_hash(payload)
    return payload

def cleanup_plan(base,session_id=None,include_active=False,now=None):
    base,_=_root(base)
    with _lock(base):return _plan(base,session_id,include_active,now)

def cleanup(base,plan_sha256,session_id=None,include_active=False,now=None):
    base,_=_root(base)
    with _lock(base):
        plan=_plan(base,session_id,include_active,now)
        if plan_sha256!=plan['planSha256']:raise SessionError('清理清单已变化，请重新预览并确认')
        # Only generated, fingerprint-matched regular files under validated session roots.
        for item in plan['sessions']:
            session=base/item['id'];_plain_path(session)
            for file in item['files']:
                p=session/file['path']
                if hashlib.sha256(_read(p,10000000)).hexdigest()!=file['sha256']:raise SessionError('清理过程中内容变化，已停止')
            # Keep the management marker until all other work has completed, so an
            # interrupted cleanup remains identifiable and can be previewed again.
            ordered=sorted(item['files'],key=lambda f:f['path']==SESSION_MARKER)
            for file in ordered:
                if file['path']==SESSION_MARKER:continue
                p=session/file['path'];_regular(p);p.unlink()
            for rel in item['directories']:_plain_path(session/rel);(session/rel).rmdir()
            _regular(session/SESSION_MARKER);(session/SESSION_MARKER).unlink()
            session.rmdir()
        return {'removed':[i['id'] for i in plan['sessions']],'skipped':plan['skipped'],'basePreserved':True}

def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='command',required=True)
    p=sub.add_parser('init');p.add_argument('--base',required=True)
    p=sub.add_parser('prepare');p.add_argument('--base',required=True);p.add_argument('--hours',type=int,default=24)
    p=sub.add_parser('confirm');p.add_argument('--session',required=True);p.add_argument('--notice-sha256',required=True);p.add_argument('--explicit-request',action='store_true')
    p=sub.add_parser('status');p.add_argument('--session',required=True)
    p=sub.add_parser('run');p.add_argument('--session',required=True);p.add_argument('--kind',choices=['birth','event'],required=True);p.add_argument('arguments',nargs=argparse.REMAINDER)
    for action in ['plan','cleanup']:
        p=sub.add_parser(action);p.add_argument('--base',required=True);p.add_argument('--session-id');p.add_argument('--include-active',action='store_true')
        if action=='cleanup':p.add_argument('--plan-sha256',required=True)
    a=parser.parse_args()
    try:
        if a.command=='init':value=init_root(a.base)
        elif a.command=='prepare':value=prepare(a.base,a.hours)
        elif a.command=='confirm':value=confirm(a.session,a.notice_sha256,a.explicit_request)
        elif a.command=='status':
            record=load_session(a.session);value={'valid':True,'session':record['path'],'expiresAt':record['expiresAt']}
        elif a.command=='run':value=run(a.session,a.kind,a.arguments[1:] if a.arguments[:1]==['--'] else a.arguments)
        elif a.command=='plan':value=cleanup_plan(a.base,a.session_id,a.include_active)
        else:value=cleanup(a.base,a.plan_sha256,a.session_id,a.include_active)
        print(json.dumps(value,ensure_ascii=False,indent=2));return 0
    except (ValueError,OSError,subprocess.SubprocessError):
        print(json.dumps({'ok':False,'message':'私有会谈操作未完成；检查明确同意、目录权限、有效期或清理清单。若清理被中断，部分工件可能已经删除，请重新预览剩余文件；不要扩大范围或绕过检查。'},ensure_ascii=False),file=sys.stderr);return 1
if __name__=='__main__':
    if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf-8');sys.stderr.reconfigure(encoding='utf-8')
    raise SystemExit(main())
