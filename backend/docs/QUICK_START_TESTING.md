# Quick Start: Testing AgentKit Integration

## Prerequisites

✅ All code has been implemented and is ready to test
✅ Dependencies are in `pyproject.toml`
✅ Environment variables need to be configured

## Step 1: Get CDP Credentials

1. Go to [Coinbase Developer Portal](https://portal.cdp.coinbase.com/)
2. Create an account or sign in
3. Create a new project
4. Generate API credentials:
   - API Key Name
   - API Private Key (download and save securely)

## Step 2: Configure Environment

Edit your `.env` file:

```bash
# Coinbase CDP Configuration
CDP_API_KEY_NAME=your_api_key_name_here
CDP_API_KEY_PRIVATE_KEY=your_private_key_here

# Network (testnet for development)
NETWORK_ID=base-sepolia
CDP_NETWORK_ID=base-sepolia

# Optional: Wallet ID (leave empty to create new wallet)
# CDP_WALLET_ID=
# CDP_WALLET_DATA=

# Existing configuration (keep these)
PRIVATE_KEY=your_ethereum_private_key_here
SEAPAY_API_BASE_URL=your_api_url
OPENAI_API_KEY=your_openai_api_key
```

## Step 3: Install/Update Dependencies

```bash
cd backend
uv sync
```

## Step 4: Start the Backend

```bash
cd backend
uvicorn app.main:app --reload
```

**On first run**, if no wallet is configured:

- The system will create a new CDP wallet
- It will log the wallet address and ID
- **IMPORTANT**: Save the wallet data from logs to `CDP_WALLET_DATA` in `.env`

## Step 5: Fund Your Wallet

### Option A: Using Base Sepolia Faucet

1. Copy your wallet address from the logs
2. Visit [Base Sepolia Faucet](https://www.coinbase.com/faucets/base-sepolia-faucet)
3. Request testnet ETH (for gas, though gasless is preferred)

### Option B: Get Testnet USDC

1. Use a testnet USDC faucet or DEX
2. Or bridge testnet ETH to USDC on a DEX

## Step 6: Test Wallet Features

### Test 1: Show Wallet Status

**User Input**: "Show me my wallet" or "What's my wallet address?"

**Expected Output**:

- Visual widget showing wallet information
- Address (shortened)
- Network (base-sepolia)
- USDC balance
- ETH balance
- Gasless transfer status

### Test 2: Check Balance

**User Input**: "How much USDC do I have?"

**Expected Output**:

- Text response with USDC balance
- Wallet address

### Test 3: Book Hotel with Payment

**User Input**: "Book a hotel in San Francisco for Dec 15-17 for 2 guests"

**Expected Flow**:

1. Agent searches for hotels
2. Shows hotel cards
3. User selects a hotel
4. Agent creates reservation
5. Agent checks wallet balance
6. Agent shows payment approval widget
7. User approves payment
8. Agent transfers USDC (gasless)
9. Agent confirms reservation

### Test 4: Transaction History

**User Input**: "Show my recent transactions"

**Expected Output**:

- List of recent transactions
- Transaction hashes
- Amounts and counterparties
- Timestamps

## Step 7: Verify Transaction

1. Copy the transaction hash from the payment confirmation
2. Visit [Base Sepolia Explorer](https://sepolia.basescan.org/)
3. Paste the transaction hash
4. Verify the USDC transfer appears on-chain

## Troubleshooting

### Issue: "CDP wallet not initialized"

**Solution**: Check CDP credentials in `.env`:

```bash
CDP_API_KEY_NAME=should_not_be_empty
CDP_API_KEY_PRIVATE_KEY=should_not_be_empty
```

### Issue: "Insufficient balance"

**Solution**: Fund your wallet with testnet USDC:

1. Get wallet address from `show_wallet_status`
2. Use faucet or DEX to get USDC
3. Wait for transaction to confirm

### Issue: "Network mismatch"

**Solution**: Ensure network is set correctly:

```bash
NETWORK_ID=base-sepolia
CDP_NETWORK_ID=base-sepolia
```

### Issue: Wallet creation fails

**Solution**: Check CDP API credentials are valid:

1. Verify API key has not expired
2. Ensure private key is correct format
3. Check Coinbase Developer Portal for issues

## Common Test Scenarios

### Scenario 1: New User

```
User: Hi, I want to book a hotel
Agent: [Greets and asks for details]
User: Show my wallet first
Agent: [Shows wallet status widget]
User: Book hotel in NYC for Dec 20-22
Agent: [Shows hotels, user selects, payment flow]
```

### Scenario 2: Insufficient Balance

```
User: Book hotel in Miami
Agent: [Shows hotels, user selects]
Agent: [Checks balance, finds insufficient funds]
Agent: "You need 0.05 USDC but only have 0.01 USDC.
       Please fund your wallet."
```

### Scenario 3: Successful Payment

```
User: Book Grand Plaza Hotel
Agent: [Creates reservation, gets 402 response]
Agent: [Checks balance - sufficient]
Agent: [Shows approval widget]
Agent: "I want to pay 0.02 USDC to [merchant] for reservation. Approve?"
User: [Clicks Approve]
Agent: [Transfers USDC]
Agent: "Payment confirmed! Transaction: 0x123..."
```

## Expected Log Output

When everything works, you should see logs like:

```
[WALLET] Wallet manager initialized
[WALLET] CDP wallet initialized successfully: 0x1234...5678
[TOOL CALL] get_wallet_info
[WALLET] Wallet: 0x1234...5678, Network: base-sepolia
[TOOL CALL] pay_invoice_with_usdc: 0.02 USDC to 0xabcd...
[WALLET] Transferring 0.02 USDC to 0xabcd... (gasless: True)
[WALLET] Transfer completed: 0x9876...
```

## Next Steps After Testing

Once testing is successful:

1. ✅ Verify all features work as expected
2. ✅ Save wallet data securely
3. ✅ Test edge cases (insufficient balance, invalid addresses)
4. ✅ Review transaction history on explorer
5. 🚀 Ready for production deployment (with mainnet credentials)

## Production Deployment

Before going to production:

1. Change network to `base-mainnet`:

   ```bash
   NETWORK_ID=base-mainnet
   CDP_NETWORK_ID=base-mainnet
   ```

2. Use production CDP credentials

3. Fund wallet with real USDC

4. Test with small amounts first

5. Implement additional security:
   - Spend limits
   - Address whitelisting
   - Rate limiting
   - Comprehensive logging

## Support

If you encounter issues:

1. Check logs in terminal
2. Review `AGENTKIT_IMPLEMENTATION_SUMMARY.md`
3. Check CDP SDK documentation
4. Verify environment variables
5. Test with fallback private key wallet

## Success Indicators

✅ Wallet initializes without errors
✅ Balance check returns valid data
✅ Wallet status widget displays correctly
✅ Payment approval widget appears
✅ USDC transfer completes successfully
✅ Transaction appears on Base Sepolia explorer
✅ Transaction history retrieves data

---

**Ready to test!** Follow these steps and you'll have a working AgentKit integration.
