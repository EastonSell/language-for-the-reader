import copy
import json
from pathlib import Path
import unittest
import study

ROOT = Path(__file__).resolve().parents[1]


class DesignTests(unittest.TestCase):
    def setUp(self):
        self.fixtures = json.loads((ROOT / 'study/fixtures.json').read_text())

    def test_complete_grid_and_latin_balance(self):
        plan = study.build(self.fixtures)
        self.assertEqual(len(plan['packets']), 12)
        self.assertEqual(len(plan['key']), 144)
        self.assertEqual(len({x['case_id'] for x in plan['key']}), 144)
        for packet in plan['packets']:
            self.assertEqual(len(packet['cases']), 12)
            rows = [x for x in plan['key'] if x['block_id'] == packet['block_id']]
            self.assertEqual(len({x['source_id'] for x in rows}), 12)
            self.assertEqual(len({(x['variant'], x['cue']) for x in rows}), 12)
        for f in self.fixtures:
            rows = [x for x in plan['key'] if x['source_id'] == f['source_id']]
            self.assertEqual(len({(x['variant'], x['cue']) for x in rows}), 12)

    def test_inputs_are_matched_and_key_is_not_in_prompts(self):
        plan = study.build(self.fixtures)
        self.assertEqual(len(plan['key']), 144)
        cases = {c['case_id']: c for p in plan['packets'] for c in p['cases']}
        for f in self.fixtures:
            self.assertEqual(len(f['relevant_cue'].split()), len(f['unrelated_cue'].split()))
            for variant in ('literal', 'paraphrase', 'corrupted', 'empty'):
                rows = [x for x in plan['key'] if x['source_id'] == f['source_id'] and x['variant'] == variant]
                self.assertEqual(len({cases[x['case_id']]['claim'] for x in rows}), 1)
                self.assertEqual(len({cases[x['case_id']]['passage'] for x in rows}), 1)
                self.assertEqual(len(rows), 3)
                for row in rows:
                    self.assertEqual(set(cases[row['case_id']]), {'case_id', 'claim', 'passage', 'question_cue'})

    def test_duplicate_source_rejected(self):
        bad = copy.deepcopy(self.fixtures); bad[1]['source_id'] = bad[0]['source_id']
        with self.assertRaises(ValueError): study.build(bad)

    def test_missing_source_rejected(self):
        with self.assertRaises(ValueError): study.build(self.fixtures[:-1])

    def test_mismatched_cue_length_rejected(self):
        bad = copy.deepcopy(self.fixtures); bad[0]['unrelated_cue'] += ' extra'
        with self.assertRaises(ValueError): study.build(bad)


class ResponseTests(unittest.TestCase):
    def setUp(self):
        self.cases = [{'case_id':'abc', 'claim':'A red boat floats.', 'passage':'A red boat floats.', 'question_cue':''}]
        self.response = {'case_id':'abc','decision':'supported','evidence':['A red boat floats.'],'rationale':'All of the claim is stated.'}

    def check_invalid(self, raw):
        out = study.parse_responses(raw, self.cases)
        self.assertTrue(out['issues'])
        self.assertEqual(out['responses'], [])

    def test_valid_response(self):
        out = study.parse_responses(json.dumps([self.response]), self.cases)
        self.assertEqual(out['responses'], [self.response])
        self.assertEqual(out['issues'], [])

    def test_duplicate_case_invalidates_packet(self):
        self.check_invalid(json.dumps([self.response, self.response]))

    def test_missing_case_invalidates_packet(self):
        self.check_invalid('[]')

    def test_unknown_case_invalidates_packet(self):
        r = dict(self.response, case_id='other'); self.check_invalid(json.dumps([r]))

    def test_extra_field_invalidates_packet(self):
        r = dict(self.response, gold=True); self.check_invalid(json.dumps([r]))

    def test_supported_requires_quote(self):
        r = dict(self.response, evidence=[]); self.check_invalid(json.dumps([r]))

    def test_quote_must_be_passage_substring(self):
        r = dict(self.response, evidence=['The boat is red.']); self.check_invalid(json.dumps([r]))

    def test_quote_from_claim_not_passage_rejected(self):
        self.cases[0]['passage'] = ''
        self.check_invalid(json.dumps([self.response]))

    def test_nonfinite_and_duplicate_json_keys_rejected(self):
        self.check_invalid('[{"case_id":"abc","case_id":"abc","decision":NaN}]')

    def test_markdown_not_repaired(self):
        self.check_invalid('```json\n' + json.dumps([self.response]) + '\n```')

    def test_wrong_types_rejected(self):
        for field in ('case_id', 'decision', 'evidence', 'rationale'):
            with self.subTest(field=field):
                self.check_invalid(json.dumps([dict(self.response, **{field: True})]))


class AnalysisTests(unittest.TestCase):
    def setUp(self):
        self.plan = study.build(json.loads((ROOT / 'study/fixtures.json').read_text()))
        self.oracle = [{'case_id':k['case_id'], 'decision':'supported' if k['gold_support'] else 'not_supported', 'evidence':[], 'rationale':'Synthetic only.'} for k in self.plan['key']]

    def test_complete_oracle_has_zero_primary_difference(self):
        out = study.analyze(self.plan['key'], self.oracle)
        self.assertEqual(out['expected_cases'],144)
        self.assertEqual(out['valid_cases'],144)
        self.assertTrue(out['response_complete'])
        self.assertEqual(out['primary']['difference_bounds'], [0.0,0.0])

    def test_missing_is_not_scored_negative(self):
        out = study.analyze(self.plan['key'], [])
        self.assertFalse(out['response_complete'])
        self.assertEqual(out['expected_cases'],144)
        self.assertEqual(out['primary']['difference_bounds'],[-1.0,1.0])
        self.assertIsNone(out['primary']['point_difference'])

    def test_all_relevant_corrupt_positives_difference_one(self):
        for r,k in zip(self.oracle,self.plan['key']):
            if k['variant']=='corrupted' and k['cue']=='relevant': r['decision']='supported'
        out = study.analyze(self.plan['key'], self.oracle)
        self.assertEqual(out['primary']['point_difference'],1.0)

    def test_duplicate_response_rejected(self):
        with self.assertRaises(ValueError): study.analyze(self.plan['key'], self.oracle + self.oracle[:1])

    def test_key_denominator_cannot_shrink(self):
        with self.assertRaises(ValueError): study.analyze(self.plan['key'][:-1], self.oracle)

    def test_uncertain_is_reported_not_hidden(self):
        self.oracle[0]['decision']='uncertain'
        out=study.analyze(self.plan['key'],self.oracle)
        self.assertEqual(out['uncertain'],1)

if __name__=='__main__': unittest.main()
