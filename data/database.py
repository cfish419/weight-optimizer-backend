import asyncio
import json
import os
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

import asyncpg
import boto3
from boto3.dynamodb.conditions import Attr, Key


class DatabaseInterface(ABC):
    """Abstract database interface for weight optimizer"""

    @abstractmethod
    async def get_flight(self, flight_id: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    async def save_flight(self, flight_data: Dict[str, Any]) -> bool:
        pass

    @abstractmethod
    async def get_baggage(self, baggage_id: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    async def save_baggage(self, baggage_data: Dict[str, Any]) -> bool:
        pass

    @abstractmethod
    async def get_aircraft_config(self, aircraft_id: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    async def save_calculation_result(self, result_data: Dict[str, Any]) -> bool:
        pass


class DynamoDBAdapter(DatabaseInterface):
    """DynamoDB implementation for weight optimizer"""

    def __init__(self):
        self.region = os.getenv("AWS_REGION", "us-east-1")
        self.table_prefix = os.getenv("DYNAMODB_TABLE_PREFIX", "weight-optimizer")
        self.endpoint_url = os.getenv("DYNAMODB_ENDPOINT_URL")

        # Initialize DynamoDB resource
        if self.endpoint_url:
            self.dynamodb = boto3.resource(
                "dynamodb", region_name=self.region, endpoint_url=self.endpoint_url
            )
        else:
            self.dynamodb = boto3.resource("dynamodb", region_name=self.region)

        # Table references
        self.flights_table = self.dynamodb.Table(f"{self.table_prefix}-flights")
        self.baggage_table = self.dynamodb.Table(f"{self.table_prefix}-baggage")
        self.aircraft_table = self.dynamodb.Table(f"{self.table_prefix}-aircraft")
        self.calculations_table = self.dynamodb.Table(
            f"{self.table_prefix}-calculations"
        )

    async def get_flight(self, flight_id: str) -> Optional[Dict[str, Any]]:
        try:
            response = self.flights_table.get_item(Key={"flight_id": flight_id})
            return response.get("Item")
        except Exception as e:
            print(f"Error getting flight {flight_id}: {e}")
            return None

    async def save_flight(self, flight_data: Dict[str, Any]) -> bool:
        try:
            flight_data["updated_at"] = datetime.utcnow().isoformat()
            self.flights_table.put_item(Item=flight_data)
            return True
        except Exception as e:
            print(f"Error saving flight: {e}")
            return False

    async def get_baggage(self, baggage_id: str) -> Optional[Dict[str, Any]]:
        try:
            response = self.baggage_table.get_item(Key={"baggage_id": baggage_id})
            return response.get("Item")
        except Exception as e:
            print(f"Error getting baggage {baggage_id}: {e}")
            return None

    async def save_baggage(self, baggage_data: Dict[str, Any]) -> bool:
        try:
            baggage_data["updated_at"] = datetime.utcnow().isoformat()
            self.baggage_table.put_item(Item=baggage_data)
            return True
        except Exception as e:
            print(f"Error saving baggage: {e}")
            return False

    async def get_aircraft_config(self, aircraft_id: str) -> Optional[Dict[str, Any]]:
        try:
            response = self.aircraft_table.get_item(Key={"aircraft_id": aircraft_id})
            return response.get("Item")
        except Exception as e:
            print(f"Error getting aircraft {aircraft_id}: {e}")
            return None

    async def save_calculation_result(self, result_data: Dict[str, Any]) -> bool:
        try:
            result_data["timestamp"] = datetime.utcnow().isoformat()
            result_data["calculation_id"] = (
                f"{result_data['flight_id']}#{result_data['timestamp']}"
            )
            self.calculations_table.put_item(Item=result_data)
            return True
        except Exception as e:
            print(f"Error saving calculation result: {e}")
            return False

    async def get_flight_baggage(self, flight_id: str) -> List[Dict[str, Any]]:
        """Get all baggage for a flight"""
        try:
            response = self.baggage_table.scan(
                FilterExpression=Attr("flight_id").eq(flight_id)
            )
            return response.get("Items", [])
        except Exception as e:
            print(f"Error getting flight baggage: {e}")
            return []


class PostgreSQLAdapter(DatabaseInterface):
    """PostgreSQL implementation for weight optimizer"""

    def __init__(self):
        self.database_url = os.getenv("DATABASE_URL")
        self.pool = None

    async def _get_pool(self):
        if not self.pool:
            self.pool = await asyncpg.create_pool(self.database_url)
        return self.pool

    async def get_flight(self, flight_id: str) -> Optional[Dict[str, Any]]:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            try:
                row = await conn.fetchrow(
                    "SELECT * FROM flights WHERE flight_id = $1", flight_id
                )
                return dict(row) if row else None
            except Exception as e:
                print(f"Error getting flight {flight_id}: {e}")
                return None

    async def save_flight(self, flight_data: Dict[str, Any]) -> bool:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            try:
                await conn.execute(
                    """
                    INSERT INTO flights (flight_id, aircraft_id, flight_number, 
                                       departure_airport, arrival_airport, 
                                       passenger_count, fuel_weight, total_weight,
                                       cg_position, status, updated_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                    ON CONFLICT (flight_id) DO UPDATE SET
                        aircraft_id = EXCLUDED.aircraft_id,
                        passenger_count = EXCLUDED.passenger_count,
                        fuel_weight = EXCLUDED.fuel_weight,
                        total_weight = EXCLUDED.total_weight,
                        cg_position = EXCLUDED.cg_position,
                        status = EXCLUDED.status,
                        updated_at = EXCLUDED.updated_at
                """,
                    flight_data["flight_id"],
                    flight_data.get("aircraft_id"),
                    flight_data.get("flight_number"),
                    flight_data.get("departure_airport"),
                    flight_data.get("arrival_airport"),
                    flight_data.get("passenger_count", 0),
                    flight_data.get("fuel_weight", 0.0),
                    flight_data.get("total_weight", 0.0),
                    flight_data.get("cg_position", 0.0),
                    flight_data.get("status", "active"),
                    datetime.utcnow(),
                )
                return True
            except Exception as e:
                print(f"Error saving flight: {e}")
                return False

    async def get_baggage(self, baggage_id: str) -> Optional[Dict[str, Any]]:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            try:
                row = await conn.fetchrow(
                    "SELECT * FROM baggage WHERE baggage_id = $1", baggage_id
                )
                return dict(row) if row else None
            except Exception as e:
                print(f"Error getting baggage {baggage_id}: {e}")
                return None

    async def save_baggage(self, baggage_data: Dict[str, Any]) -> bool:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            try:
                await conn.execute(
                    """
                    INSERT INTO baggage (baggage_id, flight_id, passenger_id,
                                       weight, compartment, special_handling,
                                       status, updated_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    ON CONFLICT (baggage_id) DO UPDATE SET
                        weight = EXCLUDED.weight,
                        compartment = EXCLUDED.compartment,
                        special_handling = EXCLUDED.special_handling,
                        status = EXCLUDED.status,
                        updated_at = EXCLUDED.updated_at
                """,
                    baggage_data["baggage_id"],
                    baggage_data.get("flight_id"),
                    baggage_data.get("passenger_id"),
                    baggage_data.get("weight", 0.0),
                    baggage_data.get("compartment"),
                    baggage_data.get("special_handling", False),
                    baggage_data.get("status", "checked"),
                    datetime.utcnow(),
                )
                return True
            except Exception as e:
                print(f"Error saving baggage: {e}")
                return False

    async def get_aircraft_config(self, aircraft_id: str) -> Optional[Dict[str, Any]]:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            try:
                row = await conn.fetchrow(
                    "SELECT * FROM aircraft_configs WHERE aircraft_id = $1", aircraft_id
                )
                return dict(row) if row else None
            except Exception as e:
                print(f"Error getting aircraft {aircraft_id}: {e}")
                return None

    async def save_calculation_result(self, result_data: Dict[str, Any]) -> bool:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            try:
                await conn.execute(
                    """
                    INSERT INTO calculation_results (flight_id, calculation_type,
                                                   result_data, timestamp)
                    VALUES ($1, $2, $3, $4)
                """,
                    result_data["flight_id"],
                    result_data.get("calculation_type", "weight_balance"),
                    json.dumps(result_data),
                    datetime.utcnow(),
                )
                return True
            except Exception as e:
                print(f"Error saving calculation result: {e}")
                return False


class DatabaseFactory:
    """Factory for creating database adapters based on configuration"""

    @staticmethod
    def create_database() -> DatabaseInterface:
        db_type = os.getenv("DATABASE_TYPE", "dynamodb").lower()

        if db_type == "dynamodb":
            return DynamoDBAdapter()
        elif db_type == "postgresql":
            return PostgreSQLAdapter()
        else:
            raise ValueError(f"Unsupported database type: {db_type}")


# Global database instance
_db_instance = None


def get_database() -> DatabaseInterface:
    """Get database instance (singleton pattern)"""
    global _db_instance
    if _db_instance is None:
        _db_instance = DatabaseFactory.create_database()
    return _db_instance
