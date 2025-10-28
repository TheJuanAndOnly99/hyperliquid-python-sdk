#!/usr/bin/env python3
"""
Get Your Telegram Chat ID
Run this AFTER sending a message to your bot
"""

import sys
import requests

if len(sys.argv) < 2:
    print()
    print("="*80)
    print("📱 GET YOUR TELEGRAM CHAT ID")
    print("="*80)
    print()
    print("Usage: python get_telegram_chat_id.py <your_bot_token>")
    print()
    print("Steps:")
    print("1. Create a bot with @BotFather on Telegram")
    print("2. Get your bot token")
    print("3. Send ANY message to your bot (just say 'hi')")
    print("4. Run this script with your bot token")
    print()
    print("Example:")
    print("   poetry run python examples/get_telegram_chat_id.py 123456:ABC-DEF")
    print()
    sys.exit(1)

bot_token = sys.argv[1]

print()
print("="*80)
print("📱 Getting your Telegram Chat ID...")
print("="*80)
print()

try:
    url = "https://api.telegram.org/bot{}/getUpdates".format(bot_token)
    response = requests.get(url, timeout=5)
    
    if response.status_code == 200:
        data = response.json()
        
        if data.get("ok"):
            updates = data.get("result", [])
            
            if len(updates) > 0:
                latest_update = updates[-1]
                chat_id = latest_update["message"]["chat"]["id"]
                chat_type = latest_update["message"]["chat"]["type"]
                
                print("✅ Found your chat ID!")
                print()
                print("="*80)
                print(f"Your Chat ID: {chat_id}")
                print(f"Chat Type: {chat_type}")
                print("="*80)
                print()
                print("Copy this to examples/copy_trade.py:")
                print()
                print(f'TELEGRAM_CHAT_ID = "{chat_id}"')
                print()
                print("="*80)
            else:
                print("❌ No messages found in bot updates")
                print()
                print("Make sure you:")
                print("1. Sent a message to your bot (e.g., 'hi')")
                print("2. Waited a few seconds")
                print("3. Run this script again")
                print()
        else:
            print(f"❌ Error from Telegram API: {data.get('description', 'Unknown error')}")
    else:
        print(f"❌ HTTP Error: {response.status_code}")
        print(f"Response: {response.text}")
        
except requests.exceptions.RequestException as e:
    print(f"❌ Error connecting to Telegram: {e}")
    print()
    print("Check:")
    print("• Your internet connection")
    print("• Your bot token is correct")
except Exception as e:
    print(f"❌ Error: {e}")

