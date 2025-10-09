import json
import sys
import uuid
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

# Add the project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from src.db.database import SessionLocal, engine
from src.db.models import Baggage, Base, Flight


def init_db():
    Base.metadata.create_all(bind=engine)


def load_mock_data():
    """Load the generated mock data into the database"""
    # Read the mock data
    with open("mock_data/mock_flight_data.json", "r") as f:
        data = json.load(f)

    db = SessionLocal()
    try:
        # Process each flight and its manifest
        for i, (flight_data, manifest) in enumerate(
            zip(data["flights"], data["manifests"])
        ):
            # Create flight record
            flight = Flight(
                id=str(uuid.uuid4()),
                flight_number=flight_data["flight_number"],
                departure=flight_data["departure"],
                arrival=flight_data["arrival"],
                aircraft_type=flight_data["aircraft_type"],
                departure_time=datetime.fromisoformat(flight_data["departure_time"]),
                estimated_passengers=flight_data["estimated_passengers"],
            )
            db.add(flight)
            db.flush()  # Get the flight ID

            # Add baggage items
            for bag_data in manifest["baggage"]:
                baggage = Baggage(
                    id=str(uuid.uuid4()),
                    flight_id=flight.id,
                    tag_number=bag_data["tag_number"],
                    weight_kg=bag_data["weight_kg"],
                    length_cm=bag_data["dimensions_cm"]["length"],
                    width_cm=bag_data["dimensions_cm"]["width"],
                    height_cm=bag_data["dimensions_cm"]["height"],
                    passenger_name=bag_data["passenger_name"],
                    priority=bag_data["priority"],
                    category=bag_data["category"],
                    status=bag_data["status"],
                )
                db.add(baggage)

            print(
                f"Processed flight {flight_data['flight_number']} with {len(manifest['baggage'])} bags"
            )

        db.commit()
        print("✅ All mock data has been successfully loaded into the database!")

    except Exception as e:
        print(f"❌ Error loading data: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("Initializing database...")
    init_db()
    print("Loading mock data...")
    load_mock_data()
