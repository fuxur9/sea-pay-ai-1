# Coinbase AgentKit Integration Plan for SeaPay Agent

## Executive Summary

This document outlines a comprehensive plan to integrate Coinbase AgentKit into the SeaPay hotel booking agent, enabling advanced wallet management capabilities and USDC payment functionality. The integration will enhance the agent's ability to manage wallets, check balances, transfer funds, and interact with blockchain networks.

## Current State Analysis

### Existing Implementation

- **Payment Method**: Currently uses `x402` protocol with `eth_account` for wallet management
- **Wallet Storage**: Private key stored in environment variable (`PRIVATE_KEY`)
- **Payment Flow**: Automatic payment handling via `x402HttpxClient` when HTTP 402 is received
- **Network**: Base Sepolia testnet
- **Currency**: USDC

### Current Limitations

1. **No wallet management UI**: Users cannot check balance, view transaction history, or manage wallet settings
2. **Single wallet per instance**: Only one wallet can be configured via environment variable
3. **No balance checking**: Agent cannot verify if wallet has sufficient funds before payment
4. **No transaction history**: No way to track past payments or transactions
5. **No multi-wallet support**: Cannot manage multiple wallets or switch between them
6. **Limited error handling**: Basic error handling for wallet configuration issues

## Coinbase AgentKit Features to Implement

### Phase 1: Core Wallet Management (Priority: High)

#### 1.1 Wallet Balance Checking

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

#### 1.2 Wallet Information Display

**Tool**: `get_wallet_info`

- **Purpose**: Display wallet address, network, and current balances
- **Implementation**:
  ```python
  @function_tool
  async def get_wallet_info(
      ctx: RunContextWrapper[SeaPayContext]
  ) -> dict[str, Any]:
      """
      Get comprehensive wallet information including address, network, and balances.
      """
  ```
- **Benefits**:
  - User can verify wallet address
  - See all asset balances at once
  - Understand which network the wallet is on

#### 1.3 Enhanced Payment Tool with Balance Check

**Enhancement**: Upgrade existing `make_payment` tool

- **New Features**:
  - Pre-payment balance check
  - Insufficient funds warning
  - Transaction status tracking
  - Better error messages with balance information

### Phase 2: Advanced Wallet Operations (Priority: Medium)

#### 2.1 USDC Transfer Capability

**Tool**: `transfer_usdc`

- **Purpose**: Allow agent to transfer USDC to other addresses
- **Implementation**:
  ```python
  @function_tool
  async def transfer_usdc(
      ctx: RunContextWrapper[SeaPayContext],
      recipient_address: str,
      amount: float,
      gasless: bool = True
  ) -> dict[str, Any]:
      """
      Transfer USDC to another address.
      Supports gasless transfers on Base network.
      """
  ```
- **Use Cases**:
  - Refund processing
  - Sending payments to hotel partners
  - User-initiated transfers
- **Security**: Requires explicit user approval before execution

#### 2.2 Transaction History

**Tool**: `get_transaction_history`

- **Purpose**: Retrieve and display recent transactions
- **Implementation**:
  ```python
  @function_tool
  async def get_transaction_history(
      ctx: RunContextWrapper[SeaPayContext],
      limit: int = 10
  ) -> dict[str, Any]:
      """
      Get recent transaction history for the wallet.
      """
  ```
- **Benefits**:
  - Users can review past payments
  - Audit trail for reservations
  - Debugging payment issues

#### 2.3 Transaction Status Check

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

### Phase 3: Multi-Wallet Support (Priority: Low)

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
        cdp_api_key = os.getenv("CDP_API_KEY_NAME")
        cdp_api_secret = os.getenv("CDP_API_KEY_SECRET")
        cdp_wallet_secret = os.getenv("CDP_WALLET_SECRET")
        network_id = os.getenv("CDP_NETWORK_ID", "base-sepolia")

        if cdp_api_key and cdp_api_secret and cdp_wallet_secret:
            # Use CDP Wallet Provider
            self.wallet_provider = CdpWalletProvider(
                api_key_name=cdp_api_key,
                api_key_private_key=cdp_api_secret,
                wallet_secret=cdp_wallet_secret,
                network_id=network_id
            )
            self.agentkit = AgentKit(wallet_provider=self.wallet_provider)
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

