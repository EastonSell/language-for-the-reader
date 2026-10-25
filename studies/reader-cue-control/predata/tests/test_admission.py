import copy
import json
from pathlib import Path
import tempfile
import unittest
import admission
import study

ROOT=Path(__file__).resolve().parents[1]

class CustodyTests(unittest.TestCase):
    def setUp(self):
        self.packets=study.build(json.loads((ROOT/'study/fixtures.json').read_text()))['packets']
        self.raw={p['block_id']:b'[]' for p in self.packets}
        self.prompts={p['block_id']:study.prompt(p).encode() for p in self.packets}
        self.receipts=[dict(block_id=p['block_id'],context_id='synthetic-context-'+str(i),
                            prompt_sha256=study.sha(self.prompts[p['block_id']]),
                            raw_sha256=study.sha(self.raw[p['block_id']]),
                            started_utc='2026-10-25T08:00:00Z',completed_utc='2026-10-25T08:01:00Z',
                            history_disabled=True,requested_reasoning_effort='xhigh',requested_model='inherited',
                            resolved_model=None,tool_audit='not_exposed',tool_calls_observed=None,
                            known_tool_use=False,known_contamination=False,
                            capture='visible_final_answer_utf8_no_added_newline') for i,p in enumerate(self.packets)]

    def check_bad(self):
        self.assertTrue(admission.validate_receipts(self.receipts,self.packets,self.raw,self.prompts))

    def test_valid_custody(self):
        self.assertEqual(admission.validate_receipts(self.receipts,self.packets,self.raw,self.prompts),[])

    def test_duplicate_context_rejected(self):
        self.receipts[1]['context_id']=self.receipts[0]['context_id']; self.check_bad()

    def test_missing_receipt_rejected(self):
        self.receipts.pop(); self.check_bad()

    def test_wrong_prompt_hash_rejected(self):
        self.receipts[0]['prompt_sha256']='0'*64; self.check_bad()

    def test_wrong_raw_hash_rejected(self):
        self.raw['B01']=b'[]\n'; self.check_bad()

    def test_no_false_zero_tool_claim(self):
        self.receipts[0]['tool_calls_observed']=0; self.check_bad()

    def test_known_tool_use_rejected(self):
        self.receipts[0]['known_tool_use']=True; self.check_bad()

    def test_known_contamination_rejected(self):
        self.receipts[0]['known_contamination']=True; self.check_bad()

    def test_history_enabled_rejected(self):
        self.receipts[0]['history_disabled']=False; self.check_bad()

    def test_global_window_rejected(self):
        self.receipts[-1]['completed_utc']='2026-10-25T08:46:00Z'; self.check_bad()

    def test_naive_or_backward_time_rejected(self):
        for value in ['2026-10-25T08:01:00','2026-10-25T07:59:59Z']:
            with self.subTest(value=value):
                self.receipts[0]['completed_utc']=value; self.check_bad()

class FreezeTests(unittest.TestCase):
    def test_mutated_payload_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp); (p/'payload.txt').write_text('before')
            result=admission.freeze(p)
            self.assertIn('payload.txt',result.get('files',{}))
            admission.verify_freeze(p)
            (p/'payload.txt').write_text('after')
            with self.assertRaises(ValueError): admission.verify_freeze(p)

    def test_existing_freeze_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp); (p/'payload.txt').write_text('before'); admission.freeze(p)
            with self.assertRaises((ValueError,FileExistsError)): admission.freeze(p)

    def test_symlink_payload_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp); (p/'payload.txt').write_text('x'); (p/'link').symlink_to('payload.txt')
            with self.assertRaises(ValueError): admission.freeze(p)

    def test_added_payload_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp); (p/'payload.txt').write_text('x'); admission.freeze(p)
            (p/'extra.txt').write_text('extra')
            with self.assertRaises(ValueError): admission.verify_freeze(p)


class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        base=Path(self.tmp.name); self.package=base/'package'; self.run=base/'synthetic-run'
        (self.package/'study').mkdir(parents=True); self.run.mkdir()
        (self.package/'study/fixtures.json').write_bytes((ROOT/'study/fixtures.json').read_bytes())
        plan=study.prepare(self.package); self.plan=plan
        admission.freeze(self.package)
        keys={x['case_id']:x for x in plan['key']}; receipts=[]
        for i,p in enumerate(plan['packets']):
            block=p['block_id']
            responses=[{'case_id':c['case_id'],'decision':'supported' if keys[c['case_id']]['gold_support'] else 'not_supported',
                        'evidence':[c['passage']] if keys[c['case_id']]['gold_support'] else [],
                        'rationale':'Synthetic oracle-shaped fixture, not a model observation.'} for c in p['cases']]
            raw=study.encoded(responses); (self.run/(block+'.raw.txt')).write_bytes(raw)
            receipts.append(dict(block_id=block,context_id='synthetic-fixture-'+str(i),
                                 prompt_sha256=study.sha(study.prompt(p).encode()),raw_sha256=study.sha(raw),
                                 started_utc='2026-10-25T08:00:00Z',completed_utc='2026-10-25T08:01:00Z',
                                 history_disabled=True,requested_reasoning_effort='xhigh',requested_model='inherited',
                                 resolved_model=None,tool_audit='not_exposed',tool_calls_observed=None,
                                 known_tool_use=False,known_contamination=False,
                                 capture='visible_final_answer_utf8_no_added_newline'))
        self.receipts=receipts
        (self.run/'receipts.json').write_bytes(study.encoded(receipts))

    def tearDown(self):
        self.tmp.cleanup()

    def test_synthetic_end_to_end_complete(self):
        result=admission.analyze_run(self.package,self.run)
        self.assertTrue(result['operational_complete'])
        self.assertEqual(result['valid_cases'],144)
        self.assertEqual(result['primary']['point_difference'],0.0)
        self.assertEqual(result['primary']['difference_bounds'],[0.0,0.0])

    def test_synthetic_bad_packet_keeps_denominator(self):
        raw=b'[]'; (self.run/'B01.raw.txt').write_bytes(raw)
        self.receipts[0]['raw_sha256']=study.sha(raw)
        (self.run/'receipts.json').write_bytes(study.encoded(self.receipts))
        result=admission.analyze_run(self.package,self.run)
        self.assertFalse(result['operational_complete'])
        self.assertEqual(result['expected_cases'],144)
        self.assertEqual(result['valid_cases'],132)
        self.assertIsNone(result['primary']['point_difference'])
        self.assertEqual(sum(c['missing_or_invalid'] for c in result['cells']),12)

    def test_synthetic_missing_custody_admits_nothing(self):
        (self.run/'receipts.json').write_bytes(study.encoded(self.receipts[:-1]))
        result=admission.analyze_run(self.package,self.run)
        self.assertFalse(result['operational_complete'])
        self.assertEqual(result['valid_cases'],0)
        self.assertEqual(result['primary']['difference_bounds'],[-1.0,1.0])

    def test_synthetic_modified_prompt_is_blocked(self):
        (self.package/'prepared/B01.prompt.txt').write_text('different')
        with self.assertRaises(ValueError): admission.analyze_run(self.package,self.run)

if __name__=='__main__':unittest.main()
