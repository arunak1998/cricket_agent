"""
Quick test to verify config.py works correctly
Run: python -m src.config_test
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.config  import config

def test_config():
    """Test configuration loading."""

    print("\n" + "="*60)
    print("🧪 Configuration Test")
    print("="*60)

    if config is None:
        print("❌ Config failed to initialize")
        return False

    # Test 1: Check if config is ready
    print("\n1️⃣  Config ready check:")
    is_ready = config.is_ready()
    print(f"   Status: {'✅ PASS' if is_ready else '❌ FAIL'}")

    # Test 2: Check environment variables
    print("\n2️⃣  Environment variables loaded:")
    for key in config.env_vars:
        print(f"   ✅ {key}")

    if not config.env_vars:
        print("   ⚠️  No environment variables loaded")

    # Test 3: Check API headers
    print("\n3️⃣  API Headers:")
    print(f"   Host: {config.HEADERS.get('x-rapidapi-host')}")
    print(f"   Key Present: {'✅ Yes' if config.HEADERS.get('x-rapidapi-key') else '❌ No'}")

    # Test 4: Check LLM
    print("\n4️⃣  LLM Model:")
    if config.model:
        print(f"   ✅ Model loaded: {type(config.model).__name__}")
    else:
        print("   ⚠️  Model not initialized (check API key)")

    # Test 5: Check cache files
    print("\n5️⃣  Cache Configuration:")
    print(f"   Cache file: {config.CACHE_FILE}")
    print(f"   Daily matches file: {config.DAILY_MATCHES_FILE}")
    print(f"   Match history file: {config.MATCH_HISTORY_FILE}")

    print("\n" + "="*60)
    print("✅ Configuration test complete!")
    print("="*60 + "\n")

    return True


if __name__ == "__main__":
    test_config()
