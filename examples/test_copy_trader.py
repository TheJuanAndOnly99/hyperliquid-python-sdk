#!/usr/bin/env python3
"""
Test Script for Copy Trading Bot
Quick test to verify everything is configured correctly
"""

import sys
import traceback

def test_imports():
    """Test that all required modules can be imported."""
    print("Testing imports...")
    try:
        import example_utils
        from hyperliquid.utils import constants
        from hyperliquid.info import Info
        from hyperliquid.exchange import Exchange
        print("✅ All imports successful")
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        traceback.print_exc()
        return False

def test_config():
    """Test configuration file."""
    print("\nTesting configuration...")
    try:
        import json
        import os
        
        config_path = os.path.join(os.path.dirname(__file__), "config.json")
        if not os.path.exists(config_path):
            print(f"❌ Config file not found: {config_path}")
            return False
        
        with open(config_path) as f:
            config = json.load(f)
        
        if not config.get("secret_key") and not config.get("keystore_path"):
            print("❌ No secret key or keystore path found in config.json")
            return False
        
        print("✅ Configuration file valid")
        return True
    except Exception as e:
        print(f"❌ Config error: {e}")
        traceback.print_exc()
        return False

def test_target_wallet():
    """Test connection to target wallet."""
    print("\nTesting target wallet connection...")
    try:
        from hyperliquid.info import Info
        from hyperliquid.utils import constants
        
        info = Info(base_url=constants.MAINNET_API_URL, skip_ws=True)
        target = "0xc20ac4dc4188660cbf555448af52694ca62b0734"
        
        user_state = info.user_state(target)
        account_value = float(user_state.get("marginSummary", {}).get("accountValue", "0"))
        
        if account_value == 0:
            print("⚠️  Target wallet has no funds")
        else:
            print(f"✅ Target wallet connected (${account_value:,.2f})")
        
        return True
    except Exception as e:
        print(f"❌ Connection error: {e}")
        traceback.print_exc()
        return False

def test_own_account():
    """Test own account connection."""
    print("\nTesting own account connection...")
    try:
        import example_utils
        from hyperliquid.utils import constants
        
        address, info, exchange = example_utils.setup(
            base_url=constants.MAINNET_API_URL, 
            skip_ws=True
        )
        
        user_state = info.user_state(address)
        account_value = float(user_state.get("marginSummary", {}).get("accountValue", "0"))
        
        print(f"✅ Account connected: {address}")
        print(f"   Account value: ${account_value:,.2f}")
        
        if account_value == 0:
            print("⚠️  Warning: Your account has no funds. Fund it to start copy trading.")
        
        return True
    except Exception as e:
        print(f"❌ Connection error: {e}")
        traceback.print_exc()
        return False

def test_copy_percentage():
    """Test copy percentage calculation."""
    print("\nTesting copy percentage calculation...")
    try:
        import example_utils
        from hyperliquid.utils import constants
        
        address, info, exchange = example_utils.setup(
            base_url=constants.MAINNET_API_URL, 
            skip_ws=True
        )
        
        my_state = info.user_state(address)
        target_state = info.user_state("0xc20ac4dc4188660cbf555448af52694ca62b0734")
        
        my_value = float(my_state.get("marginSummary", {}).get("accountValue", "0"))
        target_value = float(target_state.get("marginSummary", {}).get("accountValue", "0"))
        
        if target_value == 0:
            print("❌ Cannot calculate: target has no funds")
            return False
        
        copy_percentage = min(my_value / target_value, 1.0) if my_value > 0 else 0
        
        print(f"   Your value: ${my_value:,.2f}")
        print(f"   Target value: ${target_value:,.2f}")
        print(f"   Copy percentage: {copy_percentage * 100:.2f}%")
        print(f"   Estimated trade value: ${copy_percentage * target_value:,.2f}")
        
        if copy_percentage < 0.0001:
            print("⚠️  Warning: Copy percentage is very small (< 0.01%)")
            print("   Trades may be below minimum size limits")
        
        print("✅ Copy percentage calculated")
        return True
    except Exception as e:
        print(f"❌ Calculation error: {e}")
        traceback.print_exc()
        return False

def main():
    print("="*80)
    print("🧪 Copy Trading Bot - Configuration Test")
    print("="*80)
    
    results = []
    
    results.append(("Imports", test_imports()))
    results.append(("Config", test_config()))
    results.append(("Target Wallet", test_target_wallet()))
    results.append(("Own Account", test_own_account()))
    results.append(("Copy Percentage", test_copy_percentage()))
    
    print("\n" + "="*80)
    print("📊 Test Results:")
    print("="*80)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print("\n" + "="*80)
    if passed == total:
        print(f"✅ All tests passed ({passed}/{total})")
        print("\nYou're ready to start copy trading!")
        print("\nNext steps:")
        print("1. Fund your wallet if needed")
        print("2. Run: ./examples/setup_24_7_service.sh")
        print("3. Monitor: tail -f examples/logs/service_output.log")
    else:
        print(f"⚠️  Some tests failed ({passed}/{total})")
        print("\nPlease fix the issues above before starting copy trading.")
    print("="*80)
    
    sys.exit(0 if passed == total else 1)

if __name__ == "__main__":
    main()

