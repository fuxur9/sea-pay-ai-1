# Coinbase AgentKit Integration - Quick Start Guide

## Overview

This guide provides a quick reference for implementing Coinbase AgentKit wallet management features in the SeaPay agent.

## Current State

- **Architecture**: Supervisor `seapay_agent` orchestrates specialized agents (`check_availability_agent`, `reserve_agent`, `payment_agent`) via handoffs
- **Payment**: Uses `x402` protocol with `eth_account.Account` for wallet operations
- **Wallet**: Single private key (raw EOA) from environment variable - no explicit wallet management from agent's perspective
- **Network**: Base Sepolia testnet
- **Currency**: USDC (amounts in micro-USDC, divided by 10^6)
- **Approval Pattern**: `tool_approval_widget` + `custom_mcp_approval_function` for MCP tools (pattern to reuse for wallet actions)

## Recommended Implementation Priority

### 🔴 High Priority (Implement First)

1. **Wallet Balance Checking** (`check_wallet_balance`)

   - Check USDC balance before payments
   - Prevent failed transactions
   - User transparency

2. **Wallet Information Display** (`get_wallet_info`)

   - Show wallet address and network
   - Display all balances (USDC, ETH/gas token)
   - Show gasless USDC status
   - User verification

3. **Enhanced Payment with Balance Check**
   - Pre-flight balance verification
   - Insufficient funds warnings
   - Better error messages

### 🟡 Medium Priority (Implement Next)

4. **USDC Payment** (`pay_invoice_with_usdc`)

   - Core payment tool for USDC transfers
   - Inputs: amount_usdc, destination_address, memo, network
   - Converts micro-USDC (from 402) to USDC (÷ 1,000,000)
   - Requires user approval via approval widget
   - Use cases: Hotel payments, refunds

5. **Wallet Activity** (`get_wallet_activity`)

   - View past payments (USDC transfers with amount, counterparty, hash, timestamp, status)
   - Audit trail
   - Debugging support
   - Agent can explain its actions

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
uv add cdp-sdk
# Optional: If using LangChain integration
uv add coinbase-agentkit-langchain
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

### 4. Create Configuration Module

Create `backend/app/wallet_config.py`:

```python
from coinbase_agentkit import AgentKit, CdpWalletProvider
import os

_wallet_provider = None
_agentkit = None

def get_agentkit():
    global _agentkit
    if _agentkit is None:
        wallet_provider = CdpWalletProvider.configure_with_wallet(
            api_key_id=os.getenv("CDP_API_KEY_ID"),
            private_key=os.getenv("CDP_API_KEY_PRIVATE_KEY"),
            wallet_id=os.getenv("CDP_WALLET_ID"),
            network_id=os.getenv("CDP_NETWORK_ID", "base-sepolia"),
        )
        _agentkit = AgentKit.from_config({
            "wallet_provider": wallet_provider,
            "action_providers": [],
        })
    return _agentkit
```

### 5. Update Environment Variables

Add to `.env.example`:

```bash
# Coinbase CDP Configuration
CDP_API_KEY_NAME=your_cdp_api_key_name
CDP_API_KEY_PRIVATE_KEY=your_cdp_api_private_key

# Wallet Configuration (choose one)
# Option 1: Persistent wallet (recommended for production)
CDP_WALLET_DATA={"wallet_id": "...", "seed": "..."}  # JSON string
# OR
CDP_WALLET_ID=your_cdp_wallet_id
CDP_WALLET_SECRET=your_cdp_wallet_secret

# Option 2: Let agent create new wallet on first run (development)
# Leave wallet config empty to auto-create

# Network Configuration
NETWORK_ID=base-sepolia  # or base-mainnet, ethereum-mainnet, etc.
CDP_NETWORK_ID=base-sepolia  # Alias

# Legacy (for backward compatibility with x402)
PRIVATE_KEY=your_ethereum_private_key  # Keep during migration
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

**Option A (Dual-mode during migration)**:

```
User Request → Reserve Hotel → HTTP 402 (with amount, currency, network, pay_to) →
  get_wallet_info (verify balance) →
  pay_invoice_with_usdc (with approval) →
  make_payment (confirm reservation, no x402) →
  get_transaction_status
```

**Option B (Full AgentKit)**:

```
User Request → Reserve Hotel → HTTP 402 →
  get_wallet_info (verify balance) →
  pay_invoice_with_usdc (with approval) →
  confirm_reservation_after_onchain_payment →
  get_transaction_status
```

**Key Changes**:

- 402 payload must include `pay_to` (merchant address)
- Agent explicitly checks balance before payment
- Payment uses AgentKit USDC transfer (not x402)
- Approval widget required for wallet spend actions

## Code Structure

```
backend/
├── app/
│   ├── agents/
│   │   ├── seapay_agent.py          # Supervisor + specialized agents
│   │   └── wallet_tools.py          # NEW: Wallet management tools
│   ├── wallet/                       # NEW: Wallet module
│   │   ├── __init__.py
│   │   ├── agentkit_wallet.py       # Wallet manager
│   │   └── wallet_config.py         # Configuration & singleton
│   └── widgets/                      # Existing widgets
│       ├── hotel_card_widget.py
│       ├── tool_approval_widget.py  # Reuse for wallet approvals
│       └── wallet_status_widget.py  # NEW: Wallet status display
└── docs/
    ├── AGENTKIT_IMPLEMENTATION_PLAN.md  # Detailed plan
    └── AGENTKIT_QUICK_START.md         # This file
