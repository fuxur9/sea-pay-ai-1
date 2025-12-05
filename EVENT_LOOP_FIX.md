# Event Loop Fix - CDP Wallet Initialization

## Issue

The CDP Smart Wallet initialization was failing with:

```
ERROR: Failed to initialize CDP Smart Wallet: this event loop is already running.
```

And later:

```
ValueError: Can't patch loop of type <class 'uvloop.Loop'>
```

## Root Cause

The CDP AgentKit was trying to create or access an event loop during module import (in `__init__`), but FastAPI/uvicorn uses `uvloop` and already has an event loop running. This caused conflicts because:

1. **First attempt**: Direct initialization in `__init__` → "event loop already running"
2. **Second attempt**: Using `nest_asyncio` → "Can't patch uvloop"

## Solution: Lazy Initialization

Implemented **lazy initialization** pattern where the CDP wallet is only initialized when first accessed, not during module import.

### Changes Made

#### 1. Modified `__init__` to defer initialization

**Before**:

```python
def __init__(self):
    self.agentkit = None
    self.wallet_provider = None
    self._fallback_account = None
    self._network_id = os.getenv("NETWORK_ID", "base-sepolia")
    self._initialize_wallet()  # ← Ran immediately during import
```

**After**:

```python
def __init__(self):
    self.agentkit = None
    self.wallet_provider = None
    self._fallback_account = None
    self._network_id = os.getenv("NETWORK_ID", "base-sepolia")
    self._initialization_attempted = False
    self._cdp_credentials = self._get_cdp_credentials()
    # Don't initialize here - will be done lazily on first use
```

#### 2. Added lazy initialization helpers

```python
def _get_cdp_credentials(self) -> dict[str, Optional[str]]:
    """Get CDP credentials from environment variables."""
    return {
        "api_key_id": os.getenv("CDP_API_KEY_ID"),
        "api_key_secret": os.getenv("CDP_API_KEY_SECRET"),
        "wallet_secret": os.getenv("CDP_WALLET_SECRET"),
        "owner_private_key": os.getenv("PRIVATE_KEY"),
    }

def _ensure_initialized(self) -> None:
    """Ensure wallet is initialized (lazy initialization)."""
    if self._initialization_attempted:
        return

    self._initialization_attempted = True
    self._initialize_wallet()
```

#### 3. Updated all methods to call lazy initialization

Added `self._ensure_initialized()` at the start of:

- `get_wallet_address()`
- `get_network_id()`
- `get_balance()`
- `get_wallet_info()`
- `transfer_usdc()`

### Example

```python
def get_wallet_address(self) -> str:
    """Get the wallet address."""
    self._ensure_initialized()  # ← Only initialize on first call

    if self.wallet_provider:
        return self.wallet_provider.get_address()
    # ...
```

## How It Works

```
1. Module Import
   ↓
   __init__() called
   ↓
   Store credentials (no CDP initialization yet)
   ↓
2. First wallet method call
   ↓
   _ensure_initialized() called
   ↓
   _initialize_wallet() runs NOW (within existing event loop)
   ↓
   CDP wallet created successfully
   ↓
3. Subsequent calls
   ↓
   _ensure_initialized() returns immediately (already done)
```

## Benefits

1. ✅ **No event loop conflicts** - Initialization happens within FastAPI's existing loop
2. ✅ **Works with uvloop** - No need for nest_asyncio patching
3. ✅ **Faster startup** - Module imports quickly, initialization deferred
4. ✅ **Same functionality** - Transparent to users of the wallet manager

## Files Modified

1. **`backend/pyproject.toml`** - Added `nest-asyncio>=1.5.0` (not ultimately needed, but safe to keep)
2. **`backend/app/wallet/agentkit_wallet.py`** - Implemented lazy initialization pattern

## Testing

After this fix:

```
✅ Backend starts successfully:
INFO: Application startup complete.

✅ No event loop errors

✅ CDP wallet initializes on first use:
INFO: [WALLET] Initializing CDP Smart Wallet...
INFO: [WALLET] CDP Smart Wallet initialized successfully: 0x...
```

## Migration Notes

This is a **breaking change** for any code that expected the wallet to be initialized immediately. However, in our codebase:

- ✅ All wallet methods already work (they call `_ensure_initialized()`)
- ✅ Singleton pattern still works correctly
- ✅ No changes needed in calling code

## Summary

The lazy initialization pattern allows the CDP wallet to be created within the existing FastAPI event loop, avoiding conflicts with uvloop. The wallet is initialized transparently on first use, with no impact on functionality.

**Status**: ✅ Fixed and verified working!
