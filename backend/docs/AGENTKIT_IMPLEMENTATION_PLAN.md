# Coinbase AgentKit Integration Plan for SeaPay Agent

## Executive Summary

This document outlines a comprehensive plan to integrate Coinbase AgentKit into the SeaPay hotel booking agent, enabling advanced wallet management capabilities and USDC payment functionality. The integration will enhance the agent's ability to manage wallets, check balances, transfer funds, and interact with blockchain networks.

## Current State Analysis

### SeaPay Architecture

The SeaPay agent (`seapay_agent.py`) defines:

- **SeaPayContext**: ChatKit context with `MemoryStore` + `RequestContext`
- **Specialized Agents**:
  - `check_availability_agent`: Calls MCP `check_availability` + `show_hotel_cards`
  - `reserve_agent`: Calls MCP `reserve` tool
  - `payment_agent`: Calls `make_payment` tool
- **Supervisor Agent**: `seapay_agent` orchestrates the booking flow via handoffs
- **Server Integration**: `server.py` / `main.py` wrap this in a `SeaPayServer` + FastAPI endpoint `/chatkit`

### Existing Payment Implementation

- **Payment Method**: Uses `x402` protocol with `eth_account.Account` for wallet management
- **Wallet Storage**: Private key stored in environment variable (`PRIVATE_KEY`) - raw EOA (Externally Owned Account)
- **Payment Flow**:
  - MCP `reserve` → HTTP 402 with amount/currency/network → `make_payment` tool
  - `make_payment` uses `x402HttpxClient` against `SEAPAY_API_BASE_URL /api/reserve`
  - x402 handles HTTP 402 "Payment Required" and does on-chain ETH/USDC payment under the hood
- **Network**: Base Sepolia testnet
- **Currency**: USDC (amounts in micro-USDC, divided by 10^6 for display)
- **No Explicit Wallet Management**: There is no explicit notion of a managed wallet from the agent's perspective—just a server-side private key

### UX Pattern for Risk Actions

- **Tool Approval System**: `tool_approval_widget` and `custom_mcp_approval_function` show a widget and require explicit approve/reject for MCP tools
- **Approval Flow**: Uses `approval_event` and `approval_result` global variables, handled in `server.py` action handler
- **Pattern to Reuse**: This approval pattern is ideal to reuse for on-chain / wallet actions

### Current Limitations

1. **No wallet management UI**: Users cannot check balance, view transaction history, or manage wallet settings
2. **Single wallet per instance**: Only one wallet can be configured via environment variable
3. **No balance checking**: Agent cannot verify if wallet has sufficient funds before payment
4. **No transaction history**: No way to track past payments or transactions
5. **No multi-wallet support**: Cannot manage multiple wallets or switch between them
6. **Limited error handling**: Basic error handling for wallet configuration issues
7. **Agent unaware of wallet**: Agent has no explicit knowledge of its wallet state

## Coinbase AgentKit Features to Implement

### Phase 1: Core Wallet Management (Priority: High)

#### 1.1 Replace eth-account with Coinbase AgentKit CDP SDK

**Current Implementation**:

```python
from eth_account import Account
wallet_account = Account.from_key(private_key)
```

**New Implementation with AgentKit**:

- Install CDP SDK: `pip install coinbase-agentkit`
- Initialize wallet using CDP Wallet API
- Support both persistent wallets (from seed) and new wallet creation
- Store wallet data securely

**Benefits**:

- Multi-chain support (Base, Base Sepolia, other EVM chains, Solana)
- Built-in USDC support with gasless transfers on Base
- 4.1% APY rewards on USDC balances (via Coinbase)
- Better security and key management
- No need to manage raw private keys

#### 1.2 Wallet Balance Checking

**Tool**: `check_wallet_balance`

- **Purpose**: Check USDC balance in the agent's wallet before making payments
- **Implementation**:
  ```python
  @function_tool
  async def check_wallet_balance(
      ctx: RunContextWrapper[SeaPayContext],
      asset_id: str = "usdc"
  ) -> dict[str, Any]:
      """
      Check the current balance of USDC (or other assets) in the wallet.
      Returns balance in human-readable format.
      """
  ```
- **Benefits**:
  - Prevent failed payments due to insufficient funds
  - Provide transparency to users about available funds
  - Enable proactive balance warnings

#### 1.3 Wallet Management Tools

**Tool**: `create_wallet`

- **Purpose**: Create a new CDP wallet for the agent
- **Implementation**:
  ```python
  @function_tool
  async def create_wallet(
      ctx: RunContextWrapper[SeaPayContext]
  ) -> dict[str, Any]:
      """
      Create a new CDP wallet for the agent.
      Returns wallet address and seed phrase for backup.
      """
  ```

**Tool**: `get_wallet_info`

- **Purpose**: Display wallet address, network, and current balances
- **Returns**:
  - Address (wallet address)
  - Network (base-sepolia or base-mainnet)
  - Balances: USDC, native gas token (ETH on Base)
  - Whether gasless USDC is enabled
- **Implementation**:
  ```python
  @function_tool
  async def get_wallet_info(
      ctx: RunContextWrapper[SeaPayContext]
  ) -> dict[str, Any]:
      """
      Get comprehensive wallet information including address, network, and balances.
      Use this to check the wallet address and USDC/gas balances before making on-chain payments.
      """
  ```

**Tool**: `get_wallet_address`

