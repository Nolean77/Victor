"""
Configuration module for aOS.

Defines Pydantic v2 configuration models loaded from .env + YAML.
Provides system-wide and per-node configuration schemas.
"""

from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings


class NodeConfig(BaseSettings):
    """Configuration for a single node in the cluster."""

    node_id: str = Field(..., description="Unique identifier for this node")
    role: Literal["desktop", "laptop", "android"] = Field(..., description="Node role in the cluster")
    ip: str = Field(..., description="Local IP address on the mesh network")
    tailscale_ip: str | None = Field(None, description="Tailscale VPN IP address")
    vram_gb: float = Field(..., description="GPU VRAM in gigabytes")
    ram_gb: float = Field(..., description="System RAM in gigabytes")
    gpu_name: str = Field(..., description="GPU model name")
    thermal_limit_c: float = Field(85.0, description="Temperature threshold in Celsius")
    battery_pct: float | None = Field(None, description="Battery percentage (laptop/android only)")

    class Config:
        env_prefix = "AOS_NODE_"


class ThresholdsConfig(BaseSettings):
    """Operational thresholds for the system."""

    # Resource thresholds
    vram_warning_pct: float = Field(80.0, description="VRAM usage warning threshold")
    ram_warning_pct: float = Field(80.0, description="RAM usage warning threshold")
    cpu_warning_pct: float = Field(90.0, description="CPU usage warning threshold")

    # Thermal thresholds
    thermal_warning_c: float = Field(75.0, description="Temperature warning threshold")
    thermal_critical_c: float = Field(85.0, description="Temperature critical threshold")

    # Battery thresholds
    battery_low_pct: float = Field(20.0, description="Low battery warning")
    battery_critical_pct: float = Field(10.0, description="Critical battery threshold")

    # Task thresholds
    max_retries: int = Field(3, description="Maximum task retry attempts")
    retry_storm_threshold: int = Field(5, description="Consecutive failures to trigger stop hook")
    task_timeout_seconds: int = Field(300, description="Default task timeout")

    # Memory thresholds
    context_window_tokens: int = Field(8192, description="Max context window tokens")
    max_traced_history: int = Field(100, description="Max decision traces to retain")


class DirectoriesConfig(BaseSettings):
    """Path configuration for local directories."""

    data_dir: str = Field("./data", description="Base data directory")
    cache_dir: str = Field("./cache", description="Cache directory for compressed contexts")
    models_dir: str = Field("./models", description="Downloaded model storage")
    lora_dir: str = Field("./lora_adapters", description="LoRA adapter storage")
    logs_dir: str = Field("./logs", description="Log output directory")


class SystemConfig(BaseSettings):
    """Root configuration for the entire aOS system."""

    # Node configuration
    nodes: list[NodeConfig] = Field(default_factory=list, description="All nodes in the cluster")

    # Service URLs
    redis_url: str = Field("redis://localhost:6379", description="Redis connection URL")
    mqtt_broker: str = Field("mqtt://localhost:1883", description="MQTT broker URL")
    litellm_base_url: str = Field("http://localhost:4000", description="LiteLLM gateway URL")
    exo_api_url: str = Field("http://localhost:8080", description="Exo cluster API URL")

    # Sub-configurations
    thresholds: ThresholdsConfig = Field(default_factory=ThresholdsConfig)
    dirs: DirectoriesConfig = Field(default_factory=DirectoriesConfig)

    # Global settings
    debug: bool = Field(False, description="Enable debug logging")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field("INFO")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global config instance - load once at startup
_config: SystemConfig | None = None


def get_config() -> SystemConfig:
    """Get the global system configuration, loading if necessary."""
    global _config
    if _config is None:
        _config = SystemConfig()
    return _config


def reload_config() -> SystemConfig:
    """Force reload configuration from sources."""
    global _config
    _config = SystemConfig()
    return _config