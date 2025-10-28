# Copy Trading Guide

This guide explains how to use the copy trading system to automatically copy trades from a target wallet.

## ⚠️ Important Warnings

**Copy trading involves significant risk:**
- You can lose your entire account balance
- Target wallets may use high leverage (10x+)
- Slippage may affect trade execution
- You copy both wins AND losses
- Past performance does not guarantee future results

## Quick Start

### 1. Fund Your Wallet

First, fund your Hyperliquid wallet with the amount you want to trade with. For example:
- Small account: $100-$500
- Medium account: $500-$5,000  
- Large account: $5,000+

### 2. Track a Wallet (Read-Only)

Start by monitoring a wallet to see their activity without executing any trades:

```bash
poetry run python examples/track_wallet.py
```

This will show you:
- Account value and margin used
- All open positions
- Open orders
- Recent fills

### 3. Start Copy Trading

When you're ready to copy trades, run:

```bash
poetry run python examples/copy_trade.py
```

## How It Works

### Automatic Proportional Sizing

By default, the script automatically calculates the copy percentage based on account sizes:

```
Copy Percentage = Your Account Value / Target Account Value
```

**Example:**
- Target wallet: $21,466
- Your wallet: $100
- Copy percentage: $100 / $21,466 = 0.47%

This means you'll trade 0.47% of the target's position sizes, which is proportional to your account size.

### Manual Configuration

Edit `examples/copy_trade.py` to customize:

```python
# ===== CONFIGURATION =====
TARGET_WALLET = "0xc20ac4dc4188660cbf555448af52694ca62b0734"
AUTO_CALCULATE = True  # Auto-calculate or use manual percentage
COPY_PERCENTAGE = None  # Only used if AUTO_CALCULATE = False
CHECK_INTERVAL = 10  # Check every 10 seconds
# ==========================
```

### Interactive Confirmation

By default, the script asks for confirmation before each trade. You'll see:

```
📊 Position change detected for ETH:
   Previous size: 0.0
   Current size:  5.74
   Change: +5.740000
   Copy size: 0.0270 (0.47% of change)
   Direction: BUY
   Estimated value: $113.00

⚠️  Execute this trade? (y/n/q for quit):
```

Type:
- `y` or `yes` to execute
- `n` or `no` to skip
- `q` or `quit` to stop monitoring

## Monitoring

The script continuously monitors the target wallet and will:
1. Detect when new positions are opened
2. Detect when positions are modified
3. Detect when positions are closed
4. Copy these actions proportionally to your account

## Example Output

```
================================================================================
🚀 Setting up copy trading
================================================================================

Target wallet:  0xc20ac4dc4188660cbf555448af52694ca62b0734
Your wallet:   0xbA8e6FCAb793830f4Fac3cFb9c6F570d385Cd311

💰 Account Values:
   Target: $21,466.73
   Yours:  $100.00

📊 Automatically calculated copy percentage: 0.47%
   This means you'll trade ~$100.00 worth of positions

⚠️  IMPORTANT WARNINGS:
   1. Copy trading involves significant risk
   2. You can lose your entire $100.00
   3. Target is using ~10x leverage (very high risk)
   4. Price slippage may affect your execution
   5. You will be copying both wins AND losses

================================================================================

🔄 Starting continuous monitoring...
   Checking every 10 seconds
   Press Ctrl+C to stop
```

## Safety Features

### Minimum Size Checks

The script automatically skips trades that are too small:

```
⏭️  Skipping ETH: Copy size 0.000234 is below minimum 0.001
```

### Slippage Protection

All market orders use 1% slippage protection to prevent execution at unfavorable prices.

### Confirmation Prompts

Every trade requires manual confirmation (y/n) before execution.

## Troubleshooting

### "Command not found: python"

Use `python3` or `poetry run python`:

```bash
poetry run python examples/copy_trade.py
```

### "No accountValue"

Your wallet needs to have funds deposited. Visit [Hyperliquid](https://hyperliquid.xyz) to deposit.

### "Order failed"

Common reasons:
- Insufficient margin for the position
- Position size below minimum
- Network/API issues
- Market closed/illiquid

### Getting Better Results

1. **Monitor First**: Use `track_wallet.py` to understand the target's trading style
2. **Start Small**: Test with small amounts first
3. **Monitor Performance**: Keep track of your results vs target results
4. **Adjust Copy Percentage**: Lower it if trades are too large for your account
5. **Choose Your Targets Carefully**: Look for consistent traders with good risk management

## Advanced Features

### Custom Copy Percentage

To use a fixed copy percentage instead of auto-calculation:

```python
AUTO_CALCULATE = False
COPY_PERCENTAGE = 0.01  # Copy 1% of target positions
```

### Different Check Intervals

Check more frequently for faster execution:

```python
CHECK_INTERVAL = 5  # Check every 5 seconds (more frequent)
```

Or less frequently to save resources:

```python
CHECK_INTERVAL = 30  # Check every 30 seconds
```

### Track Multiple Wallets

You can modify the script to track multiple wallets by creating multiple `CopyTrader` instances.

## Configuration File

The script uses `examples/config.json` which should have:

```json
{
    "secret_key": "0x...",
    "account_address": "0x..."
}
```

## Legal and Risk Disclaimer

This software is provided as-is for educational purposes. Copy trading involves substantial risk of loss. You should:
- Only trade with funds you can afford to lose
- Understand that past performance does not guarantee future results
- Be aware that leverage trading can amplify losses
- Consider consulting with a financial advisor
- Check your local regulations regarding automated trading

The authors are not responsible for any financial losses incurred through the use of this software.