- **Purpose**: Get the current wallet address
- **Implementation**:
  ```python
  @function_tool
  async def get_wallet_address(
      ctx: RunContextWrapper[SeaPayContext]
  ) -> dict[str, Any]:
      """Get the current wallet address."""
  ```

**Tool**: `export_wallet`

- **Purpose**: Export wallet data (seed phrase) for backup
- **Security**: Requires explicit user approval
- **Implementation**:

  ```python
  @function_tool
  async def export_wallet(
      ctx: RunContextWrapper[SeaPayContext]
  ) -> dict[str, Any]:
      """
      Export wallet data (seed phrase) for backup.
      WARNING: This reveals sensitive information. Requires user approval.
      """
  ```

- **Benefits**:
  - User can verify wallet address
  - See all asset balances at once
  - Understand which network the wallet is on
  - Agent can reason about wallet state before payments
  - Secure wallet backup and recovery

#### 1.4 Update Payment Flow to Use USDC

**Modify `make_payment` tool**:

- Change from generic x402 to CDP SDK USDC transfers
- Implement gasless USDC transfers on Base Sepolia (testnet) and Base Mainnet
- Add balance checks before payments
- Provide better error handling for insufficient funds
- Pre-payment balance check
- Insufficient funds warning
- Transaction status tracking
- Better error messages with balance information

### Phase 2: Enhanced Payment Features (Priority: Medium)

#### 2.1 Multi-Currency Support

**Tool**: `swap_tokens`

- **Purpose**: Swap between tokens (e.g., ETH -> USDC) for payments
- **Implementation**:
  ```python
  @function_tool
  async def swap_tokens(
      ctx: RunContextWrapper[SeaPayContext],
      from_asset: str,
      to_asset: str,
      amount: float
  ) -> dict[str, Any]:
      """
      Swap between tokens (e.g., ETH -> USDC) for payments.
      Uses AgentKit action providers for DEX integration.
      """
  ```
- **Use Case**: User has ETH but hotel requires USDC → automatically swap before payment

#### 2.2 Request Testnet Funds

**Tool**: `request_faucet_funds`

- **Purpose**: Request testnet ETH from Base Sepolia faucet (once per 24 hours)
- **Implementation**:
  ```python
  @function_tool
  async def request_faucet_funds(
      ctx: RunContextWrapper[SeaPayContext]
  ) -> dict[str, Any]:
      """
      Request testnet ETH from Base Sepolia faucet (once per 24 hours).
      Use Case: Demo/testing environment - users can get testnet funds easily.
      """
  ```

#### 2.3 Ensure Wallet Funded (Optional, Dev-Only)

**Tool**: `ensure_wallet_funded`

- **Purpose**: On base-sepolia, uses a faucet or demo funding to ensure wallet has:
  - At least some USDC
  - Enough gas (or ensures gasless USDC is configured)
- **Implementation**: Uses AgentKit/CDP faucet support if available
- **Tool Description**: "Use this before booking if you suspect the wallet has no USDC/gas."

### Phase 2: Enhanced Payment Features (Priority: Medium)

#### 2.4 USDC Payment / Transfer Capability

**Tool**: `pay_invoice_with_usdc` (core payment tool)

- **Purpose**: Core payment tool for USDC payments to merchant addresses
- **Inputs** (aligned with 402 payload semantics):
  - `amount_usdc`: float | str – final user-facing USDC amount (after dividing micro-USDC by 1,000,000)
  - `destination_address`: str – merchant / SeaPay settlement wallet
  - `memo`: str | None – reservation ID or description
  - `network`: str – default base-sepolia (validate against configured network)
- **Implementation**:
  ```python
  @function_tool
  async def pay_invoice_with_usdc(
      ctx: RunContextWrapper[SeaPayContext],
      amount_usdc: float,
      destination_address: str,
      memo: str | None = None,
      network: str = "base-sepolia"
  ) -> dict[str, Any]:
      """
      Pay an invoice using USDC transfer.
      Converts human USDC amount to correct decimal integer using AgentKit.
      Uses AgentKit wallet transfer API with gasless=True for Base network.
      Waits for confirmation, then returns tx_hash, amount, currency, network, status.
      """
  ```
- **Approval Flow**:
  - Before executing, calls `build_approval_widget(...)` and waits for approve/reject
  - Reuses existing `custom_mcp_approval_function` pattern or routes through generalized `on_approval_request`
  - Agent should phrase: "I want to pay X USDC to Y for hotel reservation Z. Do you approve?"
- **Use Cases**:
  - Hotel reservation payments
  - Refund processing
  - Sending payments to hotel partners
- **Security**: Requires explicit user approval before execution via approval widget

#### 2.5 Transaction History / Wallet Activity

**Tool**: `get_wallet_activity` (or `get_transaction_history`)

- **Purpose**: Retrieve and display recent transactions
- **Returns**: Summarized list of recent transactions:
  - USDC transfers (amount, counterparty, hash, timestamp, status)
  - Useful for debugging and for the agent to explain what it did
- **Implementation**:
  ```python
  @function_tool
  async def get_wallet_activity(
      ctx: RunContextWrapper[SeaPayContext],
      limit: int = 10
  ) -> dict[str, Any]:
      """
      Get recent transaction history for the wallet.
      Returns USDC transfers with amount, counterparty, transaction hash, timestamp, and status.
      """
  ```
- **Benefits**:
  - Users can review past payments
  - Audit trail for reservations
  - Debugging payment issues
  - Agent can explain its actions

