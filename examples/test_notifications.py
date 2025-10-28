#!/usr/bin/env python3
"""
Test Notification System
Quick test to verify macOS notifications are working
"""

import subprocess
import sys

def send_notification(title: str, message: str, sound: str = "default"):
    """Send a macOS notification."""
    try:
        apple_script = f'''
        display notification "{message}" with title "{title}" sound name "{sound}"
        '''
        subprocess.run(
            ["osascript", "-e", apple_script],
            capture_output=True,
            check=False
        )
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    print("="*60)
    print("🔔 Testing macOS Notifications")
    print("="*60)
    print()
    
    # Test 1: Startup notification
    print("📤 Sending test notification 1: Startup...")
    if send_notification("🚀 Copy Trading Active", "Notifications are working!", "default"):
        print("   ✅ Notification sent")
    else:
        print("   ❌ Failed to send")
    print()
    
    # Test 2: Target move notification
    print("📤 Sending test notification 2: Target move...")
    if send_notification("🎯 Target Wallet: ETH BOUGHT", "Size: +0.1000 | Copying BUY order...", "Glass"):
        print("   ✅ Notification sent")
    else:
        print("   ❌ Failed to send")
    print()
    
    # Test 3: Trade executed notification
    print("📤 Sending test notification 3: Trade executed...")
    if send_notification("✅ Trade Executed: ETH BUY", "Size: 0.0047 | Value: ~$19.69", "Purr"):
        print("   ✅ Notification sent")
    else:
        print("   ❌ Failed to send")
    print()
    
    # Test 4: Trade failed notification
    print("📤 Sending test notification 4: Trade failed...")
    if send_notification("❌ Trade Failed: BTC BUY", "Error: Insufficient margin", "Basso"):
        print("   ✅ Notification sent")
    else:
        print("   ❌ Failed to send")
    print()
    
    print("="*60)
    print("✅ Test Complete!")
    print("="*60)
    print()
    print("You should have seen 4 macOS notifications:")
    print("  1. Startup notification (default sound)")
    print("  2. Target move notification (Glass sound)")
    print("  3. Trade executed notification (Purr sound)")
    print("  4. Trade failed notification (Basso sound)")
    print()
    print("If you didn't see them:")
    print("  1. Check System Preferences > Notifications > Terminal")
    print("  2. Make sure 'Allow Notifications' is enabled")
    print()
    
    # Ask user
    response = input("Did you see all 4 notifications? (y/n): ").lower().strip()
    
    if response in ['y', 'yes']:
        print("\n✅ Great! Notifications are working correctly.")
        print("   Your copy trading bot will now notify you of all trades!")
        sys.exit(0)
    else:
        print("\n⚠️  Notifications may not be working correctly.")
        print("   Check your macOS notification settings.")
        print("   Even without notifications, the bot will still work.")
        sys.exit(1)

if __name__ == "__main__":
    main()

