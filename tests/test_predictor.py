import unittest
from unittest.mock import patch
import pandas as pd
from ai.predictor import (
    load_training_data,
    prepare_features,
    predict_ram_usage,
    run_prediction_cycle
)

class TestPredictor(unittest.TestCase):

    def test_load_training_data_returns_dataframe(self):
        result = load_training_data()
        self.assertIsInstance(result, pd.DataFrame)

    def test_predict_ram_usage_returns_dict(self):
        result = predict_ram_usage(minutes_ahead=15)
        self.assertIsInstance(result, dict)
        self.assertIn('status', result)

    def test_predict_ram_usage_valid_percent(self):
        result = predict_ram_usage(minutes_ahead=15)
        if result['status'] == 'success':
            self.assertGreaterEqual(result['predicted_percent'], 0)
            self.assertLessEqual(result['predicted_percent'], 100)

    def test_predict_ram_usage_risk_levels(self):
        result = predict_ram_usage(minutes_ahead=15)
        if result['status'] == 'success':
            self.assertIn(result['risk_level'],
                         ['HEALTHY', 'MODERATE', 'WARNING', 'CRITICAL'])

    def test_run_prediction_cycle_returns_list(self):
        result = run_prediction_cycle()
        self.assertIsInstance(result, list)

    def test_run_prediction_cycle_three_horizons(self):
        result = run_prediction_cycle()
        # Should return predictions for 15, 30, 60 minutes
        self.assertEqual(len(result), 3)

    def test_prediction_horizons_correct(self):
        result = run_prediction_cycle()
        horizons = [p['minutes_ahead'] for p in result if p['status'] == 'success']
        self.assertIn(15, horizons)
        self.assertIn(30, horizons)
        self.assertIn(60, horizons)

if __name__ == '__main__':
    unittest.main()