#### 2.6 Transaction Status Check

**Tool**: `check_transaction_status`

- **Purpose**: Check the status of a specific transaction
- **Implementation**:
  ```python
  @function_tool
  async def check_transaction_status(
      ctx: RunContextWrapper[SeaPayContext],
      transaction_hash: str
  ) -> dict[str, Any]:
      """
      Check the status of a specific transaction by hash.
      """
  ```

### Phase 3: Advanced Features (Lower Priority, High Value)

#### 3.1 NFT-Based Booking Receipts

**Tool**: `mint_booking_receipt_nft`

- **Purpose**: Mint an NFT as a booking receipt/proof of reservation
- **Implementation**:
  ```python
  @function_tool
  async def mint_booking_receipt_nft(
      ctx: RunContextWrapper[SeaPayContext],
      reservation_id: str,
      hotel_name: str,
      booking_details: dict
  ) -> dict[str, Any]:
      """
      Mint an NFT as a booking receipt/proof of reservation.
      Add metadata: hotel images, dates, confirmation details.
      """
  ```
- **Benefits**:
  - Immutable proof of booking
  - Can be used for loyalty programs
  - Transferable (e.g., gift a hotel stay)

#### 3.2 Loyalty Token System

**Tool**: `deploy_loyalty_token`

- **Purpose**: Deploy ERC-20 loyalty token for rewards
- **Implementation**:
  ```python
  @function_tool
  async def deploy_loyalty_token(
      ctx: RunContextWrapper[SeaPayContext],
      name: str = "SeaPayRewards",
      symbol: str = "SPR"
  ) -> dict[str, Any]:
      """Deploy ERC-20 loyalty token for rewards"""
  ```

**Tool**: `award_loyalty_tokens`

- **Purpose**: Award loyalty tokens to users (e.g., 5% of booking value)
- **Implementation**:
  ```python
  @function_tool
  async def award_loyalty_tokens(
      ctx: RunContextWrapper[SeaPayContext],
      user_address: str,
      amount: float,
      reason: str
  ) -> dict[str, Any]:
      """Award loyalty tokens to users (e.g., 5% of booking value)"""
  ```
- **Use Case**:
  - Earn tokens with each booking
  - Redeem tokens for discounts
  - Gamification of hotel bookings

#### 3.3 Smart Contract Escrow for Bookings

**Tool**: `create_booking_escrow`

- **Purpose**: Create smart contract escrow that releases payment after check-in
- **Implementation**:
  ```python
  @function_tool
  async def create_booking_escrow(
      ctx: RunContextWrapper[SeaPayContext],
      hotel_address: str,
      amount: float,
      check_in_timestamp: int,
      cancellation_policy: dict
  ) -> dict[str, Any]:
      """
      Create smart contract escrow that releases payment after check-in verification.
      """
  ```
- **Benefits**:
  - Trustless booking system
  - Automatic refunds for cancellations
  - Release payment only after check-in verification
  - Dispute resolution built-in

#### 3.4 DeFi Integration - Earn While You Wait

**Tool**: `stake_usdc_for_yield`

- **Purpose**: Stake USDC in Compound or other DeFi protocols to earn yield
- **Implementation**:
  ```python
  @function_tool
  async def stake_usdc_for_yield(
      ctx: RunContextWrapper[SeaPayContext],
      amount: float
  ) -> dict[str, Any]:
      """Stake USDC in Compound or other DeFi protocols to earn yield"""
  ```

**Tool**: `unstake_usdc`

- **Purpose**: Unstake USDC from DeFi protocols
- **Implementation**:
  ```python
  @function_tool
  async def unstake_usdc(
      ctx: RunContextWrapper[SeaPayContext],
      amount: float
  ) -> dict[str, Any]:
      """Unstake USDC from DeFi protocols"""
  ```
- **Use Case**:
  - Book hotel 30 days in advance
  - Stake payment amount in Compound
  - Earn interest until check-in date
  - Automatically unstake and pay hotel

#### 3.5 Multi-Wallet Support

**Tool**: `connect_external_wallet`

- **Purpose**: Connect external wallet instead of CDP wallet
- **Implementation**:
  ```python
  @function_tool
  async def connect_external_wallet(
      ctx: RunContextWrapper[SeaPayContext],
      wallet_provider: str,  # "privy", "metamask", etc.
      wallet_address: str
  ) -> dict[str, Any]:
      """Connect external wallet instead of CDP wallet"""
  ```
- **Benefits**:
  - Users can use their existing wallets
  - Support for Privy, MetaMask, Coinbase Wallet
  - Multi-chain support (Solana, EVM)

### Phase 4: Agent Intelligence Enhancements (Priority: Low)

#### 4.1 Price Optimization Agent

**Agent**: `price_optimizer_agent`

- **Purpose**: Monitor token prices and suggest optimal payment timing
- **Instructions**:
  - If USDC/ETH rate is favorable, recommend paying now
  - If user has only ETH, calculate best swap route
  - Monitor gas fees and suggest gasless USDC transfers

#### 4.2 Budget Manager Agent

**Agent**: `budget_manager_agent`

- **Purpose**: Track user's booking budget and wallet balance
- **Instructions**:
  - Warn if booking exceeds available funds
  - Suggest alternative hotels within budget
  - Provide spending analytics

#### 4.3 Gas Fee Optimizer

**Tool**: `estimate_gas_fees`

