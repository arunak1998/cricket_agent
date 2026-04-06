"""
Simple Cache Manager - JSON-based cache with error handling.
Extracted from notebook patterns for clean, modular use.
"""

import os
import json
import logging
from pathlib import Path
from typing import Optional, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Simple JSON-based cache manager with atomic writes and cleanup.

    Features:
    - Load/save JSON cache files
    - Atomic writes (temp file pattern)
    - Timestamp tracking
    - TTL-based cleanup
    - Comprehensive error handling
    """

    def __init__(self, cache_file: str):
        """
        Initialize cache manager.

        Args:
            cache_file: Path to JSON cache file (created if not exists)
        """
        self.cache_file = cache_file
        self.cache_data = self._load()
        logger.info(f"✅ CacheManager initialized: {self.cache_file} ({self.size()} entries)")

    def _load(self) -> dict:
        """Load cache from JSON file. Returns fresh dict if file missing/corrupt."""
        if not os.path.exists(self.cache_file):
            logger.info(f"ℹ️ Cache file '{self.cache_file}' not found. Starting fresh.")
            return {}

        try:
            with open(self.cache_file, "r") as f:
                data = json.load(f)
                logger.info(f"✅ Cache loaded: {len(data)} entries")
                return data
        except json.JSONDecodeError as e:
            logger.error(f"❌ Cache corrupted (JSON decode error): {e}. Starting fresh.")
            return {}
        except IOError as e:
            logger.error(f"❌ Failed to read cache: {e}. Starting fresh.")
            return {}
        except Exception as e:
            logger.error(f"❌ Unexpected error loading cache: {e}. Starting fresh.")
            return {}

    def _save(self) -> None:
        """Save cache to JSON file with atomic writes (temp file pattern)."""
        temp_file = f"{self.cache_file}.tmp"
        try:
            # Write to temp file first
            with open(temp_file, "w") as f:
                json.dump(self.cache_data, f, indent=4)
            # Atomic rename
            os.replace(temp_file, self.cache_file)
            logger.debug(f"✅ Cache saved: {self.size()} entries")
        except IOError as e:
            logger.error(f"❌ Failed to save cache: {e}")
            # Cleanup temp file
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception:
                pass
        except Exception as e:
            logger.error(f"❌ Unexpected error saving cache: {e}")
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception:
                pass

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached data or None if not found
        """
        try:
            entry = self.cache_data.get(key)
            if entry and isinstance(entry, dict) and "data" in entry:
                return entry["data"]
            return entry
        except Exception as e:
            logger.warning(f"⚠️ Error retrieving cache key '{key}': {e}")
            return None

    def set(self, key: str, value: Any) -> None:
        """
        Set value in cache with timestamp. Auto-saves.

        Args:
            key: Cache key
            value: Data to cache
        """
        try:
            self.cache_data[key] = {
                "data": value,
                "timestamp": datetime.now().isoformat()
            }
            self._save()
        except TypeError as e:
            logger.error(f"❌ Failed to serialize cache value for '{key}': {e}")
        except Exception as e:
            logger.error(f"❌ Error setting cache key '{key}': {e}")

    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        try:
            return key in self.cache_data
        except Exception as e:
            logger.warning(f"⚠️ Error checking cache key '{key}': {e}")
            return False

    def size(self) -> int:
        """Return number of cache entries."""
        try:
            return len(self.cache_data)
        except Exception:
            return 0

    def clear(self) -> None:
        """Clear all cache entries."""
        try:
            self.cache_data = {}
            self._save()
            logger.info("✅ Cache cleared")
        except Exception as e:
            logger.error(f"❌ Error clearing cache: {e}")

    def cleanup(self, days: int = 7) -> int:
        """
        Remove cache entries older than X days.

        Args:
            days: Age threshold in days

        Returns:
            Number of entries removed
        """
        keys_to_remove = []
        try:
            cutoff_date = datetime.now() - timedelta(days=days)

            for key, entry in self.cache_data.items():
                try:
                    if isinstance(entry, dict) and "timestamp" in entry:
                        entry_date = datetime.fromisoformat(entry["timestamp"])
                        if entry_date < cutoff_date:
                            keys_to_remove.append(key)
                except ValueError as e:
                    logger.warning(f"⚠️ Invalid timestamp for '{key}': {e}")
                    keys_to_remove.append(key)
                except Exception as e:
                    logger.warning(f"⚠️ Error processing entry '{key}': {e}")

            # Remove old entries
            for key in keys_to_remove:
                del self.cache_data[key]

            if keys_to_remove:
                self._save()
                logger.info(f"✅ Cleanup removed {len(keys_to_remove)} old entries")

            return len(keys_to_remove)

        except Exception as e:
            logger.error(f"❌ Error during cleanup: {e}")
            return 0

    def __repr__(self) -> str:
        """String representation."""
        return f"CacheManager(file={self.cache_file}, entries={self.size()})"
