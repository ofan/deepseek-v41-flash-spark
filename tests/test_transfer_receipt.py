"""Offline consistency checks for the published private mirror receipt (not live proofs)."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class TransferReceiptTests(unittest.TestCase):
    def setUp(self):
        self.transfer = json.loads((ROOT / 'docs/ghcr-transfer.json').read_text())
        self.manifest = json.loads((ROOT / 'docs/production-manifest.json').read_text())
        self.success = self.transfer['attempts'][-1]

    def test_historical_failures_preserved(self):
        self.assertEqual([a['copy_exit_code'] for a in self.transfer['attempts'][:2]], [1, 1])
        self.assertEqual(self.transfer['attempts'][0]['package_after']['http_status'], 404)

    def test_exact_manifest_and_config_readback(self):
        self.assertTrue(self.transfer['package_manifest_published'])
        self.assertEqual(self.success['result'], 'PASS')
        self.assertTrue(self.success['manifest_bytes_equal'])
        self.assertTrue(self.success['config_readback_verified'])
        self.assertEqual(self.success['source_digest'], self.manifest['manifest_digest'])
        self.assertEqual(self.success['destination_digest'], self.manifest['manifest_digest'])
        self.assertEqual(self.success['config_digest'], self.manifest['config_digest'])
        self.assertEqual(self.success['layer_count'], self.manifest['layer_count'])
        self.assertEqual(self.success['compressed_layer_bytes'], self.manifest['compressed_layer_bytes'])
        self.assertTrue(self.manifest['ghcr_copy_completed'])

    def test_complete_unique_blob_receipt(self):
        blobs = self.success['blobs']
        self.assertEqual(len(blobs), 69)
        self.assertEqual(len({b['digest'] for b in blobs}), len(blobs))
        self.assertEqual(self.success['descriptor_head_checks'], len(blobs))
        for blob in blobs:
            self.assertRegex(blob['digest'], r'^sha256:[a-f0-9]{64}$')
            self.assertGreater(blob['size'], 0)
            self.assertGreaterEqual(blob['source_bytes_transferred'], 0)
            self.assertLessEqual(blob['source_bytes_transferred'], blob['size'])

    def test_independent_private_readback(self):
        verification = self.transfer['independent_readback']
        self.assertEqual(verification['package']['http_status'], 200)
        self.assertEqual(verification['package']['visibility'], 'private')
        self.assertTrue(verification['repository']['private'])
        self.assertEqual(verification['package']['version_digest'], self.manifest['manifest_digest'])
        self.assertEqual(len(verification['manifest_checks']), 2)
        for check in verification['manifest_checks']:
            self.assertTrue(check['raw_bytes_match'])
            self.assertEqual(check['digest'], self.manifest['manifest_digest'])

    def test_no_infrastructure_or_visibility_change(self):
        self.assertFalse(self.transfer['visibility_changed'])
        self.assertFalse(self.transfer['credentials_written_to_disk'])
        self.assertFalse(self.success['proxy_or_serving_changes'])
        self.assertFalse(self.success['visibility_changes'])
        self.assertFalse(self.transfer['diagnosis']['underlying_shared_relay_limit_changed'])

    def test_chunk_limit_fix_recorded(self):
        diagnosis = self.transfer['diagnosis']
        self.assertEqual(diagnosis['relay_termination']['reason'], 'OOMKilled')
        self.assertEqual(diagnosis['ghcr_chunk_limit']['fixed_max_patch_bytes'], 4 * 1024 * 1024)
        self.assertEqual(diagnosis['ghcr_chunk_limit']['status'], 416)

if __name__ == '__main__':
    unittest.main()
