#!/usr/bin/env python3
"""
Test Telegram Notifications
Simple script to verify Telegram integration is working
"""

import sys

try:
    from telegram_notifier import TelegramNotifier
except ImportError:
    print("❌ Error: telegram_notifier.py not found")
    sys.exit(1)


def main():
    print("="*80)
    print("🧪 Testing Telegram Notifications")
    print("="*80)
    print()
    
    # Get credentials
    print("To use Telegram notifications:")
    print("1. Create a bot with @BotFather on Telegram")
    print("2. Get your bot token")
    print("3. Get your chat ID")
    print()
    
    bot_token = input("Enter your Telegram bot token: ").strip()
    if not bot_token:
        print("❌ No bot token provided")
        return
    
    # Get chat ID
    print("\nGetting your chat ID...")
    from telegram_notifier import get_chat_id
    chat_id = get_chat_id(bot_token)
    
    if not chat_id:
        print("\n❌ Could not get chat ID")
        print("Make sure you've sent at least one message to your bot first!")
        return
    
    print(f"\n✅ Found chat ID: {chat_id}")
    print()
    
    # Initialize notifier
    print("Initializing Telegram notifier...")
    notifier = TelegramNotifier(bot_token, chat_id)
    print()
    
    # Test notifications
    print("📤 Sending test notifications...")
    print()
    
    tests = [
        ("Startup", lambda: notifier.notify_startup("0x1234567890", 0.0047)),
        ("Target Trade", lambda: notifier.notify_target_trade("ETH", "BOUGHT", 0.05, "BUY")),
        ("Trade Executed", lambda: notifier.notify_trade_executed("ETH", "BUY", 0.0023, 9.66)),
        ("Trade Failed", lambda: notifier.notify_trade_failed("BTC", "BUY", "Insufficient margin")),
        ("Position Closed", lambda: notifier.notify_position_closed("SOL")),
    ]
    
    for test_name, test_func in tests:
        print(f"   Testing: {test_name}...", end=" ")
        try:
            result = test_func()
            if result:
                print("✅ Sent")
            else:
                print("❌ Failed")
        except Exception as e:
            print(f"❌ Error: {e}")
        print()
    
    print("="*80)
    print("✅ Telegram Test Complete!")
    print("="*80)
    print()
    print("If you received all 5 notifications on Telegram:")
    print("✅ Telegram is working!")
    print()
    print("To enable in copy trading bot:")
    print("1. Open examples/copy_trade.py")
    print("2. Set ENABLE_TELEGRAM = True")
    print("3. Set TELEGRAM_BOT_TOKEN = '" + bot_token + "'")
    print("4. Set TELEGRAM_CHAT_ID = '" + chat_id + "'")
    print()
    print("="*80)


if __name__ == "__main__":
    main()

