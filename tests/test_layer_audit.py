"""Offline audit receipt consistency; not a substitute for registry readback."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class LayerAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.audit = json.loads((ROOT / 'docs/layer-audit.json').read_text())
        cls.manifest = json.loads((ROOT / 'docs/production-manifest.json').read_text())

    def test_complete_descriptor_inventory(self):
        a = self.audit
        self.assertEqual(a['manifest_digest'], self.manifest['manifest_digest'])
        self.assertEqual(a['config_digest'], self.manifest['config_digest'])
        self.assertEqual(a['layer_descriptors_checked'], self.manifest['layer_count'])
        self.assertEqual([x['ordinal'] for x in a['layers']], list(range(1, 73)))
        self.assertEqual(len({x['digest'] for x in a['layers']}), 68)
        for layer in a['layers']:
            self.assertRegex(layer['index_sha256'], r'^sha256:[0-9a-f]{64}$')
            self.assertIn(layer['verdict'], ['BLOCKED', 'REVIEW', 'NO_FINDING_IN_SCOPE'])

    def test_failed_publication_gate_keeps_both_private(self):
        a = self.audit
        self.assertEqual(a['verdict'], 'BLOCKED')
        self.assertFalse(a['publication_allowed'])
        self.assertFalse(a['visibility_changed'])
        self.assertEqual(a['package_visibility'], 'private')
        self.assertEqual(a['repository_visibility'], 'private')
        self.assertEqual(a['final_readback']['package']['visibility'], 'private')
        self.assertTrue(a['final_readback']['repository']['private'])
        self.assertEqual(a['final_readback']['package']['version_digest'], a['manifest_digest'])

    def test_historical_profiles_not_hidden_by_overwrite(self):
        profiles = [x for x in self.audit['confirmed_file_findings'] if x['path'] == 'opt/pico/profile.json']
        self.assertEqual([x['layer'] for x in profiles], [60, 63, 66, 68, 70])
        self.assertTrue(all('internal-domain' in x['kinds'] for x in profiles))
        launchers = [x for x in self.audit['confirmed_file_findings'] if x['path'] == 'opt/pico/entrypoint.py']
        self.assertEqual([x['layer'] for x in launchers], [60, 69])

    def test_confirmed_findings_reference_audited_layers(self):
        layers = {l['ordinal']: l for l in self.audit['layers']}
        self.assertEqual(len(self.audit['confirmed_file_findings']), 61)
        for finding in self.audit['confirmed_file_findings']:
            layer = layers[finding['layer']]
            self.assertEqual(finding['digest'], layer['digest'])
            self.assertEqual(layer['verdict'], 'BLOCKED')
            self.assertNotIn('value', finding)
        self.assertEqual(len(self.audit['config_field_inventory']), self.audit['config_fields_inspected'])
        self.assertEqual(self.audit['config_runtime_summary']['User'], 'root')
        self.assertEqual(len(self.audit['config_runtime_summary']['Env_names']), 27)

    def test_read_only_bounded_method_recorded(self):
        limits = self.audit['limits']
        self.assertFalse(limits['tensor_or_tokenizer_members_opened'])
        self.assertFalse(limits['archives_extracted_to_filesystem'])
        self.assertFalse(limits['containers_executed'])
        self.assertEqual(limits['max_text_bytes'], 512 * 1024)
        text = (ROOT / 'docs/layer-audit.md').read_text()
        self.assertIn('REVIEW is not clearance', text)
        self.assertIn('No flip', text)

if __name__ == '__main__':
    unittest.main()
