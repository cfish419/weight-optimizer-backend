import sqlite3
import sys
from pathlib import Path


def check_database():
    """Check the contents of our database"""
    try:
        # Connect to the database
        conn = sqlite3.connect("flight_optimizer.db")
        cursor = conn.cursor()

        # Check flights table
        cursor.execute("SELECT COUNT(*) FROM flights")
        flight_count = cursor.fetchone()[0]
        print(f"\n✈️  Found {flight_count} flights in database")

        # Show sample flight
        cursor.execute(
            """
            SELECT flight_number, departure, arrival, aircraft_type, departure_time 
            FROM flights LIMIT 1
        """
        )
        sample_flight = cursor.fetchone()
        if sample_flight:
            print("\nSample Flight:")
            print(f"Flight: {sample_flight[0]}")
            print(f"Route: {sample_flight[1]} -> {sample_flight[2]}")
            print(f"Aircraft: {sample_flight[3]}")
            print(f"Departure: {sample_flight[4]}")

        # Check baggage table
        cursor.execute("SELECT COUNT(*) FROM baggage")
        baggage_count = cursor.fetchone()[0]
        print(f"\n🧳 Found {baggage_count} baggage items in database")

        # Show sample baggage
        cursor.execute(
            """
            SELECT tag_number, weight_kg, passenger_name, priority 
            FROM baggage LIMIT 1
        """
        )
        sample_bag = cursor.fetchone()
        if sample_bag:
            print("\nSample Baggage:")
            print(f"Tag: {sample_bag[0]}")
            print(f"Weight: {sample_bag[1]} kg")
            print(f"Passenger: {sample_bag[2]}")
            print(f"Priority: {sample_bag[3]}")

        # Show average bags per flight
        if flight_count > 0:
            avg_bags = baggage_count / flight_count
            print(f"\n📊 Average bags per flight: {avg_bags:.1f}")

    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    check_database()
# Ensure the script runs only when executed directly
