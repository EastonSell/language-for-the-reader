"""Independent exhaustive regression assertions."""
import itertools
import unittest
import control

class ExhaustiveRegression(unittest.TestCase):
    def test_rows_and_split_are_unique_and_exhaustive(self):
        rows = control.evaluate()
        keys = [(r['policy'], tuple(r['known'])) for r in rows]
        profiles = set(itertools.combinations(range(4), 2))
        self.assertEqual(len(rows), 12)
        self.assertEqual(len(set(keys)), 12)
        self.assertEqual(set(keys), {(p, k) for p in ('lookup','oracle') for k in profiles})
        exposed = {tuple(r['known']) for r in rows if r['split']=='exposed'}
        unseen = {tuple(r['known']) for r in rows if r['split']=='unexposed'}
        self.assertEqual((len(exposed),len(unseen)), (4,2))
        self.assertFalse(exposed & unseen)
        self.assertEqual(exposed | unseen, profiles)
        self.assertTrue(all(r['split'] in ('exposed','unexposed') for r in rows))

    def test_all_denominators_and_pair_means(self):
        rows = control.evaluate()
        expected = {
            ('lookup','exposed'): (4,4,4,1.0,1.0),
            ('lookup','unexposed'): (2,2,0,0.5,0.0),
            ('oracle','exposed'): (4,4,4,1.0,1.0),
            ('oracle','unexposed'): (2,2,2,1.0,1.0),
        }
        for (policy,split), (n,valid,exact,recall,sel) in expected.items():
            group = [r for r in rows if r['policy']==policy and r['split']==split]
            self.assertEqual((len(group),sum(r['valid'] for r in group),sum(r['exact'] for r in group)),(n,valid,exact))
            self.assertEqual(sum(r['recall'] for r in group)/n,recall)
            self.assertEqual(sum(r['selectivity'] for r in group)/n,sel)
        pairs = [((0,1),(2,3)),((0,2),(1,3)),((0,3),(1,2))]
        for policy in ('lookup','oracle'):
            for a,b in pairs:
                group = [r for r in rows if r['policy']==policy and tuple(r['known']) in (a,b)]
                self.assertEqual(len(group),2)
                self.assertEqual(sum(r['selectivity'] for r in group)/2,
                                 0 if policy=='lookup' and a==(0,3) else 1)

if __name__ == '__main__': unittest.main()
