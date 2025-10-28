"""
Copy Trading Script for Hyperliquid

This script monitors a target wallet and copies their trades automatically.
Configure the target wallet address and copy percentage below.
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
    """
    Send a macOS notification.
    
    Args:
        title: Notification title
        message: Notification message
        sound: Sound name (default, Glass, etc.)
    """
    try:
        # Use osascript to send macOS notification
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


class CopyTrader:
    def __init__(self, target_wallet: str, copy_percentage: float = None, auto_calculate: bool = True, max_leverage: int = 10, enable_notifications: bool = True, telegram_config: dict = None):
        """
        Initialize the copy trader.
        
        Args:
            target_wallet: The wallet address to copy from (e.g., "0xc20ac4dc4188660cbf555448af52694ca62b0734")
            copy_percentage: Percentage of the target's position size to copy (0.0 to 1.0)
            auto_calculate: If True, automatically calculate copy percentage based on account values
            max_leverage: Maximum leverage to use (default: 10x like target wallet)
            enable_notifications: Send macOS notifications on trades (default: True)
            telegram_config: Dict with 'bot_token' and 'chat_id' for Telegram notifications
        """
        self.target_wallet = target_wallet.lower()
        self.max_leverage = max_leverage
        self.enable_notifications = enable_notifications
        
        # Setup Telegram notifier if configured
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
        
        # Track known fills to avoid duplicate execution
        self.known_fills: Set[str] = set()
        
        # Track last seen positions
        self.last_positions: Dict[str, Dict] = {}
        
        # Initialize connection
        print(f"\n{'='*80}")
        print(f"🚀 Setting up copy trading")
        print(f"{'='*80}\n")
        print(f"Target wallet:  {target_wallet}")
        
        self.address, self.info, self.exchange = example_utils.setup(
            base_url=constants.MAINNET_API_URL, skip_ws=True
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
                self.copy_percentage = min(my_value / target_value, 1.0)  # Don't go over 100%
                print(f"\n📊 Automatically calculated copy percentage: {self.copy_percentage * 100:.2f}%")
                print(f"   This means you'll trade ~{self.copy_percentage * target_value:,.2f} worth of positions")
            else:
                print("\n⚠️  Warning: Cannot auto-calculate, using manual percentage")
                self.copy_percentage = 0.01  # Default to 1% for safety
        elif copy_percentage is not None:
            self.copy_percentage = copy_percentage
            print(f"\n📊 Using manual copy percentage: {copy_percentage * 100}%")
            estimated_trade_value = copy_percentage * target_value
            print(f"   This means you'll trade ~${estimated_trade_value:,.2f} worth of positions")
        else:
            self.copy_percentage = 0.01  # Safe default
            print(f"\n⚠️  Using safe default copy percentage: {self.copy_percentage * 100}%")
        
        # Safety warning
        print(f"\n⚠️  IMPORTANT WARNINGS:")
        print(f"   1. Copy trading involves significant risk")
        print(f"   2. You can lose your entire ${my_value:,.2f}")
        print(f"   3. Target is using ~10x leverage (very high risk)")
        print(f"   4. Price slippage may affect your execution")
        print(f"   5. You will be copying both wins AND losses")
        print(f"\n{'='*80}\n")
        
        # Send startup notifications
        if self.telegram:
            self.telegram.notify_startup(target_wallet, self.copy_percentage)
        
        if self.enable_notifications:
            send_notification(
                title="🚀 Copy Trading Active",
                message=f"Tracking wallet {target_wallet[:10]}... | Copying {self.copy_percentage * 100:.2f}%",
                sound="default"
            )
    
    def get_current_positions(self) -> Dict[str, Dict]:
        """Get current positions for the target wallet."""
        try:
            user_state = self.info.user_state(self.target_wallet)
            positions = {}
            for pos in user_state["assetPositions"]:
                position = pos["position"]
                positions[position["coin"]] = position
            return positions
        except Exception as e:
            print(f"Error fetching positions: {e}")
            return {}
    
    def get_my_positions(self) -> Dict[str, float]:
        """Get your current positions."""
        try:
            my_state = self.info.user_state(self.address)
            positions = {}
            for pos in my_state.get("assetPositions", []):
                coin = pos["position"].get("coin")
                size = float(pos["position"].get("szi", 0))
                if abs(size) > 0.001:  # Only track meaningful positions
                    positions[coin] = size
            return positions
        except Exception as e:
            logging.warning(f"Error fetching my positions: {e}")
            return {}
    
    def place_copy_order(self, coin: str, current_size: float, prev_size: float):
        """
        Place an order to match the target's position change.
        
        Args:
            coin: The coin symbol (e.g., "BTC", "ETH")
            current_size: Current position size in the target wallet
            prev_size: Previous position size
        """
        # Calculate the size change
        size_diff = current_size - prev_size
        
        if abs(size_diff) < 0.0001:  # Ignore very small changes
            return
        
        # Apply copy percentage
        copy_size = abs(size_diff) * self.copy_percentage
        is_buy = size_diff > 0
        
        # If this is a SELL and you don't have a position, skip it
        if not is_buy:  # Selling
            my_positions = self.get_my_positions()
            my_position_size = my_positions.get(coin, 0)
            
            if abs(my_position_size) < 0.001:  # You don't have this position
                print(f"\n⏭️  Skipping SELL for {coin}: You don't have a position to sell")
                logging.info(f"Skipping SELL order for {coin} - no position held")
                return
        
        # Round to reasonable precision to avoid issues with tiny positions
        # For BTC/ETH we need at least 0.001
        min_size = 0.001 if coin in ["BTC", "ETH", "BNB", "SOL"] else 0.01
        
        if copy_size < min_size:
            print(f"\n⏭️  Skipping {coin}: Copy size {copy_size:.6f} is below minimum {min_size}")
            return
        
        # Round to appropriate decimals
        if coin in ["BTC", "ETH"]:
            copy_size = round(copy_size, 4)
        elif coin == "SOL":
            copy_size = round(copy_size, 2)
        else:
            copy_size = round(copy_size, 2)
        
        try:
            # Send notification when target makes a move
            action = "BOUGHT" if is_buy else "SOLD"
            size_text = f"{abs(size_diff):+.4f}"
            
            if self.telegram:
                self.telegram.notify_target_trade(coin, action, size_diff, "BUY" if is_buy else "SELL")
            
            if self.enable_notifications:
                send_notification(
                    title=f"🎯 Target Wallet: {coin} {action}",
                    message=f"Size: {size_text} | Copying {'BUY' if is_buy else 'SELL'} order...",
                    sound="Glass"
                )
            
            print(f"\n📊 Position change detected for {coin}:")
            print(f"   Previous size: {prev_size}")
            print(f"   Current size:  {current_size}")
            print(f"   Change: {size_diff:+.6f}")
            print(f"   Copy size: {copy_size} ({self.copy_percentage * 100}% of change)")
            print(f"   Direction: {'BUY' if is_buy else 'SELL'}")
            
            # Get current price to estimate trade value
            try:
                coin_data = self.info.name_to_coin[coin]
                mids = self.info.all_mids()
                current_price = float(mids.get(coin_data, 0))
                trade_value = copy_size * current_price
                print(f"   Estimated value: ${trade_value:,.2f}")
            except:
                pass
            
            # Ask for confirmation (optional - you can remove this for fully automatic trading)
            user_input = input("\n⚠️  Execute this trade? (y/n/q for quit): ").lower().strip()
            if user_input in ['n', 'no']:
                print("   ⏭️  Trade skipped by user")
                return
            if user_input in ['q', 'quit']:
                print("\n🛑 Stopping copy trading by user request")
                return
            
            # Place market order
            result = self.exchange.market_open(
                coin, 
                is_buy=is_buy, 
                sz=copy_size,
                slippage=0.01  # 1% slippage
            )
            
            if result.get("status") == "ok":
                print(f"   ✅ Order placed successfully!")
                print(f"   Status: {json.dumps(result, indent=2)}")
                
                trade_value = copy_size * current_price if 'current_price' in locals() else 0
                
                # Send success notifications
                if self.telegram:
                    self.telegram.notify_trade_executed(coin, "BUY" if is_buy else "SELL", copy_size, trade_value)
                
                if self.enable_notifications:
                    send_notification(
                        title=f"✅ Trade Executed: {coin} {'BUY' if is_buy else 'SELL'}",
                        message=f"Size: {copy_size:.4f} | Value: ~${trade_value:,.2f}",
                        sound="Purr"
                    )
            else:
                print(f"   ❌ Order failed: {result.get('response')}")
                
                error_msg = result.get('response', 'Unknown error')
                
                # Send failure notifications
                if self.telegram:
                    self.telegram.notify_trade_failed(coin, "BUY" if is_buy else "SELL", error_msg)
                
                if self.enable_notifications:
                    send_notification(
                        title=f"❌ Trade Failed: {coin} {'BUY' if is_buy else 'SELL'}",
                        message=f"Error: {error_msg}",
                        sound="Basso"
                    )
                
        except Exception as e:
            print(f"   ❌ Error placing order: {e}")
    
    def monitor_positions(self):
        """Monitor position changes and execute copy trades."""
        print(f"⏰ Last checked: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        current_positions = self.get_current_positions()
        
        # If this is the first check, decide whether to copy existing positions
        is_first_check = len(self.last_positions) == 0
        
        if is_first_check:
            if hasattr(self, 'copy_existing_positions') and self.copy_existing_positions:
                print("\n📊 First check - will copy existing positions...")
            else:
                print("\n⚠️  First check - recording current positions (won't copy existing positions)")
                print("   Future changes will be copied...")
        
        # Compare with previous positions
        for coin, position in current_positions.items():
            current_size = float(position.get("szi", 0))
            prev_size = float(self.last_positions.get(coin, {}).get("szi", 0))
            
            # On first check, only copy if explicitly enabled
            if is_first_check:
                if hasattr(self, 'copy_existing_positions') and self.copy_existing_positions:
                    logging.info(f"Copying existing position in {coin} (size: {current_size})")
                else:
                    logging.info(f"Skipping existing position in {coin} (size: {current_size})")
                    continue
            
            # Check if position changed
            if abs(current_size - prev_size) > 0.01:
                self.place_copy_order(coin, current_size, prev_size)
        
        # Handle positions that were closed
        for coin in self.last_positions:
            if coin not in current_positions:
                # Position was closed, close ours too
                try:
                    # Send notifications
                    if self.telegram:
                        self.telegram.notify_position_closed(coin)
                    
                    if self.enable_notifications:
                        send_notification(
                            title=f"🔔 Position Closed: {coin}",
                            message="Target closed position. Closing yours too...",
                            sound="Glass"
                        )
                    
                    print(f"\n📊 Position closed for {coin}")
                    self.exchange.market_close(coin)
                    print(f"   ✅ Closed position in {coin}")
                except Exception as e:
                    print(f"   ❌ Error closing position: {e}")
        
        # Update last known positions
        self.last_positions = current_positions
        
        # Print current status
        if current_positions:
            print("\n📈 Current positions being tracked:")
            for coin, position in current_positions.items():
                size = float(position.get("szi", 0))
                entry_px = position.get("entryPx", "N/A")
                pnl = position.get("unrealizedPnl", "0")
                print(f"   {coin}: {size:+.4f} @ {entry_px} (PnL: {pnl})")
        else:
            print("   No open positions")
    
    def start_monitoring(self, interval: int = 5):
        """
        Start monitoring the target wallet.
        
        Args:
            interval: Check interval in seconds (default: 5)
        """
        logging.info(f"\n🔄 Starting continuous monitoring...")
        logging.info(f"   Checking every {interval} seconds")
        logging.info("   Press Ctrl+C to stop\n")
        
        consecutive_errors = 0
        max_consecutive_errors = 5
        
        try:
            while True:
                try:
                    self.monitor_positions()
                    consecutive_errors = 0  # Reset on successful check
                except Exception as e:
                    consecutive_errors += 1
                    logging.error(f"Error during monitoring (attempt {consecutive_errors}/{max_consecutive_errors}): {e}")
                    
                    if consecutive_errors >= max_consecutive_errors:
                        logging.critical(f"Too many consecutive errors. Exiting to prevent issues.")
                        raise
                    
                    # Wait before retry
                    time.sleep(10)
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            logging.info("\n\n🛑 Monitoring stopped by user")
        except Exception as e:
            logging.critical(f"Fatal error: {e}")
            raise


def main():
    # ===== CONFIGURATION =====
    # Target wallet to copy from
    TARGET_WALLET = "0xc20ac4dc4188660cbf555448af52694ca62b0734"
    
    # AUTO-CALCULATE: Automatically calculate copy percentage based on account values
    # If True: Uses (your account value / target account value) as the copy percentage
    # If False: Uses manual COPY_PERCENTAGE below
    AUTO_CALCULATE = True
    
    # Manual copy percentage (only used if AUTO_CALCULATE is False)
    # 1.0 = 100%, 0.5 = 50%, 0.1 = 10%, etc.
    COPY_PERCENTAGE = None  # Set to a value like 0.01 for 1% if you want manual control
    
    # Check interval in seconds
    CHECK_INTERVAL = 10  # Check every 10 seconds
    
    # ==========================
    
    # Enable macOS notifications (set to False to disable)
    ENABLE_NOTIFICATIONS = True
    
    # Enable Telegram notifications - loaded from config.json
    # Add your bot token to examples/config.json under "telegram" section
    import json
    import os
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    with open(config_path) as f:
        telegram_config_data = json.load(f)
    
    telegram_settings = telegram_config_data.get("telegram", {})
    TELEGRAM_BOT_TOKEN = telegram_settings.get("bot_token")
    TELEGRAM_CHAT_ID = telegram_settings.get("chat_id", "2026256554")
    ENABLE_TELEGRAM = bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)
    
    # Copy existing positions on startup (True) or only future trades (False)
    # True  = Copy all existing positions when bot starts
    # False = Skip existing positions, only copy NEW trades
    COPY_EXISTING_POSITIONS = False
    
    # ==========================
    
    # Setup Telegram config
    telegram_config = None
    if ENABLE_TELEGRAM and TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        telegram_config = {
            "bot_token": TELEGRAM_BOT_TOKEN,
            "chat_id": TELEGRAM_CHAT_ID
        }
    
    # Create and start the copy trader
    trader = CopyTrader(
        target_wallet=TARGET_WALLET,
        auto_calculate=AUTO_CALCULATE,
        copy_percentage=COPY_PERCENTAGE,
        max_leverage=10,
        enable_notifications=ENABLE_NOTIFICATIONS,
        telegram_config=telegram_config
    )
    
    # Set whether to copy existing positions
    trader.copy_existing_positions = COPY_EXISTING_POSITIONS
    
    # Start monitoring
    trader.start_monitoring(interval=CHECK_INTERVAL)


if __name__ == "__main__":
    main()