Update `make_payment` tool to include balance checking:

```python
@function_tool
async def make_payment(
    ctx: RunContextWrapper[SeaPayContext],
    hotelName: str,
    checkIn: str,
    checkOut: str,
    guests: int,
) -> dict[str, Any]:
    """
    Make a payment with pre-flight balance check.
    """
    # 1. Check balance first
    balance_info = await _wallet_manager.get_balance("usdc")
    current_balance = balance_info["balance"]

    # 2. Get payment amount from reservation request
    # (This would come from the 402 response in actual flow)

    # 3. Warn if insufficient funds
    # 4. Proceed with payment using x402 (existing flow)
    # 5. Return enhanced result with transaction details
```

## Environment Configuration

Update `.env.example`:

```bash
# SeaPay Backend Configuration

# Option 1: Coinbase CDP Wallet Provider (Recommended for production)
CDP_API_KEY_NAME=your_cdp_api_key_name
CDP_API_KEY_SECRET=your_cdp_api_key_secret
CDP_WALLET_SECRET=your_cdp_wallet_secret
CDP_NETWORK_ID=base-sepolia  # or base-mainnet

# Option 2: Private Key Wallet (Fallback/Development)
PRIVATE_KEY=your_ethereum_private_key_here

# SeaPay API Base URL
SEAPAY_API_BASE_URL=your_api_url

# OpenAI API Key
OPENAI_API_KEY=your_open_ai_api_key
```

## Dependencies

Update `pyproject.toml`:

```toml
dependencies = [
    # ... existing dependencies ...
    "coinbase-agentkit>=0.1.0",  # Add AgentKit
    "eth-account",  # Already present
    "x402",  # Already present
]
```

## Implementation Steps

### Step 1: Setup and Installation (Week 1)

1. Install `coinbase-agentkit` package
2. Set up Coinbase Developer Portal account (if using CDP Wallet)
3. Create wallet manager module
4. Update environment configuration

### Step 2: Core Wallet Tools (Week 1-2)

1. Implement `check_wallet_balance` tool
2. Implement `get_wallet_info` tool
3. Add wallet info widget for UI display
4. Test balance checking functionality

### Step 3: Enhanced Payment Flow (Week 2)

1. Integrate balance check into `make_payment` tool
2. Add insufficient funds warnings
3. Update payment agent instructions
4. Test end-to-end payment flow

### Step 4: Advanced Features (Week 3)

1. Implement `transfer_usdc` tool
2. Implement `get_transaction_history` tool
3. Add transaction status checking
4. Create transaction history widget

### Step 5: Testing and Refinement (Week 3-4)

1. Comprehensive testing of all wallet operations
2. Error handling improvements
3. User experience refinements
4. Documentation updates

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

### 10. Wallet Backup/Recovery

- **Tool**: `backup_wallet`
- **Purpose**: Generate wallet backup (if using local wallets)
- **Use Case**: Wallet recovery procedures

## Security Considerations

1. **Private Key Management**:

   - Never log private keys
   - Use environment variables or secure key management
   - Consider using CDP Wallet API for better security

2. **Transaction Approval**:

   - All transfers require explicit user approval
   - Implement approval widgets for sensitive operations
   - Log all wallet operations for audit

3. **Balance Checks**:

   - Always verify balance before payments
   - Implement spending limits if needed
   - Warn users about low balances

4. **Error Handling**:
   - Graceful degradation if AgentKit unavailable
   - Clear error messages without exposing sensitive info
   - Fallback to existing x402 implementation

## Testing Strategy

1. **Unit Tests**:

   - Wallet manager initialization
   - Balance checking
   - Transfer operations
   - Error handling

2. **Integration Tests**:

   - End-to-end payment flow with balance checks
   - Transaction history retrieval
   - Multi-tool interactions

3. **Manual Testing**:
   - Test on Base Sepolia testnet
   - Verify all wallet operations
   - Test error scenarios

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

## Conclusion

This implementation plan provides a comprehensive roadmap for integrating Coinbase AgentKit into the SeaPay agent. The phased approach allows for incremental development and testing, ensuring stability while adding powerful wallet management capabilities.

The integration will significantly enhance the agent's capabilities, providing users with better visibility into their wallet status, more reliable payments, and additional features like transfers and transaction history.