- **Purpose**: Estimate gas fees for different transaction types
- **Implementation**:
  ```python
  @function_tool
  async def estimate_gas_fees(
      ctx: RunContextWrapper[SeaPayContext],
      transaction_type: str
  ) -> dict[str, Any]:
      """Estimate gas fees for different transaction types"""
  ```
- **Use Case**: Inform users about transaction costs, suggest gasless USDC transfers on Base

### Phase 5: Multi-Wallet Support (Priority: Low)

#### 3.1 Wallet Switching

**Tool**: `switch_wallet`

- **Purpose**: Switch between multiple configured wallets
- **Implementation**: Store multiple wallet configurations and allow switching
- **Use Cases**:
  - Personal vs. business wallets
  - Different networks (testnet vs. mainnet)
  - Multiple user accounts

#### 3.2 Wallet Creation

**Tool**: `create_wallet`

- **Purpose**: Create new wallets programmatically (if using CDP Wallet API)
- **Note**: Only available with Coinbase CDP Wallet Provider

### Phase 4: Smart Contract Interactions (Priority: Low)

#### 4.1 Token Information

**Tool**: `get_token_info`

- **Purpose**: Get information about USDC token (decimals, symbol, contract address)
- **Implementation**: Query blockchain for token metadata

#### 4.2 Smart Contract Invocation

**Tool**: `invoke_contract`

- **Purpose**: Interact with smart contracts (for advanced use cases)
- **Use Cases**:
  - Interacting with hotel booking smart contracts
  - Token swaps
  - DeFi integrations

## Architecture Changes

### Current Flow

```
User Input → Supervisor Agent → Specialized Agents → MCP Tools → x402 Payment
```

### New Flow

```
User Input → Supervisor Agent → Specialized Agents → MCP Tools → CDP SDK USDC Payment
                                                                  ↓
                                            Wallet Manager ←→ Balance Check
                                                                  ↓
                                            Transaction History Storage
                                                                  ↓
                                            Optional: DeFi/NFT Integration
```

## Implementation Architecture

### 1. AgentKit Integration Layer

Create a new module: `backend/app/wallet/agentkit_wallet.py`

```python
"""
Coinbase AgentKit wallet integration layer.
Provides wallet management capabilities using Coinbase AgentKit.
"""

from agentkit import AgentKit, CdpWalletProvider
from eth_account import Account
import os
from typing import Optional

class AgentKitWalletManager:
    """
    Manages wallet operations using Coinbase AgentKit.
    Supports both CDP Wallet Provider and local private key wallets.
    """

    def __init__(self):
        self.agentkit: Optional[AgentKit] = None
        self.wallet_provider: Optional[CdpWalletProvider] = None
        self._initialize_wallet()

    def _initialize_wallet(self):
        """Initialize wallet provider based on configuration."""
        # Check if CDP credentials are available
        # Note: Exact env var names depend on AgentKit/CDP SDK Python package
        cdp_api_key_id = os.getenv("CDP_API_KEY_ID") or os.getenv("CDP_API_KEY_NAME")
        cdp_api_key_private_key = os.getenv("CDP_API_KEY_PRIVATE_KEY") or os.getenv("CDP_API_KEY_SECRET")
        cdp_wallet_id = os.getenv("CDP_WALLET_ID")
        cdp_wallet_secret = os.getenv("CDP_WALLET_SECRET")
        network_id = os.getenv("CDP_NETWORK_ID", "base-sepolia")

        if cdp_api_key_id and cdp_api_key_private_key and (cdp_wallet_id or cdp_wallet_secret):
            # Use CDP Wallet Provider
            # Example initialization (exact API may vary):
            # wallet_provider = CdpWalletProvider.configure_with_wallet(
            #     api_key_id=cdp_api_key_id,
            #     private_key=cdp_api_key_private_key,
            #     wallet_id=cdp_wallet_id,  # or wallet_secret=cdp_wallet_secret
            #     network_id=network_id,
            # )
            # self.agentkit = AgentKit.from_config({
            #     "wallet_provider": wallet_provider,
            #     "action_providers": [],  # can extend later (DeFi, swaps, etc.)
            # })
            pass  # TODO: Implement with actual AgentKit Python SDK API
        else:
            # Fallback to private key (current implementation)
            # AgentKit can work with private keys via Viem/EthAccount provider
            private_key = os.getenv("PRIVATE_KEY")
            if private_key:
                if not private_key.startswith("0x"):
                    private_key = "0x" + private_key
                # Initialize with private key wallet
                # Note: This requires ViemWalletProvider or similar
                pass

    async def get_balance(self, asset_id: str = "usdc") -> dict:
        """Get wallet balance for specified asset."""
        if not self.agentkit:
            raise ValueError("Wallet not initialized")
        balance = self.agentkit.get_balance(asset_id=asset_id)
        return {
            "asset_id": asset_id,
            "balance": balance,
            "formatted_balance": f"{balance} {asset_id.upper()}"
        }

    async def transfer(
        self,
        recipient: str,
        amount: float,
        asset_id: str = "usdc",
        gasless: bool = True
    ) -> dict:
        """Transfer assets to another address."""
        if not self.agentkit:
            raise ValueError("Wallet not initialized")
        transfer_result = self.agentkit.transfer(
            amount=amount,
            asset_id=asset_id,
            destination=recipient,
            gasless=gasless
        )
        transfer_result.wait()  # Wait for confirmation
        return {
            "success": True,
            "transaction_hash": transfer_result.hash,
            "amount": amount,
            "asset_id": asset_id,
            "recipient": recipient
        }

    def get_wallet_address(self) -> str:
        """Get the wallet address."""
        if self.wallet_provider:
            return self.wallet_provider.address
        # Fallback to private key wallet
        private_key = os.getenv("PRIVATE_KEY")
        if private_key:
            if not private_key.startswith("0x"):
                private_key = "0x" + private_key
            account = Account.from_key(private_key)
            return account.address
        raise ValueError("No wallet configured")
```

