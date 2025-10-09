"""
Plugin System for Advanced Features
Phase 6 implementation with non-intrusive design
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class BasePlugin(ABC):
    """Base class for all advanced feature plugins"""

    def __init__(self, name: str):
        self.name = name
        self.enabled = False

    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the plugin. Return True if successful."""
        pass

    @abstractmethod
    def cleanup(self):
        """Cleanup plugin resources"""
        pass

    def is_healthy(self) -> bool:
        """Check if plugin is healthy and operational"""
        return self.enabled


class PluginInterface:
    """Interface for plugin interactions with core system"""

    def __init__(self, plugin: BasePlugin):
        self.plugin = plugin

    def safe_execute(self, method_name: str, *args, **kwargs) -> Optional[Any]:
        """Safely execute plugin method with fallback"""
        try:
            if self.plugin.is_healthy():
                method = getattr(self.plugin, method_name, None)
                if method and callable(method):
                    return method(*args, **kwargs)
        except Exception as e:
            # Log error but don't break core functionality
            import logging
            logging.getLogger(__name__).warning(
                f"Plugin {self.plugin.name} method {method_name} failed: {e}"
            )
        return None
