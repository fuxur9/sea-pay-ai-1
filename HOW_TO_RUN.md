# How to Run the SeaPay Chat Application

## Quick Start (Recommended)

Run both frontend and backend together with one command:

```bash
# From the project root directory
npm run dev
```

This will start:

- ✅ **Backend** (Python/FastAPI) on http://localhost:8002
- ✅ **Frontend** (React/Vite) on http://localhost:5172

Then open your browser to: **http://localhost:5172**

## Prerequisites

### 1. Install Required Software

- **Node.js** >= 18.18 ([Download](https://nodejs.org/))
- **Python** 3.11+ ([Download](https://www.python.org/))
- **uv** package manager ([Install](https://docs.astral.sh/uv/))

### 2. Set Environment Variables

Create a `.env` file in the `backend/` directory:

```bash
# Required
OPENAI_API_KEY=your_openai_api_key

# Coinbase CDP Configuration (for AgentKit wallet)
CDP_API_KEY_NAME=your_cdp_api_key_name
CDP_API_KEY_PRIVATE_KEY=your_cdp_api_private_key

# Network
NETWORK_ID=base-sepolia
CDP_NETWORK_ID=base-sepolia

# Optional: Existing wallet
# CDP_WALLET_ID=your_wallet_id
# CDP_WALLET_DATA={"wallet_id": "...", "seed": "..."}

# Backward compatibility (fallback wallet)
PRIVATE_KEY=your_ethereum_private_key

# SeaPay API (if using external server)
SEAPAY_API_BASE_URL=https://your-seapay-server.com
```

Export frontend environment variable:

```bash
export VITE_CHATKIT_API_DOMAIN_KEY="domain_pk_local_dev"
```

Or add to your shell profile (~/.bashrc, ~/.zshrc):

```bash
echo 'export VITE_CHATKIT_API_DOMAIN_KEY="domain_pk_local_dev"' >> ~/.zshrc
source ~/.zshrc
```

## Step-by-Step Setup

### 1. Install Root Dependencies

```bash
cd /Users/fuchunhsieh/local-lab/sea-pay-ai
npm install
```

This installs `concurrently` to run both services together.

### 2. Setup Backend

The backend setup happens automatically when you run `npm run dev`, but you can also do it manually:

```bash
cd backend
uv sync
```

### 3. Setup Frontend

The frontend setup also happens automatically, but you can do it manually:

```bash
cd frontend
npm install
```

## Running the Application

### Option 1: Run Both Together (Recommended)

```bash
# From project root
npm run dev
```

**What happens:**

- Backend starts on port 8002
- Frontend starts on port 5172
- Both run concurrently in the same terminal
- Logs from both services appear together

**Access the app:** http://localhost:5172

### Option 2: Run Separately (Advanced)

If you want to run them in separate terminals for better log visibility:

**Terminal 1 - Backend:**

```bash
cd backend
uv sync
uvicorn app.main:app --reload --port 8002
```

**Terminal 2 - Frontend:**

```bash
cd frontend
npm install
npm run dev
```

**Access the app:** http://localhost:5172

## First Run - Wallet Setup

### On First Startup

If you haven't configured a CDP wallet, the system will:

1. ✅ Create a new CDP wallet automatically
2. ✅ Log the wallet address and ID
3. ⚠️ **IMPORTANT**: Copy the wallet data from logs

Look for logs like:

```
[WALLET] New wallet created: 0x1234...5678
[WALLET] Wallet ID: abc-123-def
[WALLET] Save the wallet data to CDP_WALLET_DATA environment variable:
{"wallet_id": "...", "seed": "..."}
```

### Save Your Wallet

Add to `backend/.env`:

```bash
CDP_WALLET_DATA={"wallet_id": "...", "seed": "..."}
```

This ensures you use the same wallet on restart.

### Fund Your Wallet

1. Get your wallet address from the logs or use: "Show me my wallet"
2. Visit [Base Sepolia Faucet](https://www.coinbase.com/faucets/base-sepolia-faucet)
3. Request testnet USDC

## Testing the Application

### Test 1: Check Wallet

In the chat:

```
You: Show me my wallet
```

Expected: Visual widget showing wallet address, network, and balances

### Test 2: Book a Hotel

In the chat:

```
You: Book a hotel in San Francisco for Dec 15-17 for 2 guests
```

Expected flow:

1. Agent searches hotels → Shows cards
2. You select a hotel
3. Agent checks wallet balance
4. Agent shows payment approval
5. You approve
6. Agent transfers USDC (gasless)
7. Confirmation with transaction hash

### Test 3: Check Balance

In the chat:

```
You: How much USDC do I have?
```

Expected: Text showing your USDC balance

## Stopping the Application

### If using `npm run dev`:

Press `Ctrl+C` in the terminal - this stops both frontend and backend

### If running separately:

Press `Ctrl+C` in each terminal window

## Troubleshooting

### Backend fails to start

**Check Python and uv:**

```bash
python --version  # Should be 3.11+
uv --version     # Should be installed
```

**Check environment variables:**

```bash
cd backend
cat .env  # Verify OPENAI_API_KEY is set
```

### Frontend fails to start

**Check Node.js:**

```bash
node --version  # Should be 18.18+
npm --version   # Should be 9+
```

**Check VITE variable:**

```bash
echo $VITE_CHATKIT_API_DOMAIN_KEY  # Should output: domain_pk_local_dev
```

### Port already in use

**Backend (port 8002):**

```bash
# Find process using port 8002
lsof -ti:8002 | xargs kill -9
```

**Frontend (port 5172):**

```bash
# Find process using port 5172
lsof -ti:5172 | xargs kill -9
```

### Wallet initialization fails

1. Check CDP credentials in `backend/.env`
2. Verify API key is valid at [Coinbase Developer Portal](https://portal.cdp.coinbase.com/)
3. Check backend logs for error messages

### "Cannot connect to backend"

1. Verify backend is running: `curl http://localhost:8002/health`
2. Check frontend proxy settings in `frontend/vite.config.ts`
3. Ensure CORS is configured correctly

## File Locations

- **Frontend**: `frontend/` - React app with ChatKit
- **Backend**: `backend/` - Python FastAPI with AgentKit
- **Wallet Module**: `backend/app/wallet/` - AgentKit integration
- **Agents**: `backend/app/agents/` - SeaPay booking agent
- **Widgets**: `backend/app/widgets/` - UI components
- **Environment**: `backend/.env` - Configuration

## Ports

- **Frontend**: http://localhost:5172
- **Backend**: http://localhost:8002
- **SeaPay Server** (optional, not needed for chat): http://localhost:3000

## Next Steps

1. ✅ Get CDP credentials from [Coinbase Developer Portal](https://portal.cdp.coinbase.com/)
2. ✅ Configure `backend/.env` with API keys
3. ✅ Run `npm run dev`
4. ✅ Fund wallet with testnet USDC
5. ✅ Test booking a hotel

## Documentation

- **AgentKit Setup**: `backend/docs/QUICK_START_TESTING.md`
- **Implementation Details**: `backend/docs/AGENTKIT_IMPLEMENTATION_SUMMARY.md`
- **Complete Guide**: `backend/docs/IMPLEMENTATION_COMPLETE.md`
- **Main README**: `README.md`

---

**Need Help?**

Check the detailed testing guide: `backend/docs/QUICK_START_TESTING.md`
