"""
Configuration management for the application
"""

import os
import json
from typing import Dict, Any
from utils.constants import CONFIG_FILE, DEFAULT_CONFIG


class ConfigManager:
    """Handles loading and saving application configuration"""

    def __init__(self, config_file: str = CONFIG_FILE):
        self.config_file = config_file
        self.config = self.load()

    def load(self) -> Dict[str, Any]:
        """Load configuration from file"""
        config = DEFAULT_CONFIG.copy()

        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    saved_config = json.load(f)
                    config.update(saved_config)
            except (json.JSONDecodeError, IOError):
                pass

        return config

    def save(self, config_data: Dict[str, Any]) -> bool:
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=4)
            return True
        except IOError:
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value"""
        return self.config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value"""
        self.config[key] = value

    def reset(self) -> Dict[str, Any]:
        """Reset configuration to defaults"""
        self.config = DEFAULT_CONFIG.copy()
        return self.config