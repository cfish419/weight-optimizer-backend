from typing import Dict, Any, List, Optional
from api.schemas.baggage_schemas import BaggageItem


class BaggageRepository:
    """Repository for baggage data persistence"""
    
    def __init__(self):
        # In-memory storage for Phase 2 (replace with database in Phase 3)
        self.baggage_store: Dict[str, BaggageItem] = {}
        self.flight_baggage_index: Dict[str, List[str]] = {}
    
    def save_baggage(self, baggage_id: str, baggage_item: BaggageItem) -> bool:
        """Save baggage item"""
        try:
            self.baggage_store[baggage_id] = baggage_item
            
            # Update flight index
            flight_id = baggage_item.flight_id
            if flight_id not in self.flight_baggage_index:
                self.flight_baggage_index[flight_id] = []
            
            if baggage_id not in self.flight_baggage_index[flight_id]:
                self.flight_baggage_index[flight_id].append(baggage_id)
            
            return True
        except Exception:
            return False
    
    def get_baggage(self, baggage_id: str) -> Optional[BaggageItem]:
        """Get baggage item by ID"""
        return self.baggage_store.get(baggage_id)
    
    def get_flight_baggage(self, flight_id: str) -> List[Dict[str, Any]]:
        """Get all baggage for a flight"""
        baggage_ids = self.flight_baggage_index.get(flight_id, [])
        
        flight_baggage = []
        for baggage_id in baggage_ids:
            baggage_item = self.baggage_store.get(baggage_id)
            if baggage_item:
                # Convert to dict for API response
                baggage_dict = {
                    "baggage_id": baggage_id,
                    "weight": baggage_item.weight,
                    "length": baggage_item.length,
                    "width": baggage_item.width,
                    "height": baggage_item.height,
                    "baggage_type": baggage_item.baggage_type.value,
                    "passenger_id": baggage_item.passenger_id,
                    "flight_id": baggage_item.flight_id,
                    "special_item_type": baggage_item.special_item_type.value if baggage_item.special_item_type else None,
                    "fragile": baggage_item.fragile,
                    "hazardous": baggage_item.hazardous,
                    "loading_instructions": baggage_item.loading_instructions,
                    "compartment_preference": baggage_item.compartment_preference,
                    "volume": baggage_item.calculate_volume(),
                    "is_oversized": baggage_item.is_oversized(),
                    "loading_priority": baggage_item.get_loading_priority()
                }
                flight_baggage.append(baggage_dict)
        
        return flight_baggage
    
    def delete_baggage(self, baggage_id: str) -> bool:
        """Delete baggage item"""
        try:
            baggage_item = self.baggage_store.get(baggage_id)
            if baggage_item:
                # Remove from flight index
                flight_id = baggage_item.flight_id
                if flight_id in self.flight_baggage_index:
                    self.flight_baggage_index[flight_id].remove(baggage_id)
                
                # Remove from store
                del self.baggage_store[baggage_id]
                return True
            return False
        except Exception:
            return False
    
    def get_baggage_by_passenger(self, passenger_id: str) -> List[Dict[str, Any]]:
        """Get all baggage for a passenger"""
        passenger_baggage = []
        
        for baggage_id, baggage_item in self.baggage_store.items():
            if baggage_item.passenger_id == passenger_id:
                baggage_dict = {
                    "baggage_id": baggage_id,
                    "weight": baggage_item.weight,
                    "flight_id": baggage_item.flight_id,
                    "baggage_type": baggage_item.baggage_type.value
                }
                passenger_baggage.append(baggage_dict)
        
        return passenger_baggage
    
    def get_special_items(self, flight_id: str) -> List[Dict[str, Any]]:
        """Get all special items for a flight"""
        special_items = []
        baggage_ids = self.flight_baggage_index.get(flight_id, [])
        
        for baggage_id in baggage_ids:
            baggage_item = self.baggage_store.get(baggage_id)
            if baggage_item and baggage_item.special_item_type:
                special_items.append({
                    "baggage_id": baggage_id,
                    "special_item_type": baggage_item.special_item_type.value,
                    "weight": baggage_item.weight,
                    "dimensions": f"{baggage_item.length}x{baggage_item.width}x{baggage_item.height}",
                    "loading_instructions": baggage_item.loading_instructions
                })
        
        return special_items