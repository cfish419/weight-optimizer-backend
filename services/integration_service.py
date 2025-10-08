from typing import Dict, Any, List, Optional
import httpx
import json
from datetime import datetime
import asyncio
from dataclasses import dataclass

@dataclass
class LegacySystemConfig:
    name: str
    endpoint: str
    auth_type: str  # basic, oauth, api_key
    credentials: Dict[str, str]
    protocol: str  # rest, soap, sftp, odbc

class IntegrationService:
    def __init__(self):
        self.legacy_systems = {
            "weight_balance": LegacySystemConfig(
                name="Existing Weight & Balance System",
                endpoint="https://wb.airline.com/api",
                auth_type="basic",
                credentials={"username": "wb_user", "password": "wb_pass"},
                protocol="rest"
            ),
            "dcs": LegacySystemConfig(
                name="Departure Control System",
                endpoint="https://dcs.airline.com/soap",
                auth_type="oauth",
                credentials={"client_id": "dcs_client", "client_secret": "dcs_secret"},
                protocol="soap"
            ),
            "mro": LegacySystemConfig(
                name="Maintenance System",
                endpoint="https://mro.airline.com/api",
                auth_type="api_key",
                credentials={"api_key": "mro_api_key"},
                protocol="rest"
            ),
            "fos": LegacySystemConfig(
                name="Flight Operations System",
                endpoint="https://fos.airline.com/api",
                auth_type="basic",
                credentials={"username": "fos_user", "password": "fos_pass"},
                protocol="rest"
            )
        }
        
    async def sync_to_legacy_wb_system(self, flight_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sync weight & balance data to existing system"""
        system = self.legacy_systems["weight_balance"]
        
        payload = {
            "flight_number": flight_data["flight_number"],
            "aircraft_id": flight_data["aircraft_id"],
            "total_weight": flight_data["total_weight"],
            "cg_position": flight_data["cg_position"],
            "compartment_weights": flight_data["compartment_weights"],
            "fuel_weight": flight_data["fuel_weight"],
            "passenger_count": flight_data["passenger_count"],
            "baggage_count": flight_data["baggage_count"],
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{system.endpoint}/weight-balance",
                    json=payload,
                    auth=(system.credentials["username"], system.credentials["password"]),
                    timeout=30.0
                )
                
                return {
                    "success": response.status_code == 200,
                    "response": response.json() if response.status_code == 200 else None,
                    "error": response.text if response.status_code != 200 else None
                }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def sync_to_dcs(self, baggage_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sync baggage data to Departure Control System"""
        system = self.legacy_systems["dcs"]
        
        # SOAP envelope for DCS integration
        soap_body = f"""
        <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
            <soap:Body>
                <UpdateBaggageStatus>
                    <FlightNumber>{baggage_data['flight_number']}</FlightNumber>
                    <BaggageId>{baggage_data['baggage_id']}</BaggageId>
                    <Status>{baggage_data['status']}</Status>
                    <Weight>{baggage_data['weight']}</Weight>
                    <Compartment>{baggage_data['compartment']}</Compartment>
                    <Timestamp>{datetime.now().isoformat()}</Timestamp>
                </UpdateBaggageStatus>
            </soap:Body>
        </soap:Envelope>
        """
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    system.endpoint,
                    content=soap_body,
                    headers={"Content-Type": "text/xml; charset=utf-8"},
                    timeout=30.0
                )
                
                return {
                    "success": response.status_code == 200,
                    "response": response.text,
                    "error": None if response.status_code == 200 else response.text
                }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def sync_to_maintenance(self, maintenance_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sync maintenance data to MRO system"""
        system = self.legacy_systems["mro"]
        
        payload = {
            "aircraft_id": maintenance_data["aircraft_id"],
            "gvi_status": maintenance_data["gvi_status"],
            "visual_inspection_data": maintenance_data["visual_data"],
            "cargo_hold_condition": maintenance_data["cargo_condition"],
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{system.endpoint}/maintenance/cargo-inspection",
                    json=payload,
                    headers={"X-API-Key": system.credentials["api_key"]},
                    timeout=30.0
                )
                
                return {
                    "success": response.status_code == 200,
                    "response": response.json() if response.status_code == 200 else None,
                    "error": response.text if response.status_code != 200 else None
                }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_flight_data_from_fos(self, flight_number: str) -> Dict[str, Any]:
        """Get flight data from Flight Operations System"""
        system = self.legacy_systems["fos"]
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{system.endpoint}/flights/{flight_number}",
                    auth=(system.credentials["username"], system.credentials["password"]),
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    return {"error": f"Failed to get flight data: {response.text}"}
        except Exception as e:
            return {"error": str(e)}
    
    async def bulk_sync_all_systems(self, flight_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sync data to all relevant legacy systems"""
        results = {}
        
        # Sync to Weight & Balance system
        wb_result = await self.sync_to_legacy_wb_system(flight_data)
        results["weight_balance"] = wb_result
        
        # Sync baggage data to DCS if available
        if "baggage_data" in flight_data:
            for baggage in flight_data["baggage_data"]:
                dcs_result = await self.sync_to_dcs(baggage)
                results[f"dcs_baggage_{baggage['baggage_id']}"] = dcs_result
        
        # Sync maintenance data if available
        if "maintenance_data" in flight_data:
            mro_result = await self.sync_to_maintenance(flight_data["maintenance_data"])
            results["maintenance"] = mro_result
        
        return {
            "sync_timestamp": datetime.now().isoformat(),
            "results": results,
            "success_count": len([r for r in results.values() if r.get("success")]),
            "total_count": len(results)
        }