#!/usr/bin/env python3
"""
Boeing 737 Weight & Balance Optimizer - Phase 1
Core mathematical engine demonstration
"""

from src.core.optimizer import LoadOptimizer
from src.core.weight_balance import WeightBalanceCalculator
from src.models.aircraft import Boeing737Specs, FlightConfiguration
from src.utils.validators import FAA_Validator


def main():
    # Example flight configuration
    aircraft = Boeing737Specs()
    config = FlightConfiguration(
        aircraft=aircraft, passenger_count=150, fuel_weight=18000.0
    )

    print("=== Boeing 737 Weight & Balance Analysis ===")
    print(f"Passengers: {config.passenger_count}")
    print(f"Fuel Weight: {config.fuel_weight} kg")

    # Calculate weights
    total_weight = WeightBalanceCalculator.calculate_total_weight(config)
    cg_position = WeightBalanceCalculator.calculate_center_of_gravity(config)

    print(f"\nTotal Weight: {total_weight:.1f} kg")
    print(f"Center of Gravity: {cg_position:.3f} MAC")

    # Validate compliance
    compliance = FAA_Validator.validate_weight_balance_compliance(config)
    print(f"\nFAA Compliance: {compliance['overall_compliant']}")

    # Optimize baggage distribution
    baggage_dist = LoadOptimizer.optimize_baggage_distribution(config)
    print(f"\nOptimal Baggage Distribution:")
    print(f"  Forward Cargo: {baggage_dist['forward_cargo']:.1f} kg")
    print(f"  Aft Cargo: {baggage_dist['aft_cargo']:.1f} kg")

    # Ballast suggestions
    ballast = LoadOptimizer.suggest_ballast(config)
    print(f"\nBallast Recommendation:")
    print(f"  Location: {ballast['ballast_location']}")
    print(f"  Weight: {ballast['ballast_weight']:.1f} kg")


if __name__ == "__main__":
    main()
