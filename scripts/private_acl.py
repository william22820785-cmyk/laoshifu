"""Read actual Windows owner/DACL using Win32; no ACL mutation or file contents."""
import ctypes
from ctypes import wintypes as W
from functools import lru_cache

class AclError(ValueError):pass

@lru_cache(maxsize=1)
def _api():
    adv=ctypes.WinDLL('advapi32',use_last_error=True);kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    adv.ConvertSidToStringSidW.argtypes=[W.LPVOID,ctypes.POINTER(W.LPWSTR)];adv.ConvertSidToStringSidW.restype=W.BOOL
    adv.GetNamedSecurityInfoW.argtypes=[W.LPWSTR,ctypes.c_int,W.DWORD,ctypes.POINTER(W.LPVOID),ctypes.POINTER(W.LPVOID),ctypes.POINTER(W.LPVOID),ctypes.POINTER(W.LPVOID),ctypes.POINTER(W.LPVOID)];adv.GetNamedSecurityInfoW.restype=W.DWORD
    adv.GetAce.argtypes=[W.LPVOID,W.DWORD,ctypes.POINTER(W.LPVOID)];adv.GetAce.restype=W.BOOL
    adv.GetSecurityDescriptorControl.argtypes=[W.LPVOID,ctypes.POINTER(W.WORD),ctypes.POINTER(W.DWORD)];adv.GetSecurityDescriptorControl.restype=W.BOOL
    adv.OpenProcessToken.argtypes=[W.HANDLE,W.DWORD,ctypes.POINTER(W.HANDLE)];adv.OpenProcessToken.restype=W.BOOL
    adv.GetTokenInformation.argtypes=[W.HANDLE,ctypes.c_int,W.LPVOID,W.DWORD,ctypes.POINTER(W.DWORD)];adv.GetTokenInformation.restype=W.BOOL
    kernel.GetCurrentProcess.restype=W.HANDLE;kernel.LocalFree.argtypes=[W.HLOCAL];kernel.LocalFree.restype=W.HLOCAL
    kernel.CloseHandle.argtypes=[W.HANDLE];kernel.CloseHandle.restype=W.BOOL
    return adv,kernel

def _sid_text(pointer):
    adv,kernel=_api();text=W.LPWSTR()
    if not adv.ConvertSidToStringSidW(pointer,ctypes.byref(text)):raise AclError('SID读取失败')
    try:return text.value
    finally:kernel.LocalFree(ctypes.cast(text,W.HLOCAL))

@lru_cache(maxsize=1)
def current_sid():
    adv,kernel=_api();token=W.HANDLE();size=W.DWORD()
    if not adv.OpenProcessToken(kernel.GetCurrentProcess(),8,ctypes.byref(token)):raise AclError('用户令牌读取失败')
    try:
        adv.GetTokenInformation(token,1,None,0,ctypes.byref(size));buffer=ctypes.create_string_buffer(size.value)
        if not adv.GetTokenInformation(token,1,buffer,size.value,ctypes.byref(size)):raise AclError('用户SID读取失败')
        pointer=ctypes.cast(buffer,ctypes.POINTER(W.LPVOID)).contents.value
        return _sid_text(pointer)
    finally:kernel.CloseHandle(token)

def verify_private(path,is_directory=False):
    adv,kernel=_api();owner=W.LPVOID();dacl=W.LPVOID();descriptor=W.LPVOID()
    error=adv.GetNamedSecurityInfoW(str(path),1,5,ctypes.byref(owner),None,ctypes.byref(dacl),None,ctypes.byref(descriptor))
    if error or not descriptor:raise AclError('权限读取失败')
    try:
        user=current_sid()
        if not owner or _sid_text(owner)!=user or not dacl:raise AclError('非当前用户私有文件')
        control=W.WORD();revision=W.DWORD()
        if not adv.GetSecurityDescriptorControl(descriptor,ctypes.byref(control),ctypes.byref(revision)):raise AclError('DACL状态读取失败')
        if is_directory and not control.value&0x1000:raise AclError('目录权限仍继承外部设置')
        # ACL header is revision(1), reserved(1), size(2), ace_count(2), reserved(2).
        header=ctypes.string_at(dacl,8);count=int.from_bytes(header[4:6],'little');owner_allowed=False
        for index in range(count):
            ace=W.LPVOID()
            if not adv.GetAce(dacl,index,ctypes.byref(ace)):raise AclError('ACE读取失败')
            head=ctypes.string_at(ace,4);kind=head[0];size=int.from_bytes(head[2:4],'little')
            if kind==1:continue # Denials cannot grant access.
            if kind!=0 or size<12:raise AclError('不支持的权限条目')
            identity=_sid_text(ace.value+8)
            if identity not in (user,'S-1-5-18'):raise AclError('文件可被其他身份读取')
            if identity==user:owner_allowed=True
        if not owner_allowed:raise AclError('当前用户缺少显式权限')
        return user
    finally:kernel.LocalFree(descriptor)
