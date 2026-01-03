"""
Performance configuration and optimization settings
"""

import json
import os
from typing import Dict, Any
from dataclasses import dataclass, asdict, field

PERFORMANCE_CONFIG_FILE = 'performance_config.json'


@dataclass
class PerformanceConfig:
    """Performance settings dataclass"""

    # Parallel Downloads
    max_concurrent_downloads: int = 3
    enabled_parallel: bool = True

    # Connection Settings
    connection_retries: int = 5
    retry_delay: float = 1.0
    request_timeout: int = 60

    # Chunk/Buffer Settings
    download_chunk_size: int = 512  # KB
    buffer_size: int = 1024  # KB

    # Rate Limiting
    delay_between_files: float = 0.5  # seconds
    delay_between_batches: float = 2.0  # seconds
    batch_size: int = 10  # files per batch
    auto_handle_flood_wait: bool = True

    # Telegram DC Settings
    use_ipv6: bool = False

    # Progress Settings
    show_file_progress: bool = True
    progress_update_interval: float = 0.5  # seconds

    # Advanced
    keep_connection_alive: bool = True
    max_retries_per_file: int = 3
    skip_failed_files: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PerformanceConfig':
        """Create from dictionary"""
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered_data)


class PerformanceConfigManager:
    """Manager for performance configuration"""

    def __init__(self, config_file: str = PERFORMANCE_CONFIG_FILE):
        self.config_file = config_file
        self.config = self.load()

    def load(self) -> PerformanceConfig:
        """Load configuration from file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    return PerformanceConfig.from_dict(data)
            except (json.JSONDecodeError, IOError):
                pass

        return PerformanceConfig()

    def save(self) -> bool:
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config.to_dict(), f, indent=4)
            return True
        except IOError:
            return False

    def reset(self) -> PerformanceConfig:
        """Reset to default configuration"""
        self.config = PerformanceConfig()
        return self.config

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value"""
        return getattr(self.config, key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value"""
        if hasattr(self.config, key):
            setattr(self.config, key, value)


# Preset configurations
PERFORMANCE_PRESETS = {
    'conservative': PerformanceConfig(
        max_concurrent_downloads=1,
        enabled_parallel=False,
        download_chunk_size=256,
        delay_between_files=1.0,
        delay_between_batches=5.0,
        batch_size=5
    ),
    'balanced': PerformanceConfig(
        max_concurrent_downloads=3,
        enabled_parallel=True,
        download_chunk_size=512,
        delay_between_files=0.3,
        delay_between_batches=1.0,
        batch_size=10
    ),
    'aggressive': PerformanceConfig(
        max_concurrent_downloads=5,
        enabled_parallel=True,
        download_chunk_size=1024,
        delay_between_files=0.1,
        delay_between_batches=0.5,
        batch_size=20
    ),
    'maximum': PerformanceConfig(
        max_concurrent_downloads=8,
        enabled_parallel=True,
        download_chunk_size=2048,
        delay_between_files=0.05,
        delay_between_batches=0.2,
        batch_size=50
    )
}

def get_preset(name: str) -> PerformanceConfig:
    """Get a preset configuration"""
    return PERFORMANCE_PRESETS.get(name, PERFORMANCE_PRESETS['balanced'])