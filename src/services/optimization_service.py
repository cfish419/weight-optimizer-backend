import numpy as np
from typing import List, Dict, Optional
from src.db.models import Baggage, Flight, LoadingPlan, LabelColor
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)

class OptimizationService:
    def __init__(self, db: Session):
        self.db = db

    async def calculate_loading_plan(self, flight_id: str) -> Optional[LoadingPlan]:
        """
        Calculate the optimal loading plan for a flight
        """
        # Get flight and its baggage
        flight = self.db.query(Flight).filter(Flight.id == flight_id).first()
        if not flight:
            raise ValueError(f"Flight {flight_id} not found")

        baggage_items = self.db.query(Baggage).filter(Baggage.flight_id == flight_id).all()
        if not baggage_items:
            raise ValueError(f"No baggage items found for flight {flight_id}")

        # Sort baggage by density (descending) for initial ordering
        baggage_items.sort(key=lambda x: x.density, reverse=True)

        # Get aircraft dimensions
        aircraft = flight.aircraft
        cargo_volume = aircraft.length * aircraft.width * aircraft.height

        # Validate total weight and volume
        total_weight = sum(item.mass for item in baggage_items)
        total_volume = sum(item.volume for item in baggage_items)

        if total_weight > aircraft.max_cargo_weight:
            raise ValueError("Total baggage weight exceeds aircraft capacity")
        if total_volume > cargo_volume:
            raise ValueError("Total baggage volume exceeds cargo hold capacity")

        # Calculate positions and loading order
        positions = self._calculate_positions(baggage_items, aircraft)
        
        # Update baggage items with positions and colors
        self._assign_loading_order_and_colors(baggage_items, positions)

        # Calculate center of gravity
        cog = self._calculate_center_of_gravity(baggage_items)

        # Calculate estimated fuel efficiency gain
        efficiency_gain = self._calculate_fuel_efficiency(cog, aircraft)

        # Create or update loading plan
        loading_plan = LoadingPlan(
            flight_id=flight_id,
            total_weight=total_weight,
            total_volume=total_volume,
            center_of_gravity_x=cog['x'],
            center_of_gravity_y=cog['y'],
            center_of_gravity_z=cog['z'],
            fuel_efficiency_gain=efficiency_gain
        )

        self.db.add(loading_plan)
        self.db.commit()
        self.db.refresh(loading_plan)

        return loading_plan

    def _calculate_positions(self, baggage_items: List[Baggage], aircraft) -> List[Dict]:
        """
        Calculate optimal positions for each baggage item in the cargo hold
        Uses a 3D bin packing algorithm
        """
        positions = []
        # Simple layer-based positioning for now
        # TODO: Implement more sophisticated 3D bin packing algorithm
        current_x = 0
        current_y = 0
        current_z = 0
        layer_height = 0

        for item in baggage_items:
            # Simplified positioning - stack items in layers
            if current_x + item.volume ** (1/3) > aircraft.length:
                current_x = 0
                current_y += layer_height
                layer_height = 0
                
                if current_y + item.volume ** (1/3) > aircraft.width:
                    current_y = 0
                    current_z += layer_height
                    
                    if current_z + item.volume ** (1/3) > aircraft.height:
                        raise ValueError("Cannot fit all items in cargo hold")

            positions.append({
                'x': current_x,
                'y': current_y,
                'z': current_z
            })

            current_x += item.volume ** (1/3)
            layer_height = max(layer_height, item.volume ** (1/3))

        return positions

    def _assign_loading_order_and_colors(self, baggage_items: List[Baggage], positions: List[Dict]):
        """
        Assign loading order and colors based on positions
        Red: Load first (back of aircraft)
        Yellow: Load second (middle)
        Blue: Load last (front)
        """
        # Sort by z-coordinate first, then y, then x
        items_with_pos = list(zip(baggage_items, positions))
        items_with_pos.sort(key=lambda x: (x[1]['z'], x[1]['y'], x[1]['x']))

        total_items = len(items_with_pos)
        section_size = total_items // 3

        for i, (item, pos) in enumerate(items_with_pos):
            # Update position
            item.position_x = pos['x']
            item.position_y = pos['y']
            item.position_z = pos['z']
            
            # Update loading order
            item.loading_order = i + 1

            # Assign color based on position
            if i < section_size:
                item.label_color = LabelColor.RED
            elif i < section_size * 2:
                item.label_color = LabelColor.YELLOW
            else:
                item.label_color = LabelColor.BLUE

    def _calculate_center_of_gravity(self, baggage_items: List[Baggage]) -> Dict:
        """
        Calculate the center of gravity for all baggage items
        """
        total_mass = sum(item.mass for item in baggage_items)
        cog_x = sum(item.mass * item.position_x for item in baggage_items) / total_mass
        cog_y = sum(item.mass * item.position_y for item in baggage_items) / total_mass
        cog_z = sum(item.mass * item.position_z for item in baggage_items) / total_mass

        return {'x': cog_x, 'y': cog_y, 'z': cog_z}

    def _calculate_fuel_efficiency(self, cog: Dict, aircraft) -> float:
        """
        Calculate estimated fuel efficiency gain based on loading distribution.
        
        The calculation considers:
        1. Deviation from ideal center of gravity position
        2. Aircraft-specific balance characteristics
        3. Impact on aerodynamics and fuel consumption
        
        Args:
            cog: Dictionary containing x, y, z coordinates of center of gravity
            aircraft: Aircraft model with dimensional specifications
            
        Returns:
            Float value representing fuel efficiency gain as a percentage (0-2%)
        """
        # Define ideal center of gravity positions (industry standard positions)
        ideal_x = aircraft.length * 0.4  # 40% from the front for optimal lift distribution
        ideal_y = aircraft.width * 0.5   # Centered for lateral stability
        ideal_z = aircraft.height * 0.3  # 30% from the bottom for vertical stability

        # Calculate normalized deviations from ideal position
        deviation_x = abs(cog['x'] - ideal_x) / aircraft.length
        deviation_y = abs(cog['y'] - ideal_y) / aircraft.width
        deviation_z = abs(cog['z'] - ideal_z) / aircraft.height

        # Weight the deviations based on their impact on fuel efficiency
        # Longitudinal (x) balance has the most significant impact
        weighted_deviation = (
            0.5 * deviation_x +  # 50% weight for longitudinal balance
            0.3 * deviation_y +  # 30% weight for lateral balance
            0.2 * deviation_z    # 20% weight for vertical balance
        )

        # Calculate efficiency gain
        # Maximum potential gain of 2% when perfectly balanced
        # The relationship is non-linear, using a quadratic falloff
        max_efficiency_gain = 2.0  # 2% maximum gain
        efficiency_gain = max_efficiency_gain * (1 - weighted_deviation ** 2)

        # Ensure result is within expected range
        return max(0.0, min(efficiency_gain, max_efficiency_gain))