```

## Key Implementation Details

### Wallet Tools to Create

1. **`get_wallet_info`**: Address, network, USDC balance, ETH balance, gasless status
2. **`get_wallet_activity`**: Recent transactions (amount, counterparty, hash, timestamp, status)
3. **`pay_invoice_with_usdc`**: Core payment tool with approval flow
4. **`ensure_wallet_funded`** (dev-only): Faucet funding for testnet
5. **`show_wallet_status`**: Widget-based wallet display

### Approval Flow Integration

- Reuse existing `custom_mcp_approval_function` pattern
- Use `build_approval_widget()` for wallet spend actions
- Handle `request.approve` / `request.reject` in `server.py` action handler
- Use `approval_event` and `approval_result` global variables

### Payment Flow Updates

1. **402 Payload Contract**: Ensure `reserve` returns `pay_to` (merchant address)
2. **Update RESERVE_PAYMENT_INSTRUCTIONS**:
   - First call `get_wallet_info`
   - Then call `pay_invoice_with_usdc` with converted amount (÷ 1,000,000)
   - After payment, confirm reservation (Option A or B)
3. **Amount Conversion**: 402 provides micro-USDC, divide by 1,000,000 for USDC

## Testing Checklist

### Unit Tests

- [ ] Wallet manager initialization (CDP and fallback)
- [ ] Balance checking with mocked AgentKit
- [ ] Amount conversion (micro-USDC to USDC)
- [ ] Network validation
- [ ] Error handling (insufficient balance, network mismatch)

### Integration Tests (Base Sepolia)

- [ ] Fund wallet with USDC via faucet
- [ ] End-to-end booking flow: `get_wallet_info` → `pay_invoice_with_usdc` → confirmation
- [ ] Verify on-chain transfer on Base Sepolia explorer
- [ ] Transaction history retrieval
- [ ] Approval flow for wallet actions

### Manual Testing

- [ ] Wallet balance checking works
- [ ] Wallet info displays correctly (address, balances, network)
- [ ] Payment flow includes balance check
- [ ] Approval widget appears for `pay_invoice_with_usdc`
- [ ] Transfers execute successfully with gasless USDC
- [ ] Transaction history retrieves correctly
- [ ] Error handling works properly (insufficient funds, invalid address)
- [ ] Fallback to private key works
- [ ] Guardrails work (spend limits, network whitelist)

## Additional Interesting Features

### Payment Features

- **Price Oracle**: Get USDC/USD exchange rates (Chainlink integration)
- **Gas Estimation**: Calculate transaction costs
- **Payment Scheduling**: Schedule future payments
- **Payment Splitting**: Split costs between users (multi-sig)
- **Recurring Payments**: Subscription-style payments (ERC-20 subscription token)
- **Escrow**: Smart contract escrow for bookings
- **Refunds**: Process cancellation refunds

### Advanced Features

- **NFT Booking Receipts**: Immutable proof of booking, transferable gifts
- **Loyalty Token System**: Earn and redeem tokens (SeaPayRewards)
- **DeFi Integration**: Stake USDC for yield while waiting for check-in
- **Multi-Wallet Support**: Connect external wallets (Privy, MetaMask, Coinbase Wallet)
- **Token Swaps**: Automatic ETH → USDC conversion for payments

### Social & Compliance

- **Social Features**: Share booking NFTs, gift hotel stays
- **Insurance Integration**: Travel insurance via DeFi protocols
- **Carbon Offset NFTs**: Eco-friendly booking proofs
- **Referral Program**: Smart contract-based referral tracking

### Analytics & Management

- **Payment Analytics**: Spending insights and budget tracking
- **Multi-Currency**: Support multiple tokens with automatic conversion
- **Wallet Backup**: Secure seed phrase export
- **Price Optimization**: Agent suggests optimal payment timing
- **Budget Manager**: Track spending and suggest alternatives

## Resources

- [Coinbase AgentKit Python Docs](https://docs.cdp.coinbase.com/agent-kit)
- [AgentKit GitHub](https://github.com/coinbase/agentkit/tree/main/python)
- [CDP Wallet API](https://docs.cdp.coinbase.com/server-wallets/v1)

## Guardrails & Security

- **Spend Limits**: Hard-code per-transaction limits (e.g., < 100 USDC)
- **Network Whitelist**: Only allow base-sepolia (dev) or base-mainnet (prod)
- **Address Whitelist**: Only allow known merchant addresses (SeaPay, test merchants)
- **Approval Required**: All wallet spend actions require explicit user approval
- **Balance Checks**: Always verify balance before payments

## Next Steps

1. Review the detailed implementation plan: `AGENTKIT_IMPLEMENTATION_PLAN.md`
2. Set up Coinbase Developer Portal account (if using CDP Wallet)
3. Install AgentKit package: `uv add coinbase-agentkit`
4. Create `wallet_config.py` with singleton pattern
5. Create `wallet_tools.py` with core tools (`get_wallet_info`, `pay_invoice_with_usdc`)
6. Update `payment_agent` instructions to use new tools
7. Integrate approval flow for wallet actions
8. Test thoroughly on Base Sepolia testnet
9. Update SeaPay backend to include `pay_to` in 402 responses
10. Gradually add Phase 2 and Phase 3 features
