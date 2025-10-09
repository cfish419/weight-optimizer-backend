"""
Feature Flag Management System
Centralized control for Phase 6 advanced features
"""

import os
from typing import Dict, List


class FeatureFlags:
    """Centralized feature flag management"""

    # Phase 6 Feature Flags
    ML_OPTIMIZATION = "ML_OPTIMIZATION"
    COMPLIANCE_REPORTING = "COMPLIANCE_REPORTING"
    PREDICTIVE_ANALYTICS = "PREDICTIVE_ANALYTICS"
    MOBILE_INTEGRATION = "MOBILE_INTEGRATION"
    ADVANCED_INTEGRATIONS = "ADVANCED_INTEGRATIONS"

    @staticmethod
    def is_enabled(feature: str) -> bool:
        """Check if a feature is enabled via environment variable"""
        return os.getenv(f"ENABLE_{feature}", "false").lower() == "true"

    @staticmethod
    def get_enabled_features() -> List[str]:
        """Get list of all enabled features"""
        features = [
            FeatureFlags.ML_OPTIMIZATION,
            FeatureFlags.COMPLIANCE_REPORTING,
            FeatureFlags.PREDICTIVE_ANALYTICS,
            FeatureFlags.MOBILE_INTEGRATION,
            FeatureFlags.ADVANCED_INTEGRATIONS,
        ]
        return [f for f in features if FeatureFlags.is_enabled(f)]

    @staticmethod
    def get_feature_status() -> Dict[str, bool]:
        """Get status of all features"""
        features = [
            FeatureFlags.ML_OPTIMIZATION,
            FeatureFlags.COMPLIANCE_REPORTING,
            FeatureFlags.PREDICTIVE_ANALYTICS,
            FeatureFlags.MOBILE_INTEGRATION,
            FeatureFlags.ADVANCED_INTEGRATIONS,
        ]
        return {f: FeatureFlags.is_enabled(f) for f in features}


class PluginManager:
    """Plugin management system for advanced features"""

    def __init__(self):
        self.plugins = {}
        self.feature_flags = FeatureFlags()

    def register_plugin(self, feature_name: str, plugin_instance):
        """Register a plugin if its feature is enabled"""
        if self.feature_flags.is_enabled(feature_name):
            self.plugins[feature_name] = plugin_instance
            return True
        return False

    def get_plugin(self, feature_name: str):
        """Get plugin instance if available"""
        return self.plugins.get(feature_name)

    def is_plugin_available(self, feature_name: str) -> bool:
        """Check if plugin is loaded and available"""
        return feature_name in self.plugins

    def get_loaded_plugins(self) -> List[str]:
        """Get list of loaded plugin names"""
        return list(self.plugins.keys())


# Global plugin manager instance
plugin_manager = PluginManager()
