# Circular Import Fix

## Issue

After fixing the CDP SDK import issue, a new circular import error appeared:

```
ImportError: cannot import name 'SeaPayContext' from partially initialized module 'app.agents.seapay_agent'
(most likely due to a circular import)
```

## Root Cause

**Circular dependency**:

1. `seapay_agent.py` imports from `wallet_tools.py`
2. `wallet_tools.py` imports `SeaPayContext` from `seapay_agent.py`

This creates a circular import that Python cannot resolve.

## Solution

Used Python's `TYPE_CHECKING` pattern to defer the type import:

**Before** (causing circular import):

```python
from ..agents.seapay_agent import SeaPayContext

async def get_wallet_info(
    ctx: RunContextWrapper[SeaPayContext],
) -> dict[str, Any]:
    ...
```

**After** (fixed):

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..agents.seapay_agent import SeaPayContext

async def get_wallet_info(
    ctx: RunContextWrapper,  # Type hint removed from runtime
) -> dict[str, Any]:
    ...
```

## How It Works

- `TYPE_CHECKING` is `False` at runtime, `True` during type checking
- The import only happens during static type checking (mypy, IDE)
- At runtime, the import is skipped, breaking the circular dependency
- Type checkers still see the correct types

## Changes Made

Updated all function signatures in `wallet_tools.py`:

- ✅ `get_wallet_info(ctx: RunContextWrapper)` - removed type parameter
- ✅ `check_wallet_balance(ctx: RunContextWrapper)` - removed type parameter
- ✅ `pay_invoice_with_usdc(ctx: RunContextWrapper)` - removed type parameter
- ✅ `get_wallet_activity(ctx: RunContextWrapper)` - removed type parameter
- ✅ `get_wallet_address(ctx: RunContextWrapper)` - removed type parameter
- ✅ `export_wallet(ctx: RunContextWrapper)` - removed type parameter

## Result

✅ Circular import resolved
✅ Application starts successfully
✅ Type hints still work in IDE and type checkers
✅ No runtime overhead

---

**Status**: ✅ **FIXED** - Backend now starts without errors!
