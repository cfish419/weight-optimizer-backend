import unittest
from services.baggage_tracking.baggage_service import BaggageService
from services.sync_engine.sync_service import SyncService
from services.offline_manager.offline_service import OfflineService


class TestBaggageFlow(unittest.TestCase):
    """Integration tests for complete baggage handling flow"""
    
    def setUp(self):
        self.baggage_service = BaggageService()
        self.sync_service = SyncService()
        self.offline_service = OfflineService()
    
    def test_normal_baggage_flow(self):
        """Test normal baggage check-in and loading flow"""
        # Add standard baggage
        baggage_data = {
            "weight": 20.5,
            "length": 60,
            "width": 40,
            "height": 25,
            "baggage_type": "standard",
            "passenger_id": "PAX123",
            "flight_id": "UA1234"
        }
        
        baggage_id = self.baggage_service.add_baggage(baggage_data)
        self.assertIsNotNone(baggage_id)
        
        # Verify baggage is in flight manifest
        flight_baggage = self.baggage_service.get_flight_baggage("UA1234")
        self.assertEqual(len(flight_baggage), 1)
        self.assertEqual(flight_baggage[0]["weight"], 20.5)
    
    def test_gate_check_scenario(self):
        """Test last-minute gate check scenario"""
        # Initial baggage load
        for i in range(3):
            baggage_data = {
                "weight": 15.0 + i,
                "length": 55,
                "width": 35,
                "height": 20,
                "baggage_type": "standard",
                "passenger_id": f"PAX{i}",
                "flight_id": "UA5678"
            }
            self.baggage_service.add_baggage(baggage_data)
        
        # Gate check addition
        gate_check_data = {
            "weight": 8.5,
            "length": 45,
            "width": 30,
            "height": 15,
            "baggage_type": "gate_check",
            "passenger_id": "PAX_GATE",
            "flight_id": "UA5678"
        }
        
        gate_baggage_id = self.baggage_service.add_baggage(gate_check_data)
        
        # Verify gate check has high priority
        flight_baggage = self.baggage_service.get_flight_baggage("UA5678")
        gate_item = next(item for item in flight_baggage if item["baggage_id"] == gate_baggage_id)
        self.assertEqual(gate_item["loading_priority"], 1)  # Highest priority
    
    def test_special_item_handling(self):
        """Test special item (golf clubs) handling"""
        golf_clubs_data = {
            "weight": 12.0,
            "length": 120,  # Long golf bag
            "width": 25,
            "height": 25,
            "baggage_type": "special",
            "special_item_type": "golf_clubs",
            "passenger_id": "PAX_GOLF",
            "flight_id": "UA9999",
            "loading_instructions": "Handle with care, store vertically"
        }
        
        baggage_id = self.baggage_service.add_baggage(golf_clubs_data)
        
        # Verify special handling
        flight_baggage = self.baggage_service.get_flight_baggage("UA9999")
        golf_item = flight_baggage[0]
        
        self.assertEqual(golf_item["special_item_type"], "golf_clubs")
        self.assertEqual(golf_item["loading_priority"], 2)  # High priority for special items
        self.assertIsNotNone(golf_item["loading_instructions"])
    
    def test_compartment_optimization(self):
        """Test baggage distribution optimization"""
        flight_id = "UA_OPTIMIZE"
        
        # Add various baggage items
        baggage_items = [
            {"weight": 25.0, "priority": "heavy"},
            {"weight": 15.0, "priority": "standard"},
            {"weight": 30.0, "priority": "heavy"},
            {"weight": 10.0, "priority": "light"},
            {"weight": 20.0, "priority": "standard"}
        ]
        
        for i, item in enumerate(baggage_items):
            baggage_data = {
                "weight": item["weight"],
                "length": 60,
                "width": 40,
                "height": 25,
                "baggage_type": "standard",
                "passenger_id": f"PAX_OPT_{i}",
                "flight_id": flight_id
            }
            self.baggage_service.add_baggage(baggage_data)
        
        # Optimize compartment loading
        optimization = self.baggage_service.optimize_compartment_loading(flight_id)
        
        # Verify optimization results
        self.assertIn("forward_compartment", optimization)
        self.assertIn("aft_compartment", optimization)
        
        forward_weight = optimization["forward_compartment"]["total_weight"]
        aft_weight = optimization["aft_compartment"]["total_weight"]
        
        # Forward compartment should have more weight (stability)
        self.assertGreaterEqual(forward_weight, aft_weight)
        
        # Check weight limits
        self.assertLessEqual(forward_weight, 3400.0)  # Forward limit
        self.assertLessEqual(aft_weight, 2300.0)      # Aft limit
    
    def test_offline_sync_flow(self):
        """Test offline agent synchronization"""
        agent_id = "RAMP_AGENT_001"
        
        # Simulate offline changes
        offline_changes = [
            {
                "type": "add_baggage",
                "baggage_data": {
                    "weight": 18.0,
                    "length": 55,
                    "width": 35,
                    "height": 22,
                    "baggage_type": "standard",
                    "passenger_id": "PAX_OFFLINE",
                    "flight_id": "UA_OFFLINE"
                }
            }
        ]
        
        # Sync offline changes
        sync_result = self.offline_service.sync_offline_changes(agent_id, offline_changes)
        
        self.assertEqual(sync_result["applied"], 1)
        self.assertEqual(sync_result["failed"], 0)
        
        # Verify baggage was added
        flight_baggage = self.baggage_service.get_flight_baggage("UA_OFFLINE")
        self.assertEqual(len(flight_baggage), 1)


if __name__ == '__main__':
    unittest.main()