from pathlib import Path
import importlib.util, json, shutil, socket, subprocess, sys, tempfile, unittest
from datetime import datetime
from unittest.mock import patch
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import birth_location

def preview():
    spec = importlib.util.spec_from_file_location('preview_i18n', ROOT / 'scripts/preview_examples.py')
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result

class InternationalPreviewTests(unittest.TestCase):
    def test_translations_run_offline_without_writes(self):
        root = ROOT / 'examples'
        before = {p.relative_to(root): p.read_bytes() for p in root.rglob('*') if p.is_file()}
        for lang in ('en', 'es', 'pt'):
            with self.subTest(lang=lang), patch.object(socket.socket, 'connect', side_effect=AssertionError('network')):
                for key in ('birth', 'contract'):
                    text = preview().render(root, key, lang)
                    self.assertGreater(len(text), 800)
                    self.assertNotIn('【固定示例', text)
        self.assertEqual(before, {p.relative_to(root): p.read_bytes() for p in root.rglob('*') if p.is_file()})

    def test_language_variants_resolve_and_unknown_language_fails(self):
        for variant, base in [('en-US', 'en'), ('es-MX', 'es'), ('pt-BR', 'pt'), ('zh-CN', 'zh')]:
            self.assertEqual(preview().render(ROOT/'examples', 'birth', variant), preview().render(ROOT/'examples', 'birth', base))
        for lang in ('de', '../en', '', 'en/../../secret'):
            with self.subTest(lang=lang), self.assertRaises(ValueError):
                preview().render(ROOT/'examples', 'birth', lang)

    def test_corrupt_or_missing_translation_fails_without_fallback(self):
        for action in ('missing', 'changed', 'source-drift', 'traversal', 'bad-shape'):
            with self.subTest(action=action), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)/'examples'
                shutil.copytree(ROOT/'examples', root)
                path = root/'translations/en/birth.txt'
                manifest_path = root/'translations/manifest.json'
                manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
                if action == 'missing': path.unlink()
                elif action == 'changed': path.write_text('a different claim', encoding='utf-8')
                elif action == 'source-drift':
                    source = root/'manifest.json'
                    source.write_bytes(source.read_bytes() + b' ')
                elif action == 'traversal':
                    manifest['locales']['en']['examples'][0]['response'] = '../secret.txt'
                    manifest_path.write_text(json.dumps(manifest), encoding='utf-8')
                else:
                    manifest['locales']['en'] = []
                    manifest_path.write_text(json.dumps(manifest), encoding='utf-8')
                with self.assertRaises(ValueError): preview().render(root, 'birth', 'en')

    def test_both_entrypoints_support_translated_cli(self):
        for folder in (ROOT, ROOT/'skill'):
            for lang in ('en-US', 'es', 'pt-BR'):
                result = subprocess.run([sys.executable, str(folder/'scripts/preview_examples.py'), '--lang', lang, '--example', 'contract'], capture_output=True, encoding='utf-8')
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertGreater(len(result.stdout), 1500)
            result = subprocess.run([sys.executable, str(folder/'scripts/preview_examples.py'), '--lang', 'de'], capture_output=True, encoding='utf-8')
            self.assertNotEqual(result.returncode, 0)
            self.assertNotIn('Traceback', result.stderr)

class DistributionTests(unittest.TestCase):
    def test_private_session_entrypoint_is_shipped_in_both_editions(self):
        for folder in (ROOT, ROOT/'skill'):
            result = subprocess.run([sys.executable, str(folder/'scripts/session_store.py'), '--help'], capture_output=True, encoding='utf-8')
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((folder/'references/SESSION-PRIVACY.md').is_file())

class InternationalTimeTests(unittest.TestCase):
    def test_historical_dst_offsets(self):
        ny = birth_location.resolve_birthplace('New York, USA')
        self.assertEqual(birth_location.utc_offset_hours(datetime(1990, 1, 15, 10), ny), -5)
        self.assertEqual(birth_location.utc_offset_hours(datetime(1990, 7, 15, 10), ny), -4)

    def test_dst_gap_and_repeated_hour_require_resolution(self):
        ny = birth_location.resolve_birthplace('New York, USA')
        for value in (datetime(2024, 3, 10, 2, 30), datetime(2024, 11, 3, 1, 30)):
            with self.subTest(value=value), self.assertRaises(ValueError):
                birth_location.utc_offset_hours(value, ny)

    def test_fractional_event_offsets_reach_both_engines(self):
        for offset in (5.5, 5.75):
            with self.subTest(offset=offset), tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp)/'fusion.json'
                result = subprocess.run([sys.executable, str(ROOT/'scripts/liuyao_qimen_fusion.py'), '--question=Will the contract be signed this month?', '--category=career', '--method=numbers', '--numbers=12,35,8', '--year=2026', '--month=11', '--day=2', '--hour=9', '--minute=30', f'--timeZone={offset}', f'--output={path}'], capture_output=True, encoding='utf-8')
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertTrue(path.is_file())
                data = json.loads(path.read_text(encoding='utf-8'))
                self.assertEqual(data['timeBasis'], 'local')
                self.assertEqual(data['eventTime']['timeZone'], offset)
                self.assertEqual(data['eventTime']['utc'], '2026-11-02T04:00:00.000Z' if offset == 5.5 else '2026-11-02T03:45:00.000Z')

if __name__ == '__main__': unittest.main()
