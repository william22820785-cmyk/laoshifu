from pathlib import Path
import importlib.util,json,tempfile,shutil,unittest,socket,subprocess,sys
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/'scripts/preview_examples.py'
def module():
 spec=importlib.util.spec_from_file_location('preview',SCRIPT);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
class PreviewTests(unittest.TestCase):
 def test_preview_works_offline_and_does_not_change_source(self):
  m=module();before={p.relative_to(ROOT/'examples').as_posix():p.read_bytes() for p in (ROOT/'examples').rglob('*') if p.is_file()}
  with patch.object(socket.socket,'connect',side_effect=AssertionError('No networking')):
   text=m.render(ROOT/'examples','contract')
  self.assertIn('模拟',text);self.assertIn('不发起付款',text);self.assertIn('推进',text)
  self.assertEqual(before,{p.relative_to(ROOT/'examples').as_posix():p.read_bytes() for p in (ROOT/'examples').rglob('*') if p.is_file()})
 def test_birth_does_not_request_user_data(self):
  self.assertIn('不是对你的个人判断',module().render(ROOT/'examples','birth'))
 def test_missing_or_corrupt_file_fail_closed(self):
  for mutation in ['missing','corrupt']:
   with self.subTest(mutation=mutation),tempfile.TemporaryDirectory() as tmp:
    p=Path(tmp)/'examples';shutil.copytree(ROOT/'examples',p);f=p/'contract/source.json'
    if mutation=='missing':f.unlink()
    else:f.write_text('{}',encoding='utf-8')
    with self.assertRaises(ValueError):module().render(p,'contract')
 def test_traversal_manifest_rejected(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'examples';shutil.copytree(ROOT/'examples',p);f=p/'manifest.json';d=json.loads(f.read_text(encoding='utf-8'));d['examples'][0]['files'][0]['path']='../secret.txt';f.write_text(json.dumps(d),encoding='utf-8')
   with self.assertRaises(ValueError):module().render(p,'birth')
 def test_unknown_id_and_missing_manifest_rejected(self):
  with self.assertRaises(ValueError):module().render(ROOT/'examples','does-not-exist')
  with tempfile.TemporaryDirectory() as tmp:
   with self.assertRaises(ValueError):module().render(Path(tmp),'birth')
 def test_cli_success_and_unknown_example(self):
  for channel in ['.','skill']:
   p=subprocess.run([sys.executable,str(ROOT/channel/'scripts/preview_examples.py'),'--list'],capture_output=True,text=True,encoding='utf-8')
   self.assertEqual(p.returncode,0,p.stderr);self.assertIn('contract',p.stdout)
   p=subprocess.run([sys.executable,str(ROOT/channel/'scripts/preview_examples.py'),'--example','bogus'],capture_output=True,text=True,encoding='utf-8')
   self.assertNotEqual(p.returncode,0);self.assertNotIn('Traceback',p.stderr)
 def test_preview_is_same_in_both_editions(self):
  self.assertEqual(SCRIPT.read_bytes(),(ROOT/'skill/scripts/preview_examples.py').read_bytes())
  for p in (ROOT/'examples').rglob('*'):
   if p.is_file():self.assertEqual(p.read_bytes(),(ROOT/'skill/examples'/p.relative_to(ROOT/'examples')).read_bytes())
if __name__=='__main__':unittest.main()