### 2. Updated Agent Tools

Integrate wallet management tools into `seapay_agent.py`:

```python
from ..wallet.agentkit_wallet import AgentKitWalletManager

# Initialize wallet manager (singleton)
_wallet_manager = AgentKitWalletManager()

@function_tool
async def check_wallet_balance(
    ctx: RunContextWrapper[SeaPayContext],
    asset_id: str = "usdc"
) -> dict[str, Any]:
    """Check USDC balance in wallet."""
    try:
        balance_info = await _wallet_manager.get_balance(asset_id)
        wallet_address = _wallet_manager.get_wallet_address()

        # Format response for user
        message = (
            f"Wallet Balance:\n"
            f"Address: {wallet_address}\n"
            f"Balance: {balance_info['formatted_balance']}"
        )

        return {
            "success": True,
            "wallet_address": wallet_address,
            "balance": balance_info["balance"],
            "asset_id": asset_id,
            "formatted_balance": balance_info["formatted_balance"],
            "message": message
        }
    except Exception as e:
        logger.error(f"[ERROR] Balance check failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to check balance: {str(e)}"
        }
```

### 3. Enhanced Payment Flow

#### 3.1 Clarify 402 Payload Contract

Ensure `reserve` MCP tool's 402 response body includes:

- `amount` (integer micro-USDC)
- `currency` (USDC)
- `network` (base or base-sepolia)
- `pay_to` (merchant wallet address) – if not present, add this on the SeaPay backend

#### 3.2 Update RESERVE_PAYMENT_INSTRUCTIONS

Modify instructions for `payment_agent` to:

1. First use `get_wallet_info` to verify sufficient USDC/gas
2. Then call `pay_invoice_with_usdc` with:
   - `amount_usdc = amount / 1_000_000` (convert micro-USDC to USDC)
   - `destination_address = pay_to`
   - `network` from the payload
3. If payment succeeds, choose one of two options:

**Option A**: Call `make_payment` purely as a "confirm reservation in backend" without x402 (backend trusts on-chain payment)

**Option B**: Replace `make_payment` with a new tool `confirm_reservation_after_onchain_payment` that only calls a non-402 API endpoint

#### 3.3 Intermediate Step: Dual-Mode Payment

During migration, let the agent:

- Use `get_wallet_info` and show the wallet to user ("This is the wallet that will pay via SeaPay's x402 flow.")
- Still call `make_payment` which uses x402
- Once confident with AgentKit, switch to direct USDC transfers

#### 3.4 Updated Payment Tool Example

```python
@function_tool
async def pay_invoice_with_usdc(
    ctx: RunContextWrapper[SeaPayContext],
    amount_usdc: float,
    destination_address: str,
    memo: str | None = None,
    network: str = "base-sepolia"
) -> dict[str, Any]:
    """
    Pay an invoice using USDC transfer with approval flow.
    """
    # 1. Show approval widget (reuse existing pattern)
    approval_question = f"I want to pay {amount_usdc} USDC to {destination_address[:10]}... for {memo or 'this reservation'}. Do you approve?"
    widget = build_approval_widget(question=approval_question)
    await ctx.context.stream_widget(widget, copy_text=approval_question)

    # Wait for approval (reuse approval_event pattern)
    await approval_event.wait()
    approval_event.clear()

    if not approval_result:
        return {"success": False, "error": "User rejected payment"}

    # 2. Execute transfer using AgentKit
    transfer_result = await _wallet_manager.transfer(
        recipient=destination_address,
        amount=amount_usdc,
        asset_id="usdc",
        gasless=True
    )

    # 3. Return transaction details
    return {
        "success": True,
        "transaction_hash": transfer_result["transaction_hash"],
        "amount": amount_usdc,
        "currency": "USDC",
        "network": network,
        "status": "confirmed"
    }
```

## Environment Configuration

Update `.env.example`:

```bash
# SeaPay Backend Configuration

# Coinbase CDP Configuration
CDP_API_KEY_NAME=your_cdp_api_key_name
CDP_API_KEY_PRIVATE_KEY=your_cdp_api_private_key

# Wallet Configuration (choose one)
# Option 1: Persistent wallet (recommended for production)
CDP_WALLET_DATA={"wallet_id": "...", "seed": "..."}  # JSON string with wallet data
# OR
CDP_WALLET_ID=your_cdp_wallet_id
CDP_WALLET_SECRET=your_cdp_wallet_secret

# Option 2: Let agent create new wallet on first run (development)
# Leave wallet config empty to auto-create

# Network Configuration
NETWORK_ID=base-sepolia  # or base-mainnet, ethereum-mainnet, etc.
CDP_NETWORK_ID=base-sepolia  # Alias for NETWORK_ID

# Legacy (for backward compatibility with x402)
PRIVATE_KEY=your_ethereum_private_key  # Keep for x402 if needed during migration

# SeaPay API Base URL
SEAPAY_API_BASE_URL=your_api_url

# OpenAI API Key
OPENAI_API_KEY=your_open_ai_api_key
```

