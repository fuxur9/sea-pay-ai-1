# Coinbase AgentKit Integration - Quick Start Guide

## Overview

This guide provides a quick reference for implementing Coinbase AgentKit wallet management features in the SeaPay agent.

## Current State

- **Payment**: Uses `x402` protocol with `eth_account` for wallet operations
- **Wallet**: Single private key from environment variable
- **Network**: Base Sepolia testnet
- **Currency**: USDC

## Recommended Implementation Priority

### 🔴 High Priority (Implement First)

1. **Wallet Balance Checking** (`check_wallet_balance`)

   - Check USDC balance before payments
   - Prevent failed transactions
   - User transparency

2. **Wallet Information Display** (`get_wallet_info`)

   - Show wallet address and network
   - Display all balances
   - User verification

3. **Enhanced Payment with Balance Check**
   - Pre-flight balance verification
   - Insufficient funds warnings
   - Better error messages

### 🟡 Medium Priority (Implement Next)

4. **USDC Transfer** (`transfer_usdc`)

   - Send USDC to other addresses
   - Refund processing
   - Requires user approval

5. **Transaction History** (`get_transaction_history`)

   - View past payments
   - Audit trail
   - Debugging support

6. **Transaction Status** (`check_transaction_status`)
   - Verify transaction completion
   - Track payment status

### 🟢 Low Priority (Future Enhancements)

7. Multi-wallet support
8. Smart contract interactions
9. Payment scheduling
10. Recurring payments

## Quick Implementation Steps

### 1. Install Dependencies

```bash
cd backend
uv add coinbase-agentkit
```

### 2. Create Wallet Manager Module

Create `backend/app/wallet/agentkit_wallet.py`:

```python
from agentkit import AgentKit, CdpWalletProvider
import os

class AgentKitWalletManager:
    def __init__(self):
        # Initialize with CDP Wallet or fallback to private key
        pass

    async def get_balance(self, asset_id: str = "usdc"):
        # Get wallet balance
        pass

    async def transfer(self, recipient: str, amount: float, asset_id: str = "usdc"):
        # Transfer USDC
        pass

    def get_wallet_address(self) -> str:
        # Get wallet address
        pass
```

### 3. Add Tools to Agent

Add to `seapay_agent.py`:

```python
@function_tool
async def check_wallet_balance(
    ctx: RunContextWrapper[SeaPayContext],
    asset_id: str = "usdc"
) -> dict[str, Any]:
    """Check USDC balance in wallet."""
    # Implementation using wallet manager
    pass
```

### 4. Update Environment Variables

Add to `.env.example`:

```bash
# Coinbase CDP Wallet (Optional - for production)
CDP_API_KEY_NAME=your_key_name
CDP_API_KEY_SECRET=your_key_secret
CDP_WALLET_SECRET=your_wallet_secret
CDP_NETWORK_ID=base-sepolia

# Private Key (Fallback)
PRIVATE_KEY=your_private_key
```

## Key Features from AgentKit

### Wallet Management

- ✅ Create and manage wallets
- ✅ Check balances (USDC, ETH, etc.)
- ✅ Transfer assets
- ✅ Transaction history

### Supported Providers

- **CDP Wallet Provider** (Recommended): Coinbase-managed wallets
- **Viem/EthAccount**: Local private key wallets
- **Privy Server Wallet**: Multi-chain support

### Network Support

- Base Mainnet
- Base Sepolia (testnet)
- Other EVM-compatible chains

## Integration Points

### Current Payment Flow

```
User Request → Reserve Hotel → HTTP 402 → make_payment tool → x402 payment
```

### Enhanced Flow with AgentKit

```
User Request → Reserve Hotel → HTTP 402 →
  check_wallet_balance →
  make_payment (with balance check) →
  x402 payment →
  get_transaction_status
```

## Code Structure

```
backend/
├── app/
│   ├── agents/
│   │   └── seapay_agent.py          # Add wallet tools here
│   ├── wallet/                       # NEW: Wallet module
│   │   ├── __init__.py
│   │   └── agentkit_wallet.py       # Wallet manager
│   └── widgets/                      # NEW: Wallet widgets
│       └── wallet_info_widget.py    # Display wallet info
└── docs/
    ├── AGENTKIT_IMPLEMENTATION_PLAN.md  # Detailed plan
    └── AGENTKIT_QUICK_START.md         # This file
```

## Testing Checklist

- [ ] Wallet balance checking works
- [ ] Wallet info displays correctly
- [ ] Payment flow includes balance check
- [ ] Transfers execute successfully
- [ ] Transaction history retrieves correctly
- [ ] Error handling works properly
- [ ] Fallback to private key works

## Additional Interesting Features

### Payment Features

- **Price Oracle**: Get USDC/USD exchange rates
- **Gas Estimation**: Calculate transaction costs
- **Payment Scheduling**: Schedule future payments
- **Payment Splitting**: Split costs between users
- **Recurring Payments**: Subscription-style payments
- **Escrow**: Hold funds until conditions met
- **Refunds**: Process cancellation refunds

### Analytics & Management

- **Payment Analytics**: Spending insights
- **Multi-Currency**: Support multiple tokens
- **Wallet Backup**: Recovery procedures

## Resources

- [Coinbase AgentKit Python Docs](https://docs.cdp.coinbase.com/agent-kit)
- [AgentKit GitHub](https://github.com/coinbase/agentkit/tree/main/python)
- [CDP Wallet API](https://docs.cdp.coinbase.com/server-wallets/v1)

## Next Steps

1. Review the detailed implementation plan: `AGENTKIT_IMPLEMENTATION_PLAN.md`
2. Set up Coinbase Developer Portal account (if using CDP Wallet)
3. Install AgentKit package
4. Implement Phase 1 features (balance checking, wallet info)
5. Test thoroughly on Base Sepolia testnet
6. Gradually add Phase 2 and Phase 3 features
