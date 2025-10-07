"""
Configuration management for the itinerary planner system.
Loads settings from environment variables and config files.
"""

import os
import yaml
from typing import Dict, Any
from pathlib import Path


_config_cache: Dict[str, Any] = None


def load_config() -> Dict[str, Any]:
    """
    Load configuration from config.yaml and environment variables.
    
    Environment variables take precedence over config file.
    
    Returns:
        Configuration dictionary
    """
    global _config_cache
    
    if _config_cache is not None:
        return _config_cache
    
    # Default configuration
    config = {
        "llm": {
            "model": "gpt-4",
            "temperature": 0.7,
            "max_tokens": 2000
        },
        "api_keys": {
            "openai": os.getenv("OPENAI_API_KEY", ""),
            "amadeus": os.getenv("AMADEUS_API_KEY", ""),
            "booking": os.getenv("BOOKING_API_KEY", "")
        },
        "database": {
            "supabase_url": os.getenv("SUPABASE_URL", ""),
            "supabase_key": os.getenv("SUPABASE_KEY", "")
        },
        "system": {
            "log_level": os.getenv("LOG_LEVEL", "INFO"),
            "max_retries": 3,
            "timeout": 30
        }
    }
    
    # Try to load from config.yaml
    config_path = Path(__file__).parent / "config.yaml"
    if config_path.exists():
        try:
            with open(config_path, "r") as f:
                file_config = yaml.safe_load(f)
                if file_config:
                    # Merge configurations (env vars take precedence)
                    config = _deep_merge(config, file_config)
        except Exception as e:
            print(f"Warning: Could not load config.yaml: {e}")
    
    _config_cache = config
    return config


def get_config() -> Dict[str, Any]:
    """Get cached configuration."""
    if _config_cache is None:
        return load_config()
    return _config_cache


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two dictionaries."""
    result = base.copy()
    
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    
    return result


def validate_config(config: Dict[str, Any]) -> bool:
    """
    Validate configuration has required fields.
    
    Args:
        config: Configuration dictionary
    
    Returns:
        True if valid, False otherwise
    """
    required_keys = [
        "llm.model",
        "api_keys.openai"
    ]
    
    for key_path in required_keys:
        parts = key_path.split(".")
        current = config
        
        for part in parts:
            if part not in current:
                print(f"Missing required config: {key_path}")
                return False
            current = current[part]
        
        # Check if value is empty
        if not current:
            print(f"Empty required config: {key_path}")
            return False
    
    return True