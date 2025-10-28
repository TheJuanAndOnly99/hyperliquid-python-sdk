"""
Copy Trading Script with WebSocket Support

This version uses WebSocket subscriptions for INSTANT trade detection.
No polling needed - you'll be notified the moment the target wallet trades.
"""

import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime
from typing import Dict, Set

import example_utils

from hyperliquid.utils import constants

# Try importing Telegram notifier (optional)
try:
    from telegram_notifier import TelegramNotifier
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    TelegramNotifier = None

# Configure logging
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    handlers=[
        logging.FileHandler('copy_trade.log'),
        logging.StreamHandler(sys.stdout)
    ]
)


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
    except Exception as e:
        logging.debug(f"Could not send notification: {e}")


class CopyTraderWebsocket:
    """
    WebSocket-based copy trader for instant trade detection.
    Uses WebSocket subscriptions instead of polling for real-time updates.
    """
    
    def __init__(self, target_wallet: str, copy_percentage: float = None, 
                 auto_calculate: bool = True, max_leverage: int = 10, 
                 enable_notifications: bool = True, telegram_config: dict = None):
        """Initialize the WebSocket-based copy trader."""
        self.target_wallet = target_wallet.lower()
        self.max_leverage = max_leverage
        self.enable_notifications = enable_notifications
        
        # Track fills we've processed
        self.processed_fills: Set[str] = set()
        
        # Setup Telegram if configured
        self.telegram = None
        if telegram_config and TELEGRAM_AVAILABLE:
            try:
                self.telegram = TelegramNotifier(
                    telegram_config.get("bot_token"),
                    telegram_config.get("chat_id")
                )
                logging.info("✅ Telegram notifications enabled")
            except Exception as e:
                logging.warning(f"⚠️ Could not initialize Telegram: {e}")
        
        print(f"\n{'='*80}")
        print(f"🚀 Setting up WebSocket copy trading")
        print(f"{'='*80}\n")
        print(f"Target wallet:  {target_wallet}")
        
        # Initialize connection (WITH WebSocket enabled)
        self.address, self.info, self.exchange = example_utils.setup(
            base_url=constants.MAINNET_API_URL, skip_ws=False  # Enable WebSocket!
        )
        
        print(f"Your wallet:    {self.address}")
        
        # Get account values
        my_state = self.info.user_state(self.address)
        target_state = self.info.user_state(target_wallet)
        
        my_value = float(my_state.get("marginSummary", {}).get("accountValue", "0"))
        target_value = float(target_state.get("marginSummary", {}).get("accountValue", "0"))
        
        print(f"\n💰 Account Values:")
        print(f"   Target: ${target_value:,.2f}")
        print(f"   Yours:  ${my_value:,.2f}")
        
        # Calculate copy percentage
        if auto_calculate and copy_percentage is None:
            if my_value > 0 and target_value > 0:
                self.copy_percentage = min(my_value / target_value, 1.0)
                print(f"\n📊 Copy percentage: {self.copy_percentage * 100:.2f}%")
            else:
                self.copy_percentage = 0.01
        elif copy_percentage is not None:
            self.copy_percentage = copy_percentage
        else:
            self.copy_percentage = 0.01
        
        print(f"\n⚠️  IMPORTANT:")
        print(f"   Using WebSocket for INSTANT trade detection")
        print(f"   No polling - real-time updates!")
        print(f"   Press Ctrl+C to stop\n")
        
        # Send startup notification
        if self.telegram:
            self.telegram.notify_startup(target_wallet, self.copy_percentage)
        
        if self.enable_notifications:
            send_notification(
                title="🚀 WebSocket Copy Trading Active",
                message=f"Tracking {target_wallet[:10]}... | Instant detection enabled",
                sound="default"
            )
    
    def handle_user_fill(self, fill_data: dict):
        """Handle a new fill from the target wallet."""
        try:
            # Extract fill information
            coin = fill_data.get("coin")
            side = fill_data.get("side")  # "A" for buy, "B" for sell
            size = float(fill_data.get("sz", 0))
            price = float(fill_data.get("px", 0))
            
            # Skip if we already processed this fill
            fill_id = f"{fill_data.get('hash', '')}_{fill_data.get('time', 0)}"
            if fill_id in self.processed_fills:
                return
            
            self.processed_fills.add(fill_id)
            
            # Determine if buy or sell
            is_buy = (side == "A")
            
            print(f"\n{'='*80}")
            print(f"🎯 INSTANT TRADE DETECTED!")
            print(f"{'='*80}")
            print(f"   Coin: {coin}")
            print(f"   Direction: {'BUY' if is_buy else 'SELL'}")
            print(f"   Size: {size:+.6f}")
            print(f"   Price: ${price:,.2f}")
            print(f"   Hash: {fill_data.get('hash', '')[:16]}...")
            print(f"{'='*80}\n")
            
            # Send notifications
            action = "BOUGHT" if is_buy else "SOLD"
            if self.telegram:
                self.telegram.notify_target_trade(coin, action, size, "BUY" if is_buy else "SELL")
            
            if self.enable_notifications:
                send_notification(
                    title=f"🎯 Target {action}: {coin}",
                    message=f"Size: {size:+.4f} @ ${price:,.2f} | Copying...",
                    sound="Glass"
                )
            
            # Place copy order
            self.place_copy_order(coin, size, is_buy, price)
            
        except Exception as e:
            logging.error(f"Error handling fill: {e}")
    
    def place_copy_order(self, coin: str, size: float, is_buy: bool, price: float):
        """Place an order to copy the target's trade."""
        
        # Calculate copy size
        copy_size = abs(size) * self.copy_percentage
        
        # Round appropriately
        if coin in ["BTC", "ETH"]:
            copy_size = round(copy_size, 4)
        elif coin == "SOL":
            copy_size = round(copy_size, 2)
        else:
            copy_size = round(copy_size, 2)
        
        # Skip if too small
        if copy_size < 0.001:
            print(f"   ⏭️  Skipping {coin}: Copy size {copy_size:.6f} too small")
            return
        
        print(f"\n📤 Executing copy trade:")
        print(f"   Coin: {coin}")
        print(f"   Direction: {'BUY' if is_buy else 'SELL'}")
        print(f"   Size: {copy_size:.6f}")
        print(f"   Price: ${price:,.2f}")
        
        try:
            # Place order
            result = self.exchange.market_open(
                coin,
                is_buy=is_buy,
                sz=copy_size,
                slippage=0.01
            )
            
            if result.get("status") == "ok":
                print(f"   ✅ Order executed!")
                
                trade_value = copy_size * price
                
                # Send success notification
                if self.telegram:
                    self.telegram.notify_trade_executed(coin, "BUY" if is_buy else "SELL", copy_size, trade_value, price)
                
                if self.enable_notifications:
                    send_notification(
                        title=f"✅ Trade Executed: {coin} {'BUY' if is_buy else 'SELL'}",
                        message=f"Size: {copy_size:.4f} @ ${price:,.2f}",
                        sound="Purr"
                    )
            else:
                print(f"   ❌ Order failed: {result.get('response')}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    def start_monitoring(self):
        """Start monitoring via WebSocket."""
        print(f"\n🔌 Connecting to WebSocket for real-time updates...")
        
        def on_fill(msg):
            """Callback when we receive user fill data."""
            data = msg["data"]
            
            # Check if this is for our target wallet
            if data.get("user", "").lower() != self.target_wallet:
                return
            
            fills = data.get("fills", [])
            
            for fill in fills:
                self.handle_user_fill(fill)
        
        # Subscribe to userFills for the target wallet
        subscription = {"type": "userFills", "user": self.target_wallet}
        
        logging.info(f"Subscribing to fills for {self.target_wallet}")
        self.info.subscribe(subscription, on_fill)
        
        print(f"✅ WebSocket connected and subscribed!")
        print(f"⏳ Waiting for trades... (Press Ctrl+C to stop)")
        
        try:
            # Keep the WebSocket connection alive
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n🛑 Stopping WebSocket monitoring...")
            
            # Send shutdown notification
            if self.telegram:
                self.telegram.send_message(
                    f"🛑 <b>Copy Trading Bot Stopped</b>\n\nReason: <code>User stopped</code>\nTime: {time.strftime('%Y-%m-%d %H:%M:%S')}"
                )
            
            if self.enable_notifications:
                send_notification(
                    title="🛑 Bot Stopped",
                    message="WebSocket monitoring stopped",
                    sound="Basso"
                )
        except Exception as e:
            logging.critical(f"Fatal error: {e}")
            raise
        finally:
            # Cleanup WebSocket connection
            if self.info.ws_manager:
                self.info.disconnect_websocket()


def main():
    # ===== CONFIGURATION =====
    TARGET_WALLET = "0xc20ac4dc4188660cbf555448af52694ca62b0734"
    AUTO_CALCULATE = True
    COPY_PERCENTAGE = None
    ENABLE_NOTIFICATIONS = True
    
    # Telegram setup
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    with open(config_path) as f:
        telegram_config_data = json.load(f)
    
    telegram_settings = telegram_config_data.get("telegram", {})
    TELEGRAM_BOT_TOKEN = telegram_settings.get("bot_token")
    TELEGRAM_CHAT_ID = telegram_settings.get("chat_id", "2026256554")
    ENABLE_TELEGRAM = bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)
    
    # Setup Telegram config
    telegram_config = None
    if ENABLE_TELEGRAM and TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        telegram_config = {
            "bot_token": TELEGRAM_BOT_TOKEN,
            "chat_id": TELEGRAM_CHAT_ID
        }
    
    # Create and start the WebSocket copy trader
    trader = CopyTraderWebsocket(
        target_wallet=TARGET_WALLET,
        auto_calculate=AUTO_CALCULATE,
        copy_percentage=COPY_PERCENTAGE,
        max_leverage=10,
        enable_notifications=ENABLE_NOTIFICATIONS,
        telegram_config=telegram_config
    )
    
    # Start monitoring
    trader.start_monitoring()


if __name__ == "__main__":
    main()

