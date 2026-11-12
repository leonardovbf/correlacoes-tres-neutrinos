"""Independent checks of the new statistical and fixed-budget procedures."""
import sys
import unittest
from pathlib import Path

import numpy as np
from scipy.stats import bootstrap

sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'analysis')]
from feedback_statistics import intervals,weighted_statistics,statistics,first_loss,wilson,slope
from feedback_noise import assignment,trio,sample_counts,analyze_counts


class FeedbackRevisionTests(unittest.TestCase):
    def test_bca_matches_scipy_for_mean(self):
        data=np.array([.1,.4,.8,.9,1.1,1.7,2.8,5.])
        indices=np.random.default_rng(31).integers(0,len(data),size=(10000,len(data)))
        draws=data[indices].mean(axis=1)
        jack=np.array([np.delete(data,i).mean() for i in range(len(data))])
        actual=intervals(data.mean(),draws,jack)
        scipy_result=bootstrap((data,),np.mean,n_resamples=10000,method='BCa',rng=np.random.default_rng(31))
        np.testing.assert_allclose(actual['BCa'],scipy_result.confidence_interval,atol=1e-13)

    def test_basic_interval_reflects_percentile_about_estimate(self):
        result=intervals(1.,np.linspace(1,3,101),np.arange(10.))
        np.testing.assert_allclose(result['basic'],[-.95,.95])
        self.assertTrue(intervals(.5,np.linspace(1,3,101),np.arange(10.))['bias_fraction_at_boundary'])

    def test_bootstrap_weights_preserve_joint_moments(self):
        rng=np.random.default_rng(11)
        blocks=[rng.normal(size=(4,3,k)) for k in (3,3,1)]
        reference2=np.ones((3,3));reference3=np.ones((3,1))
        actual=weighted_statistics(blocks,[[2,0,1,1]],reference2,reference3,3)[0]
        expected=statistics([b[[0,0,2,3]].mean(axis=0) for b in blocks],reference2,reference3,3)
        np.testing.assert_allclose(actual,expected,atol=1e-14)

    def test_slope_uses_r3_values_on_log_grid(self):
        x=np.log10([.1,.3,1,3,10]);self.assertAlmostEqual(float(slope(x,2+3*x)),3.)

    def test_threshold_reports_first_loss_and_reentry(self):
        result=first_loss([0,.1,.2,.3],[True,False,True,True])
        self.assertEqual(result['bracket'],[0.,.1]);self.assertTrue(result['later_reentry'])
        self.assertEqual(first_loss([0,.1],[True,True])['status'],'lower_bound_only')
        self.assertEqual(first_loss([0,.1],[False,False])['status'],'failure_at_zero')

    def test_assignment_channel_is_stochastic_and_matches_known_flip(self):
        matrix=assignment(4,.1)
        np.testing.assert_allclose(matrix.sum(axis=0),1,atol=1e-14)
        self.assertAlmostEqual(matrix[1,0],.1*.9**3)

    def test_trio_marginal_preserves_spectator_bit(self):
        vector=np.zeros(16);vector[9]=7
        expected=np.zeros(8);expected[1]=7
        np.testing.assert_array_equal(trio(vector),expected)

    def test_fixed_budget_includes_both_calibrations(self):
        probabilities=np.tile(np.arange(1,17)/136.,(32,1))
        counts=sample_counts(probabilities,.03,np.random.default_rng(8))
        self.assertEqual(counts['raw'].sum(),327680)
        self.assertEqual(counts['signal'].sum()+counts['zero'].sum()+counts['one'].sum(),327680)
        self.assertTrue(np.all(counts['raw'].sum(axis=1)==10240))
        result,draws,condition=analyze_counts(counts,0.,0.,902,repetitions=50)
        self.assertEqual(draws.shape,(50,2));self.assertLess(condition,10)
        self.assertIn('primary_equivalent',result['mitigated'])

    def test_wilson_extremes_remain_in_unit_interval(self):
        self.assertAlmostEqual(wilson(0,100)[0],0)
        self.assertAlmostEqual(wilson(100,100)[1],1)
        self.assertGreater(wilson(100,100)[0],.95)

if __name__=='__main__':unittest.main()
