import unittest
import numpy as np
from search_ratio_bounds import make_pairs, search_reciprocal

class GridSearchTests(unittest.TestCase):
    def test_pair_count_and_order(self):
        pairs=make_pairs(100)
        self.assertEqual(len(pairs),5050)
        self.assertTrue(np.all(pairs[:,0]<pairs[:,1]))
    def test_negative_to_positive_grid_includes_zero(self):
        pairs=make_pairs(200,-1,1)
        self.assertEqual(len(pairs),20100)
        self.assertEqual(float(pairs.min()),-1)
        self.assertEqual(float(pairs.max()),1)
        self.assertTrue(np.any(pairs==0))
    def test_negative_grid_matches_naive(self):
        pairs=make_pairs(4,-1,1);x=np.array([.2,.8]);y=np.array([.4,.6]);atol=.2
        expected=[]
        for i,(lo,hi) in enumerate(pairs):
            for j,(lo2,hi2) in enumerate(pairs):
                if all(abs((lo+(hi-lo)*a)*(lo2+(hi2-lo2)*b)-1)<=atol for a,b in zip(x,y)):expected.append((i,j))
        self.assertEqual(sorted(search_reciprocal(x,y,pairs,atol,block_size=3)['survivors']),expected)
    def test_search_matches_naive_enumeration(self):
        pairs=make_pairs(4);x=np.array([.2,.8]);y=np.array([.4,.6]);atol=.2
        expected=[]
        for i,(lo,hi) in enumerate(pairs):
            for j,(lo2,hi2) in enumerate(pairs):
                if all(abs((lo+(hi-lo)*a)*(lo2+(hi2-lo2)*b)-1)<=atol for a,b in zip(x,y)):expected.append((i,j))
        result=search_reciprocal(x,y,pairs,atol,block_size=3)
        self.assertEqual(sorted(result['survivors']),expected)
        self.assertEqual(result['tested_combinations'],len(pairs)**2)
    def test_satisfiable_case_not_accidentally_rejected(self):
        result=search_reciprocal(np.array([1.,1.]),np.array([1.,1.]),make_pairs(10),1e-8)
        self.assertEqual(len(result['survivors']),100)
    def test_one_failure_rules_out_all_rows(self):
        result=search_reciprocal(np.array([0.,1.]),np.array([0.,1.]),make_pairs(10),1e-8)
        self.assertEqual(result['survivors'],[])

if __name__=='__main__':unittest.main()
