import requests
from typing import Optional
from src.models.weather import WeatherData, WeatherCondition

class WeatherService:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.base_url = "https://api.openweathermap.org/data/2.5"
        
    async def get_weather_data(self, airport_code: str) -> Optional[WeatherData]:
        """Get current weather data for airport"""
        try:
            # In production, use real weather API
            # For demo, return sample data
            return self._get_sample_weather(airport_code)
        except Exception as e:
            print(f"Weather service error: {e}")
            return None
            
    def _get_sample_weather(self, airport_code: str) -> WeatherData:
        """Sample weather data for demo"""
        weather_samples = {
            "SEA": WeatherData(
                temperature=15.0,
                wind_speed=12.0,
                wind_direction=270,
                visibility=10.0,
                condition=WeatherCondition.RAIN,
                density_altitude=500.0,
                crosswind_component=8.0,
                headwind_component=9.0
            ),
            "DEN": WeatherData(
                temperature=25.0,
                wind_speed=15.0,
                wind_direction=180,
                visibility=15.0,
                condition=WeatherCondition.CLEAR,
                density_altitude=6500.0,
                crosswind_component=0.0,
                headwind_component=15.0
            ),
            "MIA": WeatherData(
                temperature=32.0,
                wind_speed=8.0,
                wind_direction=90,
                visibility=8.0,
                condition=WeatherCondition.CLEAR,
                density_altitude=100.0,
                crosswind_component=8.0,
                headwind_component=0.0
            )
        }
        
        return weather_samples.get(airport_code, weather_samples["SEA"])
        
    def calculate_fuel_adjustment(self, weather: WeatherData, base_fuel: float) -> float:
        """Calculate fuel adjustment based on weather conditions"""
        adjustment_factor = 1.0
        
        # Headwind/tailwind adjustments
        if weather.headwind_component > 0:  # Headwind
            adjustment_factor += weather.headwind_component * 0.002  # 0.2% per knot
        else:  # Tailwind
            adjustment_factor += weather.headwind_component * 0.001  # 0.1% per knot
            
        # Temperature adjustments
        if weather.temperature > 30:
            adjustment_factor += 0.05  # 5% for hot weather
        elif weather.temperature < -10:
            adjustment_factor += 0.03  # 3% for cold weather
            
        # Weather condition adjustments
        if weather.condition in [WeatherCondition.STORM, WeatherCondition.TURBULENCE]:
            adjustment_factor += 0.08  # 8% for severe weather
        elif weather.condition in [WeatherCondition.RAIN, WeatherCondition.SNOW]:
            adjustment_factor += 0.03  # 3% for precipitation
            
        return base_fuel * adjustment_factor
        
    def get_performance_limitations(self, weather: WeatherData) -> dict:
        """Get performance limitations based on weather"""
        limitations = {
            "max_takeoff_weight_reduction": 0.0,
            "runway_condition": "dry",
            "visibility_category": "cat_i",
            "crosswind_limit_exceeded": False
        }
        
        # Performance factor affects max weight
        perf_factor = weather.get_performance_factor()
        limitations["max_takeoff_weight_reduction"] = (1.0 - perf_factor) * 100  # percentage
        
        # Runway conditions
        if weather.condition in [WeatherCondition.RAIN, WeatherCondition.SNOW]:
            limitations["runway_condition"] = "wet"
        elif weather.condition == WeatherCondition.ICE:
            limitations["runway_condition"] = "icy"
            
        # Visibility categories
        if weather.visibility < 0.5:
            limitations["visibility_category"] = "cat_iii"
        elif weather.visibility < 2.0:
            limitations["visibility_category"] = "cat_ii"
            
        # Crosswind limits (typical 737 limit ~35 knots)
        if weather.crosswind_component > 35:
            limitations["crosswind_limit_exceeded"] = True
            
        return limitations