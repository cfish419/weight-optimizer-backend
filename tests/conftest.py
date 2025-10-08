import pytest
import cv2
import numpy as np
from datetime import datetime
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.db.models import Base, Aircraft, Flight
from src.db.database import SQLALCHEMY_DATABASE_URL

@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    """
    Setup test environment variables before any tests run.
    This ensures we're using test-specific configuration.
    """
    # Store current environment
    original_env = dict(os.environ)
    
    # Load test environment variables
    from dotenv import load_dotenv
    load_dotenv('tests/.env.test', override=True)
    
    yield
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)

@pytest.fixture(scope="session")
def test_db():
    """
    Create a test database and provide a session factory.
    This fixture:
    1. Creates a fresh test database for each test session
    2. Sets up all required tables
    3. Provides a session factory for test operations
    4. Cleans up the database after tests complete
    """
    from sqlalchemy_utils import create_database, database_exists, drop_database
    
    # Create test database URL
    test_db_url = SQLALCHEMY_DATABASE_URL
    
    # Drop test database if it exists and create a fresh one
    if database_exists(test_db_url):
        drop_database(test_db_url)
    create_database(test_db_url)
    
    # Create test database engine
    engine = create_engine(test_db_url)
    
    # Create all tables
    Base.metadata.create_all(engine)
    
    # Create session factory
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=engine
    )
    
    yield TestingSessionLocal
    
    # Cleanup: Drop test database after all tests
    drop_database(test_db_url)

@pytest.fixture
def test_image():
    """
    Create a test image file for baggage measurement tests.
    """
    # Create a sample image
    image = np.ones((500, 500, 3), dtype=np.uint8) * 255
    
    # Add a reference marker
    cv2.rectangle(image, (50, 50), (150, 150), (0, 0, 0), -1)
    
    # Add a simulated baggage item
    cv2.rectangle(image, (200, 200), (400, 400), (128, 128, 128), -1)
    
    # Save the image
    filename = "test_baggage_image.jpg"
    cv2.imwrite(filename, image)
    
    yield filename
    
    # Cleanup
    os.remove(filename)

@pytest.fixture
def sample_aircraft_data():
    """
    Provide sample aircraft data for tests.
    """
    return {
        "model": "B737-800",
        "max_cargo_weight": 20000.0,
        "max_cargo_volume": 150.0,
        "length": 30.0,
        "width": 3.5,
        "height": 2.2
    }

@pytest.fixture
def sample_flight_data():
    """
    Provide sample flight data for tests.
    """
    return {
        "flight_number": "TEST123",
        "departure_time": datetime.now(),
        "arrival_time": datetime.now(),
        "status": "scheduled"
    }

@pytest.fixture
def test_aircraft(test_db, sample_aircraft_data):
    """
    Create a test aircraft in the database.
    """
    db = test_db()
    aircraft = Aircraft(**sample_aircraft_data)
    db.add(aircraft)
    db.commit()
    db.refresh(aircraft)
    yield aircraft
    db.close()

@pytest.fixture
def test_flight(test_db, test_aircraft, sample_flight_data):
    """
    Create a test flight in the database.
    """
    db = test_db()
    flight_data = sample_flight_data.copy()
    flight_data["aircraft_id"] = test_aircraft.id
    flight = Flight(**flight_data)
    db.add(flight)
    db.commit()
    db.refresh(flight)
    yield flight
    db.close()