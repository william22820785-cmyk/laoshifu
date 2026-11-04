from pathlib import Path
import importlib.util, json, shutil, socket, subprocess, sys, tempfile, unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
def preview():
    spec=importlib.util.spec_from_file_location('culture_preview', ROOT/'scripts/preview_examples.py')
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value
class CulturalWelcomeTests(unittest.TestCase):
    def test_cultural_exploration_is_offline_and_does_not_create_a_personal_session(self):
        m=preview()
        before={p.relative_to(ROOT):p.read_bytes() for p in (ROOT/'references').glob('CULTURAL-WELCOME.*.md')}
        with patch.object(socket.socket,'connect',side_effect=AssertionError('No network')):
            for lang in ('zh','en','es','pt'):
                self.assertGreater(len(m.render_welcome(ROOT,lang)),400)
        self.assertEqual(before,{p.relative_to(ROOT):p.read_bytes() for p in (ROOT/'references').glob('CULTURAL-WELCOME.*.md')})
    def test_stale_or_noncompliant_welcome_audit_stops_preview(self):
        for change in ('text','ratio'):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as temp:
                root=Path(temp);(root/'references/cultural-noun-audits').mkdir(parents=True)
                text=root/'references/CULTURAL-WELCOME.en.md';ledger=root/'references/cultural-noun-audits/en.json'
                shutil.copy2(ROOT/'references/CULTURAL-WELCOME.en.md',text)
                shutil.copy2(ROOT/'references/cultural-noun-audits/en.json',ledger)
                if change=='text':text.write_text(text.read_text(encoding='utf-8')+' changed',encoding='utf-8')
                else:
                    value=json.loads(ledger.read_text(encoding='utf-8'))
                    for noun in value['nouns']:noun['technical']=True
                    ledger.write_text(json.dumps(value),encoding='utf-8')
                with self.assertRaises(ValueError):preview().render_welcome(root,'en')
    def test_regional_tags_and_invalid_or_missing_welcome(self):
        m=preview();self.assertEqual(m.render_welcome(ROOT,'pt-BR'),m.render_welcome(ROOT,'pt'))
        for lang in ('../en','xx',''):
            with self.assertRaises(ValueError):m.render_welcome(ROOT,lang)
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(ValueError):m.render_welcome(Path(temp),'en')
    def test_both_distribution_entrypoints_have_a_standalone_welcome(self):
        for folder in (ROOT,ROOT/'skill'):
            for lang in ('en','zh','es','pt-BR'):
                p=subprocess.run([sys.executable,str(folder/'scripts/preview_examples.py'),'--welcome','--lang',lang],capture_output=True,encoding='utf-8')
                self.assertEqual(p.returncode,0,p.stderr);self.assertGreater(len(p.stdout),400)
                base_lang=lang.split('-')[0]
                self.assertEqual(p.stdout,(folder/'references'/f'CULTURAL-WELCOME.{base_lang}.md').read_text(encoding='utf-8'))
        for lang in ('zh','en','es','pt'):
            rel=Path('references')/f'CULTURAL-WELCOME.{lang}.md'
            self.assertEqual((ROOT/rel).read_bytes(),(ROOT/'skill'/rel).read_bytes())
if __name__=='__main__':unittest.main()
