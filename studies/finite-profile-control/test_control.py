import unittest
import control

class ControlTest(unittest.TestCase):
    def test_lookup_generalization_counterexample(self):
        rows = control.evaluate()
        lookup = [r for r in rows if r['policy'] == 'lookup']
        self.assertEqual(len(lookup), 6)
        self.assertEqual(sum(r['exact'] for r in lookup if r['split']=='exposed'), 4)
        self.assertEqual(sum(r['exact'] for r in lookup if r['split']=='unexposed'), 0)
        self.assertEqual(sum(r['selectivity'] for r in lookup if r['split']=='unexposed'), 0)
    def test_oracle_and_invalid_accounting(self):
        rows = control.evaluate()
        self.assertTrue(all(r['exact'] == 1 for r in rows if r['policy']=='oracle'))
        self.assertEqual(control.score((0,1), (0,0)), (False, 0, 0, 0))
        self.assertEqual(control.score((0,1), (2,4)), (False, 0, 0, 0))

if __name__ == '__main__': unittest.main()
