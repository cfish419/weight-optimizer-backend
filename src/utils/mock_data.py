import json
import os
import random
from datetime import datetime, timedelta

from faker import Faker

fake = Faker()


class MockDataGenerator:
    def __init__(self):
        self.southwest_airports = [
            "DAL",
            "HOU",
            "LAS",
            "PHX",
            "MDW",
            "DEN",
            "ATL",
            "LAX",
            "OAK",
            "BWI",
        ]
        self.aircraft_types = ["737-700", "737-800", "737 MAX 8"]

    def generate_flight(self):
        """Generate a mock Southwest flight"""
        flight_number = f"WN{random.randint(1000, 9999)}"
        departure = random.choice(self.southwest_airports)
        arrival = random.choice([x for x in self.southwest_airports if x != departure])

        return {
            "flight_number": flight_number,
            "departure": departure,
            "arrival": arrival,
            "aircraft_type": random.choice(self.aircraft_types),
            "departure_time": (
                datetime.now() + timedelta(hours=random.randint(1, 48))
            ).isoformat(),
            "estimated_passengers": random.randint(120, 175),
        }

    def generate_baggage(self, count=1):
        """Generate mock baggage items"""
        baggages = []
        for _ in range(count):
            weight = round(
                random.uniform(10, 32), 1
            )  # Southwest's weight limit is 32kg
            volume = round(random.uniform(0.1, 0.5), 2)

            baggage = {
                "tag_number": f"WN{random.randint(1000000, 9999999)}",
                "weight_kg": weight,
                "dimensions_cm": {
                    "length": round(random.uniform(45, 90)),
                    "width": round(random.uniform(30, 60)),
                    "height": round(random.uniform(20, 40)),
                },
                "passenger_name": fake.name(),
                "priority": random.choice(["PRIORITY", "STANDARD"]),
                "category": random.choice(["CHECKED", "CARRYON", "CARGO"]),
                "status": "CHECKED_IN",
            }
            baggages.append(baggage)

        return baggages if count > 1 else baggages[0]

    def generate_flight_manifest(self, flight_data=None):
        """Generate a complete flight manifest with baggage"""
        if not flight_data:
            flight_data = self.generate_flight()

        num_bags = random.randint(80, 150)
        baggages = self.generate_baggage(count=num_bags)

        manifest = {
            "flight": flight_data,
            "baggage": baggages,
            "total_weight_kg": sum(bag["weight_kg"] for bag in baggages),
            "timestamp": datetime.now().isoformat(),
        }

        return manifest

    def save_mock_data(self, num_flights=5):
        """Save mock data to files for demo purposes"""
        data_dir = "mock_data"
        os.makedirs(data_dir, exist_ok=True)

        all_data = {"flights": [], "manifests": []}

        for _ in range(num_flights):
            flight = self.generate_flight()
            manifest = self.generate_flight_manifest(flight)
            all_data["flights"].append(flight)
            all_data["manifests"].append(manifest)

        # Save to JSON files
        with open(f"{data_dir}/mock_flight_data.json", "w") as f:
            json.dump(all_data, f, indent=2)

        return f"Mock data saved to {data_dir}/mock_flight_data.json"


def generate_demo_data():
    """Utility function to generate demo data"""
    generator = MockDataGenerator()
    return generator.save_mock_data()
