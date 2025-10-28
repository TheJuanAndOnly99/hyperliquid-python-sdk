#!/usr/bin/env python3
"""
Test Copy Trading Logic (Dry Run)
Shows what trades WOULD be executed without actually trading
"""

import time
from typing import Dict

import example_utils
from hyperliquid.info import Info
from hyperliquid.utils import constants


def test_position_detection():
    """Test if we can detect position changes."""
    print("="*80)
    print("🧪 TESTING COPY TRADING LOGIC (DRY RUN)")
    print("="*80)
    print()
    
    # Setup
    target_wallet = "0xc20ac4dc4188660cbf555448af52694ca62b0734"
    address, info, exchange = example_utils.setup(base_url=constants.MAINNET_API_URL, skip_ws=True)
    
    my_state = info.user_state(address)
    my_value = float(my_state.get("marginSummary", {}).get("accountValue", "0"))
    target_state = info.user_state(target_wallet)
    target_value = float(target_state.get("marginSummary", {}).get("accountValue", "0"))
    
    copy_percentage = min(my_value / target_value, 1.0) if (my_value > 0 and target_value > 0) else 0.0047
    
    print(f"Target wallet: {target_wallet}")
    print(f"Your wallet:   {address}")
    print(f"Copy %:       {copy_percentage * 100:.2f}%")
    print()
    
    # Get current positions
    last_positions = {}
    
    def get_target_positions():
        user_state = info.user_state(target_wallet)
        positions = {}
        for pos in user_state.get("assetPositions", []):
            p = pos["position"]
            positions[p["coin"]] = p
        return positions
    
    def simulate_trade(coin: str, target_change: float, is_buy: bool):
        """Simulate what trade would be executed."""
        copy_size = abs(target_change) * copy_percentage
        
        # Get price
        try:
            coin_data = info.name_to_coin[coin]
            mids = info.all_mids()
            price = float(mids.get(coin_data, 0))
            trade_value = copy_size * price
        except:
            price = 0
            trade_value = 0
        
        print(f"\n{'='*80}")
        print(f"📊 SIMULATED TRADE DETECTED")
        print(f"{'='*80}")
        print(f"Coin:          {coin}")
        print(f"Target Change: {target_change:+.6f}")
        print(f"Direction:     {'BUY' if is_buy else 'SELL'}")
        print()
        print(f"Copy Size:     {copy_size:.6f}")
        print(f"Price:         ${price:,.2f}" if price > 0 else "Price:         Unknown")
        print(f"Trade Value:   ${trade_value:,.2f}" if trade_value > 0 else "")
        print()
        print("✅ This trade WOULD be executed")
        print("   (In real mode, you'd press 'y' to confirm)")
        print(f"{'='*80}\n")
    
    print("🔍 Starting detection test...")
    print("   Monitoring for position changes")
    print("   This will show what WOULD be copied")
    print("   Press Ctrl+C to stop")
    print()
    print("="*80)
    
    # First check
    last_positions = get_target_positions()
    print(f"\n⏰ Initial positions recorded:")
    for coin, pos in last_positions.items():
        size = float(pos.get("szi", 0))
        print(f"   {coin}: {size:+.6f}")
    
    check_count = 0
    try:
        while True:
            time.sleep(10)  # Check every 10 seconds
            check_count += 1
            
            print(f"\n{'─'*80}")
            print(f"Check #{check_count} at {time.strftime('%H:%M:%S')}")
            print(f"{'─'*80}")
            
            current_positions = get_target_positions()
            
            # Compare with last positions
            for coin, position in current_positions.items():
                current_size = float(position.get("szi", 0))
                prev_size = float(last_positions.get(coin, {}).get("szi", 0))
                
                if abs(current_size - prev_size) > 0.01:  # Significant change
                    is_buy = (current_size - prev_size) > 0
                    simulate_trade(coin, current_size - prev_size, is_buy)
            
            # Check for closed positions
            for coin in last_positions:
                if coin not in current_positions:
                    print(f"\n🔔 Position closed: {coin}")
                    print("   In real mode, you'd close your position too")
            
            last_positions = current_positions
            print(f"   No changes detected... (waiting for target to trade)")
            
    except KeyboardInterrupt:
        print("\n\n✅ Test completed successfully!")
        print(f"   Did {check_count} checks")
        print("   Bot is ready to copy trades!")


if __name__ == "__main__":
    test_position_detection()

