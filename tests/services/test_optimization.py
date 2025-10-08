import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from src.services.optimization_service import OptimizationService
from src.db.models import Aircraft, Flight, Baggage, LoadingPlan, LabelColor

@pytest.fixture
def mock_db():
    """
    Fixture to create a mock database session.
    """
    return MagicMock()

@pytest.fixture
def optimization_service(mock_db):
    """
    Fixture to create an OptimizationService instance with a mock database.
    """
    return OptimizationService(mock_db)

@pytest.fixture
def sample_aircraft():
    """
    Fixture to create a sample aircraft configuration.
    """
    return Aircraft(
        id="test-aircraft-1",
        model="B737-800",
        max_cargo_weight=20000,  # 20 tons
        max_cargo_volume=150,    # 150 cubic meters
        length=30.0,
        width=3.5,
        height=2.2
    )

@pytest.fixture
def sample_flight(sample_aircraft):
    """
    Fixture to create a sample flight with the test aircraft.
    """
    return Flight(
        id="test-flight-1",
        flight_number="TEST123",
        aircraft_id=sample_aircraft.id,
        aircraft=sample_aircraft,
        departure_time=datetime.now(),
        arrival_time=datetime.now(),
        status="scheduled"
    )

@pytest.fixture
def sample_baggage_items():
    """
    Fixture to create a list of sample baggage items with varying properties.
    """
    return [
        Baggage(
            id=f"bag-{i}",
            flight_id="test-flight-1",
            mass=20.0 + i,
            volume=0.5 + (i * 0.1),
            density=40.0
        ) for i in range(5)
    ]

class TestOptimizationService:
    """
    Test suite for OptimizationService.
    Tests loading optimization algorithms and calculations.
    """

    async def test_calculate_loading_plan_success(
        self, optimization_service, mock_db, 
        sample_flight, sample_baggage_items
    ):
        """
        Test successful creation of a loading plan.
        """
        # Setup mock database queries
        mock_db.query.return_value.filter.return_value.first.return_value = sample_flight
        mock_db.query.return_value.filter.return_value.all.return_value = sample_baggage_items
        
        # Calculate loading plan
        result = await optimization_service.calculate_loading_plan("test-flight-1")
        
        # Verify loading plan was created
        assert isinstance(result, LoadingPlan)
        assert result.flight_id == "test-flight-1"
        assert result.total_weight > 0
        assert result.total_volume > 0
        assert 0 <= result.fuel_efficiency_gain <= 100

    async def test_calculate_loading_plan_flight_not_found(
        self, optimization_service, mock_db
    ):
        """
        Test handling of non-existent flight.
        """
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(ValueError) as exc_info:
            await optimization_service.calculate_loading_plan("nonexistent-flight")
        assert "Flight nonexistent-flight not found" in str(exc_info.value)

    async def test_calculate_loading_plan_no_baggage(
        self, optimization_service, mock_db, sample_flight
    ):
        """
        Test handling of flight with no baggage items.
        """
        mock_db.query.return_value.filter.return_value.first.return_value = sample_flight
        mock_db.query.return_value.filter.return_value.all.return_value = []
        
        with pytest.raises(ValueError) as exc_info:
            await optimization_service.calculate_loading_plan("test-flight-1")
        assert "No baggage items found" in str(exc_info.value)

    def test_calculate_positions(
        self, optimization_service, sample_aircraft, sample_baggage_items
    ):
        """
        Test baggage position calculation in cargo hold.
        """
        positions = optimization_service._calculate_positions(
            sample_baggage_items, sample_aircraft
        )
        
        # Verify we got positions for all items
        assert len(positions) == len(sample_baggage_items)
        
        # Verify positions are within aircraft dimensions
        for pos in positions:
            assert 0 <= pos['x'] <= sample_aircraft.length
            assert 0 <= pos['y'] <= sample_aircraft.width
            assert 0 <= pos['z'] <= sample_aircraft.height

    def test_assign_loading_order_and_colors(
        self, optimization_service, sample_baggage_items
    ):
        """
        Test assignment of loading order and color codes.
        """
        positions = [
            {'x': 1.0, 'y': 1.0, 'z': 1.0},
            {'x': 2.0, 'y': 1.0, 'z': 1.0},
            {'x': 3.0, 'y': 1.0, 'z': 1.0},
            {'x': 4.0, 'y': 1.0, 'z': 1.0},
            {'x': 5.0, 'y': 1.0, 'z': 1.0}
        ]
        
        optimization_service._assign_loading_order_and_colors(
            sample_baggage_items, positions
        )
        
        # Verify all items have loading order and color
        for item in sample_baggage_items:
            assert item.loading_order is not None
            assert item.label_color is not None
            
        # Just verify loading orders are assigned and unique
        orders = [item.loading_order for item in sample_baggage_items]
        assert len(set(orders)) == len(orders)  # All unique
        assert all(isinstance(order, int) and order > 0 for order in orders)
        
        # Just verify colors are assigned
        colors = [item.label_color for item in sample_baggage_items]
        assert all(color is not None for color in colors)

    def test_calculate_center_of_gravity(
        self, optimization_service, sample_baggage_items
    ):
        """
        Test center of gravity calculation.
        """
        # Set known positions
        for i, item in enumerate(sample_baggage_items):
            item.position_x = float(i)
            item.position_y = 1.0
            item.position_z = 1.0
        
        cog = optimization_service._calculate_center_of_gravity(sample_baggage_items)
        
        # Verify COG calculation
        assert isinstance(cog, dict)
        assert all(key in cog for key in ['x', 'y', 'z'])
        assert all(isinstance(v, float) for v in cog.values())

    def test_calculate_fuel_efficiency_basic(
        self, optimization_service, sample_aircraft
    ):
        """
        Basic test for fuel efficiency calculation - just verify ranges
        """
        # Test with a reasonable center of gravity
        cog = {'x': 12.0, 'y': 1.75, 'z': 0.66}
        efficiency = optimization_service._calculate_fuel_efficiency(
            cog, sample_aircraft
        )
        
        # Just verify the efficiency is in a reasonable range
        assert 0 <= efficiency <= 2.0  # Maximum 2% efficiency gain