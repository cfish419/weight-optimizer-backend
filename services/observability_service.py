"""
Observability Service - Centralized logging, metrics, and monitoring
"""

import json
import logging
import time
from contextlib import contextmanager
from datetime import datetime
from functools import wraps
from typing import Any, Dict, Optional

import boto3


class ObservabilityService:
    """Centralized observability service for metrics, logging, and monitoring"""

    def __init__(self):
        self.cloudwatch = boto3.client("cloudwatch")
        self.logger = self._setup_structured_logging()

    def _setup_structured_logging(self) -> logging.Logger:
        """Setup structured JSON logging"""
        logger = logging.getLogger("weight_optimizer")
        logger.setLevel(logging.INFO)

        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '{"timestamp": "%(asctime)s", "level": "%(levelname)s", '
            '"message": "%(message)s", "module": "%(name)s"}'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger

    def log_business_event(
        self, event_type: str, data: Dict[str, Any], request_id: Optional[str] = None
    ):
        """Log business events with structured data"""
        log_data = {
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": request_id,
            "data": data,
        }
        self.logger.info(json.dumps(log_data))

    def put_metric(
        self,
        metric_name: str,
        value: float,
        unit: str = "Count",
        dimensions: Optional[Dict[str, str]] = None,
    ):
        """Send custom metric to CloudWatch"""
        try:
            metric_data = {
                "MetricName": metric_name,
                "Value": value,
                "Unit": unit,
                "Timestamp": datetime.utcnow(),
            }

            if dimensions:
                metric_data["Dimensions"] = [
                    {"Name": k, "Value": v} for k, v in dimensions.items()
                ]

            self.cloudwatch.put_metric_data(
                Namespace="WeightOptimizer", MetricData=[metric_data]
            )
        except Exception as e:
            self.logger.error(f"Failed to send metric {metric_name}: {e}")

    def track_performance(self, operation_name: str):
        """Decorator to track operation performance"""

        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                request_id = kwargs.get("request_id", "unknown")

                try:
                    result = func(*args, **kwargs)
                    duration = (time.time() - start_time) * 1000

                    # Log performance
                    self.log_business_event(
                        "performance",
                        {
                            "operation": operation_name,
                            "duration_ms": duration,
                            "status": "success",
                        },
                        request_id,
                    )

                    # Send metric
                    self.put_metric(
                        f"{operation_name}Latency", duration, "Milliseconds"
                    )
                    self.put_metric(f"{operation_name}Success", 1)

                    return result

                except Exception as e:
                    duration = (time.time() - start_time) * 1000

                    # Log error
                    self.log_business_event(
                        "error",
                        {
                            "operation": operation_name,
                            "duration_ms": duration,
                            "error": str(e),
                            "status": "error",
                        },
                        request_id,
                    )

                    # Send error metric
                    self.put_metric(f"{operation_name}Error", 1)

                    raise

            return wrapper

        return decorator

    @contextmanager
    def trace_operation(self, operation_name: str, **context):
        """Context manager for tracing operations"""
        start_time = time.time()
        request_id = context.get("request_id", "unknown")

        self.log_business_event(
            "operation_start", {"operation": operation_name, **context}, request_id
        )

        try:
            yield
            duration = (time.time() - start_time) * 1000

            self.log_business_event(
                "operation_complete",
                {
                    "operation": operation_name,
                    "duration_ms": duration,
                    "status": "success",
                },
                request_id,
            )

            self.put_metric(f"{operation_name}Duration", duration, "Milliseconds")

        except Exception as e:
            duration = (time.time() - start_time) * 1000

            self.log_business_event(
                "operation_error",
                {
                    "operation": operation_name,
                    "duration_ms": duration,
                    "error": str(e),
                    "status": "error",
                },
                request_id,
            )

            self.put_metric(f"{operation_name}Error", 1)
            raise

    def track_business_metrics(
        self,
        fuel_savings: float,
        loading_time_reduction: float,
        agent_count: int,
        request_id: Optional[str] = None,
    ):
        """Track key business metrics"""
        metrics = {
            "FuelSavings": fuel_savings,
            "LoadingTimeReduction": loading_time_reduction,
            "ActiveAgents": agent_count,
        }

        for metric_name, value in metrics.items():
            self.put_metric(metric_name, value)

        self.log_business_event("business_metrics", metrics, request_id)


# Global instance
observability = ObservabilityService()
