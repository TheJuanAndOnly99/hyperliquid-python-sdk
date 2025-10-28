"""
Wallet Tracking Script for Hyperliquid

This script monitors a target wallet and displays their trading activity,
positions, and performance metrics.

Note: This is read-only and does not execute any trades.
"""

import json
import time
from datetime import datetime

from hyperliquid.utils import constants

from hyperliquid.info import Info


def format_number(value: str, decimals: int = 2) -> str:
    """Format a number string with decimal places."""
    try:
        num = float(value)
        if abs(num) < 0.01:
            return f"{num:.{decimals}f}"
        return f"{num:,.{decimals}f}"
    except:
        return value


def print_separator():
    """Print a separator line."""
    print("=" * 80)


def display_user_state(info: Info, target_wallet: str):
    """Display the current state of the target wallet."""
    try:
        user_state = info.user_state(target_wallet)
        positions = []
        
        for pos in user_state["assetPositions"]:
            positions.append(pos["position"])
        
        margin_summary = user_state.get("marginSummary", {})
        account_value = margin_summary.get("accountValue", "0")
        margin_used = margin_summary.get("totalMarginUsed", "0")
        
        print(f"\n💰 Account Value: ${format_number(account_value)}")
        print(f"📊 Margin Used:  ${format_number(margin_summary.get('totalMarginUsed', '0'))}")
        
        if positions:
            print(f"\n📈 Open Positions ({len(positions)}):\n")
            for i, pos in enumerate(positions, 1):
                coin = pos.get("coin", "N/A")
                szi = format_number(pos.get("szi", "0"), 4)
                entry_px = pos.get("entryPx", "N/A")
                current_px = format_number(pos.get("entryPx", "0"))  # This would ideally be mark price
                unrealized_pnl = format_number(pos.get("unrealizedPnl", "0"))
                roe = pos.get("returnOnEquity", "0.00")
                
                direction = "LONG" if float(pos.get("szi", 0)) > 0 else "SHORT"
                
                print(f"  {i}. {coin:8s} {direction:5s} | Size: {szi:>10s} | Entry: ${entry_px:>10s} | PnL: ${unrealized_pnl:>12s} | ROE: {roe:>6s}%")
                
                # Additional details
                lev = pos.get("leverage", {})
                margin_used = format_number(pos.get("marginUsed", "0"))
                pos_value = format_number(pos.get("positionValue", "0"))
                
                print(f"      Margin: ${margin_used:>8s} | Pos Value: ${pos_value:>10s} | Leverage: {lev.get('value', 'N/A')}x")
        else:
            print("\n📭 No open positions")
        
        # Withdrawable
        withdrawable = format_number(user_state.get("withdrawable", "0"))
        print(f"\n💵 Withdrawable: ${withdrawable}")
        
    except Exception as e:
        print(f"❌ Error fetching user state: {e}")
        return False
    
    return True


def display_open_orders(info: Info, target_wallet: str):
    """Display open orders for the target wallet."""
    try:
        orders = info.open_orders(target_wallet)
        
        if orders:
            print(f"\n📋 Open Orders ({len(orders)}):\n")
            for i, order in enumerate(orders, 1):
                coin = order.get("coin", "N/A")
                side = order.get("side", "N/A")
                side_str = "BUY" if side == "B" else "SELL"
                size = format_number(order.get("sz", "0"), 4)
                limit_px = format_number(order.get("limitPx", "0"))
                timestamp = order.get("timestamp", 0)
                
                time_str = datetime.fromtimestamp(timestamp / 1000).strftime("%H:%M:%S")
                
                print(f"  {i}. {coin:8s} {side_str:5s} | Size: {size:>10s} | Price: ${limit_px:>10s} | Time: {time_str}")
        else:
            print("\n📭 No open orders")
            
    except Exception as e:
        print(f"❌ Error fetching orders: {e}")


def display_recent_fills(info: Info, target_wallet: str, limit: int = 5):
    """Display recent fills for the target wallet."""
    try:
        fills = info.user_fills(target_wallet)
        
        if fills:
            recent_fills = sorted(fills, key=lambda x: x.get("time", 0), reverse=True)[:limit]
            print(f"\n🔄 Recent Fills (last {len(recent_fills)} of {len(fills)}):\n")
            
            for i, fill in enumerate(recent_fills, 1):
                coin = fill.get("coin", "N/A")
                side = fill.get("side", "N/A")
                side_str = "BUY" if side == "B" else "SELL"
                size = format_number(fill.get("sz", "0"), 4)
                price = format_number(fill.get("px", "0"))
                closed_pnl = format_number(fill.get("closedPnl", "0"))
                timestamp = fill.get("time", 0)
                
                time_str = datetime.fromtimestamp(timestamp / 1000).strftime("%Y-%m-%d %H:%M:%S")
                
                print(f"  {i}. {coin:8s} {side_str:5s} | Size: {size:>10s} | Price: ${price:>10s} | PnL: ${closed_pnl:>12s}")
                print(f"      {time_str}")
        else:
            print("\n📭 No fills found")
            
    except Exception as e:
        print(f"❌ Error fetching fills: {e}")


def main():
    # ===== CONFIGURATION =====
    # Target wallet to track
    TARGET_WALLET = "0xc20ac4dc4188660cbf555448af52694ca62b0734"
    
    # Update interval in seconds (use 0 for single check)
    UPDATE_INTERVAL = 0  # Set to 10 or more for continuous monitoring
    
    # ==========================
    
    # Initialize
    info = Info(base_url=constants.MAINNET_API_URL, skip_ws=True)
    
    if UPDATE_INTERVAL == 0:
        # Single check
        print_separator()
        print(f"📊 Tracking Wallet: {TARGET_WALLET}")
        print_separator()
        
        display_user_state(info, TARGET_WALLET)
        display_open_orders(info, TARGET_WALLET)
        display_recent_fills(info, TARGET_WALLET)
        
        print_separator()
    else:
        # Continuous monitoring
        print("🔄 Starting continuous monitoring...")
        print(f"   Checking every {UPDATE_INTERVAL} seconds")
        print("   Press Ctrl+C to stop\n")
        
        try:
            check_number = 0
            while True:
                check_number += 1
                print_separator()
                print(f"🕐 Check #{check_number} | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print_separator()
                
                display_user_state(info, TARGET_WALLET)
                display_open_orders(info, TARGET_WALLET)
                display_recent_fills(info, TARGET_WALLET)
                
                print(f"\n⏱️  Next update in {UPDATE_INTERVAL} seconds...")
                print_separator()
                time.sleep(UPDATE_INTERVAL)
                
        except KeyboardInterrupt:
            print("\n\n🛑 Monitoring stopped by user")
            print_separator()


if __name__ == "__main__":
    main()

