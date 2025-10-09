import unittest

from src.core.weight_balance import WeightBalanceCalculator
from src.models.aircraft import Boeing737Specs, FlightConfiguration


class TestWeightBalanceCalculator(unittest.TestCase):

    def setUp(self):
        self.aircraft = Boeing737Specs()
        self.config = FlightConfiguration(
            aircraft=self.aircraft, passenger_count=150, fuel_weight=15000.0
        )

    def test_total_weight_calculation(self):
        total_weight = WeightBalanceCalculator.calculate_total_weight(self.config)
        expected = 41000 + 150 * 75.6 + 150 * 7.6 + 150 * 15.9 + 5 * 85.0 + 15000
        self.assertAlmostEqual(total_weight, expected, places=1)

    def test_cg_calculation(self):
        cg = WeightBalanceCalculator.calculate_center_of_gravity(self.config)
        self.assertIsInstance(cg, float)
        self.assertGreater(cg, 0.0)
        self.assertLess(cg, 1.0)

    def test_weight_limits_validation(self):
        limits = WeightBalanceCalculator.validate_weight_limits(self.config)
        self.assertIn("mtow_valid", limits)
        self.assertIn("mlw_valid", limits)
        self.assertIn("mzfw_valid", limits)

    def test_cg_limits_validation(self):
        cg_valid = WeightBalanceCalculator.validate_cg_limits(self.config)
        self.assertIsInstance(cg_valid, bool)


if __name__ == "__main__":
    unittest.main()
