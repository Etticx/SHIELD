import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('ratio_audit',Path(__file__).resolve().parents[1]/'tools'/'test_ratio_bounds.py')
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class BoundsAuditTests(unittest.TestCase):
    def test_consistent_raw_ratios_pass(self):
        row=dict(zip(module.FEATURES,[.25,.1,.15,.6,.4,2/3,1.5]))
        results=module.check_row(row,module.default_bounds(),1e-8,1e-8)
        self.assertTrue(all(r['status']=='match' for r in results))
    def test_corrupted_pair_fails(self):
        row=dict(zip(module.FEATURES,[.25,.1,.15,.6,.4,.1,1.5]))
        self.assertTrue(any(r['status']=='mismatch' for r in module.check_row(row,module.default_bounds(),1e-8,1e-8)))
    def test_two_distinct_bound_pairs_can_pass_all_checks(self):
        row=dict(zip(module.FEATURES,[.25,.1,.15,.6,.4,2/3,1.5]))
        bounds=module.default_bounds()
        # Multiply both income ratios by two. Identities still hold: bounds are not unique.
        for k in module.FEATURES[:2]:bounds[k]=[0,2]
        self.assertTrue(all(r['status']=='match' for r in module.check_row(row,bounds,1e-8,1e-8)))
    def test_missing_value_is_skipped_not_zero(self):
        row=dict(zip(module.FEATURES,[.25,.1,.15,.6,.4,2/3,1.5]));row[module.FEATURES[0]]=None
        results=module.check_row(row,module.default_bounds(),1e-8,1e-8)
        self.assertEqual(results[-1]['status'],'skipped')
    def test_invalid_bounds_rejected(self):
        bounds=module.default_bounds();bounds[module.FEATURES[0]]=[1,0]
        with self.assertRaises(ValueError):module.validate_bounds(bounds)

if __name__=='__main__':unittest.main()