### Wallet Ownership Model

**Phase 1 (Simple)**: One AgentKit/CDP smart wallet controlled by the backend (similar to today's single EOA), used for all bookings.

**Phase 2 (Advanced)**: Per-user or per-thread wallets, so each user has their own smart wallet; the agent manages them on their behalf.

### Network Choices

- **Dev/Test**: `base-sepolia` for hotels test environment (already referenced in prompt instructions for 402)
- **Prod**: `base-mainnet` when ready

### Payment Semantics

- Keep pricing and settlement in USDC as already done conceptually
- 402 amounts ÷ 10^6 for 6-decimals (micro-USDC to USDC conversion)
- Decide whether:
  - **Option A**: Still call SeaPay `/api/reserve` that triggers on-chain payment internally, or
  - **Option B**: Move to "pay merchant address directly with USDC" model and let SeaPay confirm by listening on-chain

The plan assumes Phase 1: keep `/api/reserve`, but have the agent explicitly manage its wallet and payments using AgentKit.

## Dependencies

Update `pyproject.toml`:

```toml
dependencies = [
    # ... existing dependencies ...
    "coinbase-agentkit>=0.1.0",  # Core AgentKit SDK
    "coinbase-agentkit-langchain>=0.1.0",  # If using LangChain integration (optional)
    "cdp-sdk>=0.1.0",  # Coinbase Developer Platform SDK
    "eth-account",  # Keep for backward compatibility with x402 (can remove after migration)
    "x402",  # Keep for backward compatibility (can remove after migration)
]
```

### Configuration Module

Add a small `wallet_config.py` (or `agentkit_config.py`) in `backend/app/`:

- Reads env vars
- Creates a singleton `AgentKit` + `CdpWalletProvider`
- Expose helper `get_agentkit()` / `get_wallet()` functions

Example structure:

```python
from coinbase_agentkit import AgentKit, CdpWalletProvider
import os

_wallet_provider = None
_agentkit = None

def get_wallet_provider():
    global _wallet_provider
    if _wallet_provider is None:
        _wallet_provider = CdpWalletProvider.configure_with_wallet(
            api_key_id=os.getenv("CDP_API_KEY_ID"),
            private_key=os.getenv("CDP_API_KEY_PRIVATE_KEY"),
            wallet_id=os.getenv("CDP_WALLET_ID"),
            network_id=os.getenv("CDP_NETWORK_ID", "base-sepolia"),
        )
    return _wallet_provider

def get_agentkit():
    global _agentkit
    if _agentkit is None:
        _agentkit = AgentKit.from_config({
            "wallet_provider": get_wallet_provider(),
            "action_providers": [],  # can extend later (DeFi, swaps, etc.)
        })
    return _agentkit
```

## Surface Wallet State in Conversation & Widgets

### 5.1 Wallet Summary Messages

On first booking in a thread, have the supervisor agent:

- Call `get_wallet_info`
- Summarize to user: address (shortened), USDC balance, network
- Optionally ask user to fund it if balance is low (for non-custodial patterns)

### 5.2 Wallet Widgets

Add a `wallet_status_widget` similar to `hotel_card_widget`:

- Show address, USDC balance, gas balance, recent txs
- Add a tool `show_wallet_status` that:
  - Calls `get_wallet_info` and `get_wallet_activity`
  - Builds and streams a widget with that data

### 5.3 Use Existing Approval UX

For any AgentKit "spend" tools:

- Reuse `tool_approval_widget.py` UI and approval events in `server.py`
- This keeps consistent UX for both MCP calls and on-chain actions
- The `request.approve` and `request.reject` actions are already handled in `server.py`

## Implementation Roadmap

### Week 1-2: Foundation

1. **Install and configure Coinbase AgentKit SDK**

   - Install `coinbase-agentkit` and `cdp-sdk` packages
   - Set up Coinbase Developer Portal account
   - Obtain CDP API keys

2. **Replace eth-account with CDP SDK wallet**

   - Create `wallet_config.py` module with singleton pattern
   - Initialize CDP Wallet Provider
   - Support both persistent wallets (from seed) and new wallet creation
   - Store wallet data securely

3. **Update environment variables and configuration**

   - Update `.env.example` with CDP configuration
   - Create configuration module for wallet initialization
   - Implement fallback to private key for backward compatibility

4. **Implement basic wallet creation and management**
   - `create_wallet` tool
   - `get_wallet_address` tool
   - `export_wallet` tool (with approval)

### Week 3-4: Core Payment Integration

1. **Modify `make_payment` to use CDP SDK USDC transfers**

   - Replace x402 flow with CDP SDK transfers
   - Implement gasless USDC transfer support (Base network)
   - Add balance checking before payments

2. **Create wallet management tools**

   - `check_wallet_balance` tool
   - `get_wallet_info` tool
   - `pay_invoice_with_usdc` tool with approval flow

3. **Test payment flow end-to-end**
   - Test on Base Sepolia testnet
   - Verify gasless USDC transfers
   - Test balance checks and error handling

### Week 5-6: Enhanced Features

1. **Implement token swap functionality**

   - `swap_tokens` tool for multi-currency support
   - Integration with DEX protocols via AgentKit action providers

2. **Add faucet funds request for testnet**

   - `request_faucet_funds` tool
   - Base Sepolia faucet integration

3. **Integrate transaction history**

   - `get_wallet_activity` tool
   - Transaction status checking

4. **Create wallet info widget for frontend display**

   - `wallet_status_widget` similar to `hotel_card_widget`
   - `show_wallet_status` tool

5. **Add multi-currency support**
   - Support for ETH, WETH, and other tokens
   - Automatic conversion suggestions

### Week 7-8: Advanced Features (Optional)

1. **NFT booking receipts**

   - `mint_booking_receipt_nft` tool
   - Metadata integration (hotel images, dates, confirmation)

2. **Loyalty token system**

   - `deploy_loyalty_token` tool
   - `award_loyalty_tokens` tool
   - Integration with booking flow

3. **Smart contract escrow**

   - `create_booking_escrow` tool
   - Check-in verification integration

4. **DeFi yield integration**

   - `stake_usdc_for_yield` tool
   - `unstake_usdc` tool
   - Automatic yield optimization

5. **Multi-wallet support**
   - `connect_external_wallet` tool
   - Support for Privy, MetaMask, Coinbase Wallet

### Week 9+: Agent Intelligence Enhancements

1. **Price Optimization Agent**

   - Monitor token prices
   - Suggest optimal payment timing
   - Calculate best swap routes

2. **Budget Manager Agent**

   - Track booking budget
   - Suggest alternatives within budget
   - Provide spending analytics

3. **Gas Fee Optimizer**
   - `estimate_gas_fees` tool
   - Suggest gasless transfers when available

## Additional Interesting Functions to Consider

### 1. Price Oracle Integration

- **Tool**: `get_usdc_price`
- **Purpose**: Get current USDC/USD exchange rate
- **Use Case**: Display prices in USD equivalent

### 2. Gas Price Estimation

- **Tool**: `estimate_gas_cost`
- **Purpose**: Estimate gas costs for transactions
- **Use Case**: Show total cost including gas fees

### 3. Payment Scheduling

- **Tool**: `schedule_payment`
- **Purpose**: Schedule payments for future dates
- **Use Case**: Pre-pay for future reservations

### 4. Multi-Currency Support

- **Tool**: `convert_currency`
- **Purpose**: Convert between different cryptocurrencies
- **Use Case**: Accept payments in multiple tokens

### 5. Payment Splitting

- **Tool**: `split_payment`
- **Purpose**: Split payments between multiple recipients
- **Use Case**: Split hotel costs between multiple guests

### 6. Recurring Payments

- **Tool**: `setup_recurring_payment`
- **Purpose**: Set up subscription-style payments
- **Use Case**: Monthly hotel subscriptions or loyalty programs

### 7. Payment Escrow

- **Tool**: `create_escrow`
- **Purpose**: Hold funds in escrow until conditions are met
- **Use Case**: Hold payment until check-in confirmation

### 8. Refund Processing

- **Tool**: `process_refund`
- **Purpose**: Process refunds for cancellations
- **Use Case**: Hotel cancellation refunds

### 9. Payment Analytics

- **Tool**: `get_payment_analytics`
- **Purpose**: Get spending analytics and insights
- **Use Case**: User spending reports

### Additional Interesting Features

#### 1. Split Payment Support

- Multiple users can contribute USDC to a single booking
- Smart contract manages collection and refunds
- **Tool**: `split_payment` - Split payments between multiple recipients

#### 2. Subscription Model

- Deploy ERC-20 subscription token
- Monthly fee for premium bookings
- Automatic renewal via smart contract
- **Tool**: `setup_subscription` - Set up recurring payments

#### 3. Dynamic Pricing with Oracles

- Integrate Chainlink oracles for real-time pricing
- Convert hotel prices from fiat to USDC automatically
- Price protection: lock in USDC rate at booking time
- **Tool**: `get_usdc_price` - Get USDC/USD exchange rate

#### 4. Social Features

- Share booking NFTs with friends
- Gift hotel stays as transferable NFTs
- Group booking coordination via multi-sig wallet

#### 5. Insurance Integration

- Optional travel insurance via DeFi protocol
- Pay small premium in USDC
- Automatic claim processing via oracle verification
- **Tool**: `purchase_travel_insurance` - Buy insurance for booking

#### 6. Carbon Offset NFTs

- Purchase carbon offset for travel
- Mint NFT proof of eco-friendly booking
- Integrate with carbon credit protocols
- **Tool**: `purchase_carbon_offset` - Buy carbon offset NFT

#### 7. Referral Program

- Smart contract-based referral tracking
- Automatic USDC rewards for successful referrals
- On-chain transparent reward distribution
- **Tool**: `track_referral` - Track and reward referrals

#### 8. Multi-User & Shared Wallets

- Per-user smart wallets managed by the agent, with:
  - Spending limits
  - "Split payment" tools (pay part from user A, part from user B)
  - Shared trip wallets for group bookings

#### 9. Token & FX Management

- Tools to:
  - Swap other tokens to USDC (e.g. WETH → USDC) using DEX integrations through AgentKit action providers
  - Quote fiat → USDC conversions and show equivalent amounts

#### 10. Risk/Compliance Helpers

- Use AgentKit / CDP features or custom actions to:
  - Screen destination addresses (sanctions/compliance)
  - Check transaction history to detect suspicious patterns
  - **Tool**: `screen_address` - Check address against compliance lists

## Security Considerations & Guardrails

1. **Private Key Management**:

   - Never log private keys
   - Use environment variables or secure key management
   - Consider using CDP Wallet API for better security

2. **Transaction Approval**:

   - All transfers require explicit user approval via approval widget
   - Reuse existing `custom_mcp_approval_function` pattern for wallet actions
   - Log all wallet operations for audit

3. **Balance Checks**:

   - Always verify balance before payments using `get_wallet_info`
   - Implement spending limits if needed
   - Warn users about low balances

4. **Spend Limits**:

   - Hard-code limits per transaction (e.g., < 100 USDC in tools)
   - Per-thread spending limits
   - Configurable via environment variables

5. **Network & Address Whitelisting**:

   - Whitelist networks (only allow base-sepolia in dev, base-mainnet in prod)
   - Only allow known merchant addresses (SeaPay, test merchants)
   - Validate `destination_address` against whitelist before transfers

6. **Error Handling**:
   - Graceful degradation if AgentKit unavailable
   - Clear error messages without exposing sensitive info
   - Fallback to existing x402 implementation

## Testing Strategy

1. **Unit Tests** (backend only, no UI):

   - For `wallet_tools.py`:
     - Mock CDP/AgentKit client and assert:
       - Correct parsing of amounts and networks
       - Proper error messages when insufficient balance or network mismatch
       - Wallet creation and export functionality
       - Token swap calculations
   - For `payment_agent` logic:
     - Prompt-level tests (or scripted tool-calls) that:
       - Given a 402 payload, the agent chooses `get_wallet_info` → `pay_invoice_with_usdc`
   - For wallet manager:
     - Test CDP SDK initialization
     - Test fallback to private key
     - Test wallet persistence

2. **Integration Tests on base-sepolia**:

   - Use actual CDP test keys and Base Sepolia:
     - Fund wallet with USDC via faucet
     - Run end-to-end "book a hotel → pay with USDC" flow
     - Verify on-chain transfer and backend reservation
     - Test gasless USDC transfers
     - Test token swaps (ETH → USDC)
     - Test transaction history retrieval

3. **Mainnet Testing** (Small transactions first):

   - Test on Base Mainnet with small amounts
   - Verify gasless USDC transfers work
   - Test DeFi integrations (staking/unstaking)
   - Verify NFT minting for booking receipts

4. **Manual Testing**:
   - Test on Base Sepolia testnet
   - Verify all wallet operations
   - Test error scenarios
   - Test approval flow for wallet actions
   - Test faucet fund requests
   - Test multi-currency support

## Success Metrics

1. **Functionality**:

   - ✅ Wallet balance checking works correctly
   - ✅ Payments include balance verification
   - ✅ Transaction history is accessible
   - ✅ Transfers execute successfully

2. **User Experience**:

   - ✅ Clear wallet information display
   - ✅ Helpful error messages
   - ✅ Smooth payment flow

3. **Reliability**:
   - ✅ Graceful fallback if AgentKit unavailable
   - ✅ Proper error handling
   - ✅ Transaction confirmation

## Risk Mitigation

1. **Private Key Security**:

   - Use CDP SDK's secure key management (don't store private keys directly)
   - Never log private keys or seed phrases
   - Use environment variables or secure key management services

