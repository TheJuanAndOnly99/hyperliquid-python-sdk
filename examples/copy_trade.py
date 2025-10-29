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
    def __init__(self, target_wallet: str, copy_percentage: float = None, auto_calculate: bool = True, max_leverage: int = 10, enable_notifications: bool = True, telegram_config: dict = None, use_isolated_margin: bool = True, match_existing_if_similar: bool = True, price_deviation_threshold: float = 0.005, pnl_percent_threshold: float = 0.003):
        """
        Initialize the copy trader.
        
        Args:
            target_wallet: The wallet address to copy from (e.g., "0xc20ac4dc4188660cbf555448af52694ca62b0734")
            copy_percentage: Percentage of the target's position size to copy (0.0 to 1.0)
            auto_calculate: If True, automatically calculate copy percentage based on account values
            max_leverage: Maximum leverage to use (default: 10x like target wallet)
            enable_notifications: Send macOS notifications on trades (default: True)
            telegram_config: Dict with 'bot_token' and 'chat_id' for Telegram notifications
            use_isolated_margin: Use isolated margin instead of cross margin (default: True)
            match_existing_if_similar: If True, attempt to match existing positions on startup when conditions are similar
            price_deviation_threshold: Max relative deviation between mid and entryPx to consider "similar" (e.g., 0.005 = 0.5%)
            pnl_percent_threshold: Max |PnL%| relative to notional to consider "similar" (e.g., 0.003 = 0.3%)
        """
        self.target_wallet = target_wallet.lower()
        self.max_leverage = max_leverage
        self.enable_notifications = enable_notifications
        self.use_isolated_margin = use_isolated_margin
        self.match_existing_if_similar = match_existing_if_similar
        self.price_deviation_threshold = price_deviation_threshold
        self.pnl_percent_threshold = pnl_percent_threshold
        
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
        
        # Print margin mode
        margin_mode = "ISOLATED" if self.use_isolated_margin else "CROSS"
        print(f"\n🔧 Margin Mode: {margin_mode}")
        if self.use_isolated_margin:
            print(f"   Using isolated margin with {self.max_leverage}x leverage")
            print(f"   Each position will have dedicated margin allocated")
        else:
            print(f"   Using cross margin with {self.max_leverage}x leverage")
            print(f"   All positions share the same margin pool")
        
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
        if self.use_isolated_margin:
            print(f"   6. Using isolated margin: each position is isolated and funded separately")
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
        
        self._startup_notified = True
    
    def _should_match_existing_position(self, coin: str, position: Dict) -> bool:
        """Decide if an existing target position should be matched on startup based on market similarity.

        Conditions (any one passing is sufficient):
        - Current mid is within price_deviation_threshold of target entryPx
        - |unrealized PnL %| is within pnl_percent_threshold relative to entry notional
        """
        try:
            entry_px = float(position.get("entryPx", 0) or 0)
            szi = float(position.get("szi", 0) or 0)
            unrealized_pnl = float(position.get("unrealizedPnl", 0) or 0)

            # Fetch current mid price for coin
            current_price = None
            try:
                coin_data = self.info.name_to_coin[coin]
                mids = self.info.all_mids()
                current_price = float(mids.get(coin_data, 0))
            except Exception:
                current_price = None

            price_ok = False
            if current_price and entry_px > 0:
                rel_dev = abs(current_price - entry_px) / entry_px
                price_ok = rel_dev <= self.price_deviation_threshold

            pnl_ok = False
            notional = abs(szi) * entry_px
            if notional > 0:
                pnl_pct = abs(unrealized_pnl) / notional
                pnl_ok = pnl_pct <= self.pnl_percent_threshold

            return bool(price_ok or pnl_ok)
        except Exception:
            return False

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
    
    def adjust_copy_percentage(self):
        """
        Dynamically adjust copy percentage based on current account values.
        This ensures we maintain relative position sizing as account values change.
        """
        try:
            my_state = self.info.user_state(self.address)
            target_state = self.info.user_state(self.target_wallet)
            
            my_value = float(my_state.get("marginSummary", {}).get("accountValue", "0"))
            target_value = float(target_state.get("marginSummary", {}).get("accountValue", "0"))
            
            if my_value > 0 and target_value > 0:
                new_copy_percentage = min(my_value / target_value, 1.0)  # Don't go over 100%
                
                # Only log if there's a significant change (more than 1%)
                change = abs(new_copy_percentage - self.copy_percentage)
                if change > 0.01:
                    old_pct = self.copy_percentage * 100
                    new_pct = new_copy_percentage * 100
                    logging.info(f"📊 Adjusting copy percentage: {old_pct:.2f}% → {new_pct:.2f}% "
                                f"(Your value: ${my_value:,.2f}, Target: ${target_value:,.2f})")
                
                self.copy_percentage = new_copy_percentage
            else:
                logging.warning("Could not adjust copy percentage: invalid account values")
        except Exception as e:
            logging.warning(f"Error adjusting copy percentage: {e}")
    
    def sync_positions_on_startup(self):
        """
        Sync positions on startup to ensure we're aligned with the target.
        This handles the case where the bot restarts and needs to sync up with existing positions.
        """
        print("\n" + "="*80)
        print("🔄 SYNCING POSITIONS ON STARTUP")
        print("="*80)
        
        # Get target's current positions
        target_positions = self.get_current_positions()
        
        # Get my current positions
        my_positions = self.get_my_positions()
        
        if not target_positions:
            print("   Target has no open positions.")
            # Close any positions we have if target has none
            if my_positions:
                print(f"   Closing {len(my_positions)} positions to match target...")
                for coin, size in my_positions.items():
                    try:
                        print(f"   Closing {coin} position: {size}")
                        self.exchange.market_close(coin)
                    except Exception as e:
                        logging.warning(f"Could not close {coin}: {e}")
            print("   ✅ Synced - no positions")
            return
        
        print(f"\n   Target has {len(target_positions)} positions:")
        print(f"   You have {len(my_positions)} positions:")
        print()
        
        # Check if we need to sync
        needs_sync = False
        
        # Check target's positions
        for coin, position in target_positions.items():
            target_size = float(position.get("szi", 0))
            expected_size = target_size * self.copy_percentage
            my_size = my_positions.get(coin, 0)
            
            target_direction = "long" if target_size > 0 else "short"
            my_direction = "long" if my_size > 0 else "short"
            
            size_diff = abs(expected_size - my_size)
            
            print(f"   {coin}:")
            print(f"      Target: {target_size:+.4f} ({target_direction})")
            print(f"      Expected: {expected_size:+.4f}")
            print(f"      Your current: {my_size:+.4f} ({my_direction})")
            
            # If direction is wrong or size is off by more than 5%, we need to sync
            if abs(size_diff) > abs(expected_size * 0.05):
                print(f"      ⚠️  Needs sync (diff: {size_diff:+.4f})")
                needs_sync = True
            else:
                print(f"      ✅ In sync")
        
        # Check for positions you have that target doesn't
        for coin in my_positions:
            if coin not in target_positions:
                print(f"   {coin}: You have {my_positions[coin]} but target doesn't")
                print(f"      ⚠️  Needs to close")
                needs_sync = True
        
        print()
        
        if not needs_sync:
            print("   ✅ All positions already in sync!")
            print("   No sync needed.")
        else:
            print("   ⚠️  POSITIONS OUT OF SYNC")
            print("   This can happen if:")
            print("   • Bot was stopped/restarted")
            print("   • You manually traded")
            print("   • Network issues during trading")
            print()
            print("   The bot will continue monitoring - sync will happen gradually")
            print("   or you can manually adjust positions now.")
        
        print("="*80 + "\n")
        # Also log to file
        logging.info("="*80)
        logging.info("Position sync check completed")
        if needs_sync:
            logging.info("⚠️  Positions out of sync - bot will gradually adjust")
        else:
            logging.info("✅ All positions in sync")
        logging.info("="*80)
    
    def log_sync_status(self):
        """
        Log the current sync status between target and our positions.
        Called periodically during monitoring to track position alignment.
        """
        try:
            target_positions = self.get_current_positions()
            my_positions = self.get_my_positions()
            
            # If target has no positions, log that
            if not target_positions:
                if my_positions:
                    logging.info(f"📊 Sync Status: Target has 0 positions, you have {len(my_positions)} position(s) to close")
                else:
                    logging.debug("📊 Sync Status: Both target and you have 0 positions - fully synced")
                return
            
            sync_issues = []
            in_sync_count = 0
            
            # Check each target position
            for coin, position in target_positions.items():
                target_size = float(position.get("szi", 0))
                expected_size = target_size * self.copy_percentage
                my_size = my_positions.get(coin, 0)
                
                size_diff = abs(expected_size - my_size)
                size_diff_pct = (size_diff / abs(expected_size) * 100) if abs(expected_size) > 0.001 else 0
                
                # Consider synced if within 5% of expected
                if abs(size_diff) <= abs(expected_size * 0.05) or size_diff_pct < 5:
                    in_sync_count += 1
                else:
                    sync_issues.append({
                        "coin": coin,
                        "target": target_size,
                        "expected": expected_size,
                        "actual": my_size,
                        "diff": size_diff,
                        "diff_pct": size_diff_pct
                    })
            
            # Check for positions we have that target doesn't
            extra_positions = []
            for coin in my_positions:
                if coin not in target_positions:
                    extra_positions.append({"coin": coin, "size": my_positions[coin]})
            
            # Log summary
            total_target = len(target_positions)
            total_mine = len(my_positions)
            
            if len(sync_issues) == 0 and len(extra_positions) == 0 and total_target == total_mine:
                logging.info(f"✅ Sync Status: All {in_sync_count} position(s) in sync")
            else:
                logging.info(f"📊 Sync Status: {in_sync_count}/{total_target} in sync, {len(sync_issues)} need adjustment")
                
                # Log details of sync issues
                for issue in sync_issues:
                    logging.info(f"   ⚠️  {issue['coin']}: Expected {issue['expected']:+.4f}, have {issue['actual']:+.4f} "
                               f"(diff: {issue['diff']:+.4f}, {issue['diff_pct']:.1f}%)")
                
                # Log extra positions
                for extra in extra_positions:
                    logging.info(f"   📌 {extra['coin']}: You have {extra['size']:+.4f} but target doesn't")
                    
        except Exception as e:
            logging.warning(f"Error logging sync status: {e}")
    
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
        
        # If this is a SELL and you don't have a position, skip it unless opening/increasing a short
        if not is_buy:  # Selling
            my_positions = self.get_my_positions()
            my_position_size = my_positions.get(coin, 0)

            # Determine whether target action is opening/increasing a short
            opening_or_increasing_short = (current_size < 0 and prev_size <= 0 and abs(current_size) > abs(prev_size))

            if abs(my_position_size) < 0.001 and not opening_or_increasing_short:
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
            
            # Get current price
            current_price = 0
            try:
                coin_data = self.info.name_to_coin[coin]
                mids = self.info.all_mids()
                current_price = float(mids.get(coin_data, 0))
            except:
                pass
            
            print(f"\n📊 Position change detected for {coin}:")
            print(f"   Previous size: {prev_size}")
            print(f"   Current size:  {current_size}")
            print(f"   Change: {size_diff:+.6f}")
            print(f"   Copy size: {copy_size} ({self.copy_percentage * 100}% of change)")
            print(f"   Direction: {'BUY' if is_buy else 'SELL'}")
            print(f"   Price @ detection: ${current_price:,.2f}")
            
            # Calculate trade value
            if current_price > 0:
                trade_value = copy_size * current_price
                print(f"   Estimated value: ${trade_value:,.2f}")
            
            # Configure isolated margin if enabled
            if self.use_isolated_margin:
                print(f"   Setting isolated margin mode for {coin}...")
                # Set leverage to isolated mode (is_cross=False means isolated)
                try:
                    leverage_result = self.exchange.update_leverage(self.max_leverage, coin, is_cross=False)
                    if leverage_result.get("status") == "ok":
                        print(f"   ✅ Leverage set to {self.max_leverage}x (isolated)")
                    else:
                        logging.warning(f"Could not set leverage for {coin}: {leverage_result}")
                except Exception as e:
                    logging.warning(f"Error setting leverage for {coin}: {e}")
                
                # Calculate and add isolated margin for the position
                if current_price > 0 and trade_value > 0:
                    # For isolated margin, we need to fund the position
                    # The margin needed = position value / leverage
                    required_margin = trade_value / self.max_leverage
                    # Add a 10% buffer for safety
                    margin_to_add = required_margin * 1.1
                    # Round to 6 decimal places (USD precision) to avoid rounding errors
                    # The API requires exact 6-decimal precision for USD amounts
                    margin_to_add = round(margin_to_add, 6)
                    
                    try:
                        margin_result = self.exchange.update_isolated_margin(margin_to_add, coin)
                        if margin_result.get("status") == "ok":
                            print(f"   ✅ Added ${margin_to_add:,.2f} isolated margin")
                        else:
                            logging.warning(f"Could not add isolated margin for {coin}: {margin_result}")
                    except Exception as e:
                        logging.warning(f"Error adding isolated margin for {coin}: {e}")
            
            # Place market order (automatic - no confirmation needed)
            result = self.exchange.market_open(
                coin, 
                is_buy=is_buy, 
                sz=copy_size,
                slippage=0.01  # 1% slippage
            )
            
            if result.get("status") == "ok":
                # Get executed price from result
                executed_price = current_price
                try:
                    if "response" in result and "data" in result["response"]:
                        # Try to get executed price from response
                        data = result["response"]["data"]
                        if "statuses" in data and len(data["statuses"]) > 0:
                            if "filled" in data["statuses"][0]:
                                filled_data = data["statuses"][0]["filled"]
                                if "totalSz" in filled_data and "avgPx" in filled_data:
                                    executed_price = float(filled_data["avgPx"])
                except:
                    pass
                
                print(f"   ✅ Order placed successfully!")
                print(f"   Price @ execution: ${executed_price:,.2f}")
                
                trade_value = copy_size * executed_price
                
                # Send success notifications
                if self.telegram:
                    self.telegram.notify_trade_executed(coin, "BUY" if is_buy else "SELL", copy_size, trade_value, executed_price)
                
                if self.enable_notifications:
                    send_notification(
                        title=f"✅ Trade Executed: {coin} {'BUY' if is_buy else 'SELL'}",
                        message=f"Size: {copy_size:.4f} @ ${executed_price:,.2f} | Value: ~${trade_value:,.2f}",
                        sound="Purr"
                    )
                
                # Adjust copy percentage after successful trade
                self.adjust_copy_percentage()
                
                # Log sync improvement after trade
                try:
                    my_positions_after = self.get_my_positions()
                    my_size_after = my_positions_after.get(coin, 0)
                    expected_size = current_size * self.copy_percentage
                    sync_diff = abs(expected_size - abs(my_size_after))
                    sync_diff_pct = (sync_diff / abs(expected_size) * 100) if abs(expected_size) > 0.001 else 0
                    logging.info(f"📊 Sync Update - {coin}: After trade, position is {sync_diff_pct:.1f}% off target "
                               f"(target: {expected_size:+.4f}, actual: {my_size_after:+.4f})")
                except Exception as e:
                    logging.debug(f"Could not log sync update: {e}")
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
                if self.match_existing_if_similar:
                    print("\n🤝 First check - will copy existing positions IF market conditions are similar")
                else:
                    print("\n⚠️  First check - recording current positions (won't copy existing positions)")
                    print("   Future changes will be copied...")
        
        # Compare with previous positions
        for coin, position in current_positions.items():
            current_size = float(position.get("szi", 0))
            prev_size = float(self.last_positions.get(coin, {}).get("szi", 0))
            
            # On first check, only copy if explicitly enabled or if similar conditions
            if is_first_check:
                if hasattr(self, 'copy_existing_positions') and self.copy_existing_positions:
                    logging.info(f"Copying existing position in {coin} (size: {current_size})")
                    prev_size_for_first = 0.0
                elif self.match_existing_if_similar and self._should_match_existing_position(coin, position):
                    logging.info(f"Matching existing position in {coin} due to similar conditions (size: {current_size})")
                    prev_size_for_first = 0.0
                else:
                    logging.info(f"Skipping existing position in {coin} (size: {current_size})")
                    continue
            
            # Check if position changed
            if is_first_check:
                # Use prev_size_for_first to open equivalent position from zero when applicable
                if abs(current_size - prev_size_for_first) > 0.01:
                    self.place_copy_order(coin, current_size, prev_size_for_first)
            else:
                # No delta, but consider late matching if conditions become similar and we hold no position
                if self.match_existing_if_similar:
                    try:
                        my_positions_now = self.get_my_positions()
                        my_sz_now = float(my_positions_now.get(coin, 0))
                    except Exception:
                        my_sz_now = 0.0

                    no_change = abs(current_size - prev_size) <= 0.01
                    if abs(my_sz_now) < 0.001 and abs(current_size) > 0.01 and no_change:
                        if self._should_match_existing_position(coin, position):
                            logging.info(f"Matching {coin} later due to similar conditions (size: {current_size})")
                            self.place_copy_order(coin, current_size, 0.0)
                            # After placing, skip delta handling for this coin in this cycle
                            continue

                if abs(current_size - prev_size) > 0.01:
                    self.place_copy_order(coin, current_size, prev_size)
        
        # Handle positions that were closed or reduced
        for coin in self.last_positions:
            prev_size = float(self.last_positions[coin].get("szi", 0))
            
            if coin not in current_positions:
                # Position was completely closed, close ours too
                try:
                    # Calculate how much of our position to close (proportional to target)
                    my_positions = self.get_my_positions()
                    my_position_size = my_positions.get(coin, 0)
                    
                    if abs(my_position_size) > 0.001:  # We have a position to close
                        print(f"\n📊 Target closed position for {coin}")
                        print(f"   Target had: {prev_size:+.4f}")
                        print(f"   Your position: {my_position_size:+.4f}")
                        print(f"   Closing entire position...")
                        
                        # Send notifications
                        if self.telegram:
                            self.telegram.notify_position_closed(coin)
                        
                        if self.enable_notifications:
                            send_notification(
                                title=f"🔔 Position Closed: {coin}",
                                message=f"Target closed {abs(prev_size):.4f}. Closing yours...",
                                sound="Glass"
                            )
                        
                        close_result = self.exchange.market_close(coin)
                        print(f"   ✅ Closed position in {coin}")
                        
                        # Adjust copy percentage after closing position
                        if close_result.get("status") == "ok":
                            self.adjust_copy_percentage()
                except Exception as e:
                    print(f"   ❌ Error closing position: {e}")
            else:
                # Position changed (not closed completely)
                current_size = float(current_positions[coin].get("szi", 0))
                
                # Calculate size change
                size_diff = current_size - prev_size
                
                if abs(size_diff) > 0.01:
                    # This will be handled by place_copy_order above
                    # But if it's a reduction, we need to close our proportional amount
                    if (size_diff < 0 and prev_size > 0) or (size_diff > 0 and prev_size < 0):
                        # Position is being reduced/closed partially
                        close_amount = abs(size_diff) * self.copy_percentage
                        my_positions = self.get_my_positions()
                        my_position_size = my_positions.get(coin, 0)
                        
                        # Only close if we have a position
                        if abs(my_position_size) > 0.001:
                            # Determine how much to close
                            direction = my_position_size < 0  # True if short, False if long
                            
                            # Round close amount appropriately
                            if coin in ["BTC", "ETH"]:
                                close_amount = round(close_amount, 4)
                            elif coin == "SOL":
                                close_amount = round(close_amount, 2)
                            else:
                                close_amount = round(close_amount, 2)
                            
                            if abs(close_amount) > 0.001:
                                print(f"\n📊 Target reduced position for {coin}")
                                print(f"   Target reduced by: {abs(size_diff):.4f}")
                                print(f"   Closing your position by: {close_amount:.4f}")
                                
                                # Close using market_close with specific size and opposite direction
                                # We need to close in the direction opposite to our position
                                is_buy = not (my_position_size > 0)  # If long, we buy to close, if short we need to...
                                
                                # Actually, let's use the exchange method properly
                                result = self.exchange.market_close(coin, sz=close_amount)
                                
                                if result.get("status") == "ok":
                                    print(f"   ✅ Reduced position by {close_amount:.4f}")
                                    # Adjust copy percentage after reducing position
                                    self.adjust_copy_percentage()
                                else:
                                    print(f"   ❌ Failed to reduce position: {result}")
        
        # Update last known positions
        self.last_positions = current_positions
        
        # Log sync status periodically (every 10 checks to avoid spam)
        if not hasattr(self, '_sync_check_counter'):
            self._sync_check_counter = 0
        self._sync_check_counter += 1
        if self._sync_check_counter >= 10:
            self.log_sync_status()
            self._sync_check_counter = 0
        
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
    
    def start_monitoring(self, interval: int = 5, sync_on_startup: bool = True):
        """
        Start monitoring the target wallet.
        
        Args:
            interval: Check interval in seconds (default: 5)
            sync_on_startup: Check and sync positions on startup (default: True)
        """
        # Sync positions on startup if enabled
        if sync_on_startup:
            self.sync_positions_on_startup()
        
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
            self._notify_shutdown("User stopped")
        except Exception as e:
            logging.critical(f"Fatal error: {e}")
            self._notify_shutdown(f"Error: {e}")
            raise
    
    def _notify_shutdown(self, reason: str):
        """Notify when bot stops."""
        try:
            if self.telegram:
                self.telegram.send_message(
                    f"🛑 <b>Copy Trading Bot Stopped</b>\n\nReason: <code>{reason}</code>\nTime: {time.strftime('%Y-%m-%d %H:%M:%S')}"
                )
            
            if self.enable_notifications:
                send_notification(
                    title="🛑 Bot Stopped",
                    message=reason,
                    sound="Basso"
                )
        except Exception as e:
            logging.warning(f"Could not send shutdown notification: {e}")


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
    # Lower values = faster response time but more API requests
    # Rate limit: 1,200 requests/minute per IP (about 20 requests/second)
    # Recommended: 5 seconds = ~12 requests/minute per target wallet
    # Minimum safe: 3 seconds = ~20 requests/minute per target wallet
    # You can run multiple targets if staying under rate limits
    CHECK_INTERVAL = 3  # Check every 5 seconds (safe for quick response)
    
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
    
    # Match existing positions if market conditions are similar (price/PnL near entry)
    MATCH_EXISTING_IF_SIMILAR = True
    # Consider similar if mid price within 0.5% of entry
    PRICE_DEVIATION_THRESHOLD = 0.005
    # Or if |PnL%| relative to notional is within 0.3%
    PNL_PERCENT_THRESHOLD = 0.003

    # Sync positions on startup - ensures bot aligns with target after restart
    # True  = Check if positions are aligned and report
    # False = Don't check positions on startup
    SYNC_ON_STARTUP = True
    
    # Use isolated margin instead of cross margin
    # True  = Use isolated margin (each position has dedicated margin)
    # False = Use cross margin (all positions share margin pool)
    USE_ISOLATED_MARGIN = True
    
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
        telegram_config=telegram_config,
        use_isolated_margin=USE_ISOLATED_MARGIN,
        match_existing_if_similar=MATCH_EXISTING_IF_SIMILAR,
        price_deviation_threshold=PRICE_DEVIATION_THRESHOLD,
        pnl_percent_threshold=PNL_PERCENT_THRESHOLD
    )
    
    # Set whether to copy existing positions
    trader.copy_existing_positions = COPY_EXISTING_POSITIONS
    
    # Start monitoring with sync enabled
    trader.start_monitoring(interval=CHECK_INTERVAL, sync_on_startup=SYNC_ON_STARTUP)


if __name__ == "__main__":
    main()

