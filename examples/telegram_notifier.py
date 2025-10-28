"""
Telegram Notifier for Copy Trading Bot
Sends notifications via Telegram when trades are detected
"""

import logging
import requests
from typing import Optional


class TelegramNotifier:
    def __init__(self, bot_token: str, chat_id: str):
        """
        Initialize Telegram notifier.
        
        Args:
            bot_token: Your Telegram bot token from @BotFather
            chat_id: Your Telegram chat/user ID
        """
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        
        # Test connection
        try:
            response = requests.get(f"{self.base_url}/getMe", timeout=5)
            if response.status_code == 200:
                bot_info = response.json()
                logging.info(f"✅ Telegram bot connected: @{bot_info['result']['username']}")
            else:
                logging.error(f"❌ Telegram bot connection failed: {response.text}")
        except Exception as e:
            logging.warning(f"⚠️ Could not connect to Telegram: {e}")
    
    def send_message(self, message: str, parse_mode: str = "HTML") -> bool:
        """
        Send a message to Telegram.
        
        Args:
            message: Message text to send
            parse_mode: HTML or Markdown formatting
        """
        try:
            url = f"{self.base_url}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": parse_mode
            }
            
            response = requests.post(url, json=payload, timeout=5)
            if response.status_code == 200:
                logging.info("✅ Telegram notification sent")
                return True
            else:
                logging.warning(f"⚠️ Telegram notification failed: {response.text}")
                return False
                
        except Exception as e:
            logging.error(f"❌ Error sending Telegram message: {e}")
            return False
    
    def notify_target_trade(self, coin: str, action: str, size_change: float, direction: str):
        """Notify when target makes a trade."""
        emoji = "📈" if direction == "BUY" else "📉"
        message = f"""
{emoji} <b>Target Trade Detected</b>

Coin: <b>{coin}</b>
Action: {action}
Change: {size_change:+.6f}
Direction: <b>{direction}</b>

Bot will copy this trade...
"""
        self.send_message(message)
    
    def notify_trade_executed(self, coin: str, direction: str, size: float, value: Optional[float] = None):
        """Notify when your trade executes successfully."""
        message = f"""
✅ <b>Trade Executed Successfully</b>

Coin: <b>{coin}</b>
Direction: {direction}
Size: {size:.6f}
"""
        if value:
            message += f"Value: ${value:,.2f}"
        
        self.send_message(message)
    
    def notify_trade_failed(self, coin: str, direction: str, error: str):
        """Notify when trade execution fails."""
        message = f"""
❌ <b>Trade Failed</b>

Coin: {coin}
Direction: {direction}
Error: <code>{error}</code>
"""
        self.send_message(message)
    
    def notify_position_closed(self, coin: str):
        """Notify when a position is closed."""
        message = f"""
🔔 <b>Position Closed</b>

Coin: <b>{coin}</b>
Target closed position.
Your position will be closed too.
"""
        self.send_message(message)
    
    def notify_startup(self, target_wallet: str, copy_percentage: float):
        """Notify when bot starts up."""
        message = f"""
🚀 <b>Copy Trading Bot Started</b>

Target: <code>{target_wallet}</code>
Copy %: {copy_percentage * 100:.2f}%

Bot is now monitoring and will copy all new trades.
"""
        self.send_message(message)


def get_chat_id(token: str) -> Optional[str]:
    """
    Helper to get your chat ID.
    Send any message to your bot, then run this.
    """
    try:
        url = f"https://api.telegram.org/bot{token}/getUpdates"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("ok") and len(data.get("result", [])) > 0:
                chat_id = data["result"][-1]["message"]["chat"]["id"]
                print(f"\n✅ Your chat ID is: {chat_id}")
                print(f"Add this to your config!\n")
                return str(chat_id)
            else:
                print("❌ No messages found. Send a message to your bot first.")
                return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        token = sys.argv[1]
        get_chat_id(token)
    else:
        print("Usage: python telegram_notifier.py <your_bot_token>")
        print("\nTo get your bot token:")
        print("1. Talk to @BotFather on Telegram")
        print("2. Create a new bot with /newbot")
        print("3. Get your token")
        print("\nThen run this script with your token to get your chat ID")

