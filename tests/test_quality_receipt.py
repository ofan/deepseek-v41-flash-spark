"""Keep the partial local quality result separate from official benchmarks."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class QualityReceiptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.receipt = json.loads((ROOT / 'docs/benchmarks/2026-11-14-quality.json').read_text())

    def test_existing_suite_counts_and_score(self):
        result = self.receipt['steering_on']
        rows = result['requests']
        self.assertEqual(len(rows), 14)
        self.assertEqual(result['score']['total'], 14)
        self.assertEqual(result['score']['passed'], sum(r['passed'] for r in rows))
        for group, count in [('adoption', 6), ('needles', 2), ('p5-capability', 6)]:
            self.assertEqual(sum(r['group'] == group for r in rows), count)
        for row in rows:
            self.assertRegex(row['prompt_sha256'], r'^[a-f0-9]{64}$')
            self.assertRegex(row['answer_sha256'], r'^[a-f0-9]{64}$')
            self.assertNotIn('content', row)
            self.assertNotIn('prompt', row)

    def test_missing_off_is_not_a_zero_or_historical_score(self):
        self.assertEqual(self.receipt['steering_off']['status'], 'not_run')
        self.assertIsNone(self.receipt['steering_off']['score'])
        self.assertIsNone(self.receipt['on_minus_off_percentage_points'])
        self.assertFalse(self.receipt['engine_restarted'])
        self.assertFalse(self.receipt['serving_settings_changed'])

    def test_official_reference_is_not_comparable(self):
        self.assertFalse(self.receipt['official_comparison_is_matching'])
        self.assertIsNone(self.receipt['official_minus_local_percentage_points'])
        official = self.receipt['official_reference']
        self.assertEqual(official['score_percent'], 42.6)
        self.assertEqual(official['text_only_subset_percent'], 44.0)
        self.assertEqual(official['http_status'], 200)
        self.assertTrue(official['source_url'].startswith('https://huggingface.co/deepseek-ai/'))

    def test_same_quality_settings_with_clock_cap_on(self):
        settings = self.receipt['settings']
        self.assertEqual(settings['concurrency'], 1)
        self.assertEqual(settings['graphics_clock_cap_mhz'], 2200)
        self.assertTrue(settings['existing_prompts_unchanged'])
        self.assertEqual(settings['adoption']['max_tokens'], 128)
        self.assertEqual(settings['adoption']['seed'], 42)
        self.assertEqual(settings['p5']['max_tokens'], 8192)
        self.assertEqual(settings['p5']['reasoning_effort'], 'high')

    def test_docs_disclose_partial_comparison(self):
        readme = (ROOT / 'README.md').read_text()
        details = (ROOT / 'docs/benchmarks.md').read_text()
        self.assertIn('The requested fresh OFF/ON comparison remains incomplete.', readme)
        self.assertIn('non-matching reference', readme)
        self.assertIn('No clock\nunlock, engine restart', details)
        condition = '**Benchmarks measured with every GPU capped at 2,200 MHz (graphics clock).**'
        self.assertIn(condition, readme)
        self.assertIn(condition, details)


if __name__ == '__main__':
    unittest.main()