2. **Gas Fee Spikes**:

   - Use Base network for low fees
   - Implement gasless USDC transfers
   - Monitor gas prices and suggest optimal timing

3. **Failed Transactions**:

   - Implement robust error handling and retry logic
   - Provide clear error messages to users
   - Log transaction failures for debugging

4. **Balance Management**:

   - Always check balance before transactions
   - Warn users about insufficient funds
   - Suggest funding options (faucet, swap, etc.)

5. **Network Issues**:

   - Support multiple RPC endpoints for redundancy
   - Implement connection retry logic
   - Graceful degradation if CDP SDK unavailable

6. **Smart Contract Risks**:
   - Audit escrow contracts before deployment
   - Test thoroughly on testnet before mainnet
   - Implement timeouts and cancellation policies

## Documentation Updates

Per project rules, update the following files:

- **docs/DirectoryStructure.md**: Document new wallet service modules (`app/wallet/`, `app/agents/wallet_tools.py`)
- **docs/ProjectGoals.md**: Add wallet management and crypto payment goals
- **docs/TASK.md**: Track implementation tasks with phases and priorities
- **docs/CHANGELOG.md**: Document all changes as they're implemented

## Recommended Starting Point

**Start with Phase 1** to get core wallet functionality working:

1. Replace eth-account with CDP SDK
2. Implement basic wallet management tools
3. Update payment flow to use USDC transfers
4. Test thoroughly on Base Sepolia

Then proceed to **Phase 2** for enhanced payment features based on user feedback and business requirements.

**Phase 3-4** advanced features can be implemented incrementally based on:

- User demand
- Business value
- Technical feasibility
- Regulatory considerations

## Conclusion

This implementation plan provides a comprehensive roadmap for integrating Coinbase AgentKit into the SeaPay agent. The phased approach allows for incremental development and testing, ensuring stability while adding powerful wallet management capabilities.

The integration will significantly enhance the agent's capabilities, providing users with:

- Better visibility into wallet status
- More reliable payments with gasless USDC transfers
- Multi-currency support and token swaps
- Advanced features like NFT receipts, loyalty tokens, and DeFi integration
- Intelligent agents for price optimization and budget management

**Key Sources**:

- [Coinbase AgentKit Documentation](https://docs.cdp.coinbase.com/agent-kit)
- [CDP SDK Python](https://github.com/coinbase/agentkit/tree/main/python)
- [AgentKit GitHub Repository](https://github.com/coinbase/agentkit)
