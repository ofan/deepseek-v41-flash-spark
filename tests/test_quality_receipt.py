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

    def test_local_acceptance_is_not_a_standardized_score(self):
        planned = json.loads((ROOT / 'docs/benchmarks/2026-11-14-standardized-quality.json').read_text())
        self.assertEqual(planned['status'], 'source_output_budget_fixed_live_run_pending')
        self.assertEqual(planned['samples_run'], 0)
        self.assertEqual(planned['dataset']['http_status'], 200)
        self.assertTrue(planned['dataset']['staged'])
        self.assertEqual(planned['dataset']['actual_text_samples'], 2158)
        self.assertEqual(planned['dataset']['actual_total_samples'], 2500)
        self.assertRegex(planned['dataset']['parquet_sha256'], r'^[a-f0-9]{64}$')
        self.assertRegex(planned['dataset']['text_jsonl_sha256'], r'^[a-f0-9]{64}$')
        self.assertFalse(planned['dataset']['questions_or_answers_published'])
        self.assertFalse(planned['adapter']['evaluator_sources_changed'])
        self.assertEqual(planned['adapter']['actual_hle_generation_requests'], 0)
        self.assertEqual(planned['adapter']['default_concurrency'], 1)
        self.assertIsNone(planned['recipe_score_percent'])
        self.assertIsNone(planned['recipe_minus_official_percentage_points'])
        self.assertIsNone(planned['raw_result'])
        self.assertEqual(planned['official_score_percent'], 44.0)
        self.assertFalse(planned['serving_changed'])
        self.assertFalse(planned['clock_settings_changed'])
        self.assertFalse(planned['engine_restarted'])
        self.assertFalse(planned['new_eval_prompts_authored'])

    def test_blocker_is_the_output_cap_not_dataset_access(self):
        planned = json.loads((ROOT / 'docs/benchmarks/2026-11-14-standardized-quality.json').read_text())
        probes = planned['diagnostic_probes']
        self.assertEqual(probes['scored_samples'], 0)
        self.assertEqual(probes['requests'], 9)
        self.assertEqual(probes['ended_at_cap_with_no_content'], 5)
        self.assertEqual(probes['ended_with_answer'], 4)
        self.assertEqual(probes['settings']['max_tokens'], 32768)
        self.assertFalse(probes['published'])
        self.assertEqual(probes['projection']['status'], 'withdrawn_not_an_isolated_runtime_estimate')
        fix=planned['source_output_budget_fix']
        self.assertEqual(fix['default_max_output_tokens'],262144)
        self.assertFalse(fix['live_deployed'])
        self.assertFalse(fix['public_image_rebuilt'])
        isolation = planned['isolation']
        self.assertFalse(isolation['admission_pause_applied'])
        self.assertEqual(isolation['scored_samples_requiring_rerun'], 0)
        self.assertEqual(planned['generation_setting_preflight']['pinned_frontend_compiled_default_max_output_tokens'], 32768)
        self.assertFalse(planned['generation_setting_preflight']['judge_model_frozen'])

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

    def test_docs_separate_standardized_quality_from_acceptance(self):
        readme = (ROOT / 'README.md').read_text()
        details = (ROOT / 'docs/benchmarks.md').read_text()
        quality = readme.split('## Quality\n', 1)[1].split('## Requirements\n', 1)[0]
        self.assertIn('No recipe quality score or point delta is claimed.', quality)
        self.assertIn('Not measured', quality)
        self.assertIn('2,158 text-only', quality)
        self.assertIn('32,768', quality)
        self.assertIn('262,144-token',quality)
        self.assertIn('not a deployed production change',quality)
        self.assertIn('disclosed',quality)
        self.assertIn('Serving acceptance check', quality)
        self.assertNotIn('Steering OFF', quality)
        self.assertNotIn('OFF/ON', quality)
        self.assertNotIn('blocked', quality.lower())
        self.assertIn('Run status: not run; samples 0', details)
        self.assertIn('HLE w/o tools | 42.6 full; **44.0 text-only**', details)
        condition = '**Benchmarks measured with every GPU capped at 2,200 MHz (graphics clock).**'
        self.assertIn(condition, readme)
        self.assertIn(condition, details)

    def test_existing_hle_runner_blocker_has_evidence(self):
        planned = json.loads((ROOT / 'docs/benchmarks/2026-11-14-standardized-quality.json').read_text())
        readiness = planned['readiness']
        self.assertFalse(readiness['generation_http_endpoint_option'])
        self.assertTrue(readiness['generation_creates_local_engine'])
        self.assertFalse(readiness['default_dataset_staged'])
        self.assertEqual(readiness['defaults']['expert_parallelism'], 8)
        self.assertEqual(readiness['defaults']['max_num_seqs'], 384)
        for value in readiness['source_file_sha256'].values():
            self.assertRegex(value, r'^[a-f0-9]{64}$')


if __name__ == '__main__':
    unittest.main()
