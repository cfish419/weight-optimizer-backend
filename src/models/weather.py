from dataclasses import dataclass
from typing import Optional
from enum import Enum

class WeatherCondition(Enum):
    CLEAR = "clear"
    RAIN = "rain"
    SNOW = "snow"
    ICE = "ice"
    TURBULENCE = "turbulence"
    STORM = "storm"

@dataclass
class WeatherData:
    temperature: float  # Celsius
    wind_speed: float  # knots
    wind_direction: int  # degrees
    visibility: float  # nautical miles
    condition: WeatherCondition
    density_altitude: float  # feet
    crosswind_component: float  # knots
    headwind_component: float  # knots (positive = headwind, negative = tailwind)
    
    def get_performance_factor(self) -> float:
        """Calculate performance degradation factor (0.0 to 1.0)"""
        factor = 1.0
        
        # Temperature effects
        if self.temperature > 30:  # Hot weather
            factor -= 0.05
        elif self.temperature < -20:  # Cold weather
            factor -= 0.02
            
        # Density altitude effects
        if self.density_altitude > 5000:
            factor -= 0.03
            
        # Weather condition effects
        if self.condition in [WeatherCondition.RAIN, WeatherCondition.SNOW]:
            factor -= 0.02
        elif self.condition == WeatherCondition.ICE:
            factor -= 0.05
            
        return max(0.8, factor)  # Minimum 80% performance
    
    def get_deicing_weight(self) -> float:
        """Calculate additional weight from de-icing fluid (kg)"""
        if self.condition in [WeatherCondition.ICE, WeatherCondition.SNOW]:
            if self.temperature < 0:
                return 200.0  # Typical de-icing fluid weight
        return 0.0