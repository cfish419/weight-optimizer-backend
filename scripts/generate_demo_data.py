"""
Script to generate and load demo data for the hackathon demonstration.
Run this script to populate the database with realistic-looking test data.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.utils.mock_data import generate_demo_data

async def main():
    print("Generating demo data for Southwest Airlines baggage optimization...")
    
    # Generate mock flight and baggage data
    result = generate_demo_data()
    print(f"✅ {result}")
    
    print("\nDemo data is ready! You can now:")
    print("1. Start the API server")
    print("2. Use the generated data in mock_data/mock_flight_data.json")
    print("3. Test the optimization endpoints with realistic data")

if __name__ == "__main__":
    asyncio.run(main())
# Ensure the script runs only when executed directly