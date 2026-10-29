import unittest
import numpy as np
from synthetic_ratio_sanity import generate_cases, verdict, feature_frame

class SanityTests(unittest.TestCase):
    def test_reproducible_and_balanced(self):
        a=generate_cases(10,42);b=generate_cases(10,42)
        self.assertEqual(a,b);self.assertEqual(len(a),50)
        for r in a:
            self.assertAlmostEqual(r['total_assets'],r['total_liabilities']+r['equity'],places=6)
            self.assertNotEqual(r['equity'],0)
    def test_strong_and_weak_base_definitions(self):
        cases=generate_cases(100,42)
        strong=[r for r in cases if r['variant']=='base' and r['profile']=='strong']
        weak=[r for r in cases if r['variant']=='base' and r['profile']=='weak']
        self.assertTrue(strong and weak)
        self.assertTrue(all(r['net_income']/r['total_assets']>=.1 and r['total_liabilities']/r['total_assets']<=.3 for r in strong))
        self.assertTrue(all(r['net_income']<0 and r['total_liabilities']/r['total_assets']>=.85 for r in weak))
    def test_directional_verdict_not_accuracy(self):
        self.assertEqual(verdict('profit_up','mixed',.2,.4)[0],'consistent')
        self.assertEqual(verdict('profit_up','mixed',.6,.4)[0],'counterintuitive')
        self.assertEqual(verdict('profit_up','mixed',.4,.4)[0],'unchanged')
        self.assertEqual(verdict('base','mixed',.4,.4)[0],'inconclusive')
    def test_feature_mapping_and_identity_transform(self):
        cases=generate_cases(10,42);names=["Net Income to Stockholder's Equity",'Net Income to Total Assets','Retained Earnings to Total Assets','Debt ratio %','Net worth/Assets','Equity to Liability','Liability to Equity']
        frame=feature_frame(cases,names)
        self.assertEqual(frame.shape,(50,7));self.assertTrue(np.isfinite(frame.values).all())
        self.assertAlmostEqual(frame.iloc[0,1],cases[0]['net_income']/cases[0]['total_assets'])
        self.assertTrue(np.any((frame.values<0)|(frame.values>1)))

if __name__=='__main__':unittest.main()
