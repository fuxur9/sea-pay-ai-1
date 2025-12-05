"""
Wallet management tools for SeaPay agent.

This module provides function tools that agents can use to interact with
the wallet manager for balance checking, transfers, and wallet information.
"""

import logging
from typing import Any, TYPE_CHECKING

from agents import RunContextWrapper, function_tool

from .wallet_config import get_wallet_manager

if TYPE_CHECKING:
    from ..agents.seapay_agent import SeaPayContext

logger = logging.getLogger(__name__)


@function_tool(
    description_override=(
        "Get comprehensive wallet information including address, network, and balances. "
        "Use this to check the wallet address and USDC/gas balances before making on-chain payments. "
        "Returns wallet address, network (base-sepolia or base-mainnet), USDC balance, ETH balance, "
        "and whether gasless USDC transfers are enabled."
    )
)
async def get_wallet_info(
    ctx: RunContextWrapper,
) -> dict[str, Any]:
    """
    Get comprehensive wallet information.
    
    Returns wallet address, network, USDC balance, ETH balance, and gasless status.
    Use this tool before making payments to verify sufficient balance.
    
    Returns:
        dict: Wallet information with address, network, balances, and gasless status
    """
    logger.info("[TOOL CALL] get_wallet_info")
    
    try:
        wallet_manager = get_wallet_manager()
        wallet_info = await wallet_manager.get_wallet_info()
        
        return wallet_info
    except Exception as e:
        logger.error(f"[ERROR] get_wallet_info failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to get wallet information: {str(e)}",
        }


@function_tool(
    description_override=(
        "Check the current balance of USDC (or other assets) in the wallet. "
        "Returns balance in human-readable format. "
        "Use this to verify sufficient funds before making payments."
    )
)
async def check_wallet_balance(
    ctx: RunContextWrapper,
    asset_id: str = "usdc",
) -> dict[str, Any]:
    """
    Check the current balance of USDC (or other assets) in the wallet.
    
    Args:
        asset_id: The asset to check balance for (default: "usdc")
        
    Returns:
        dict: Balance information with asset_id, balance, and formatted_balance
    """
    logger.info(f"[TOOL CALL] check_wallet_balance: {asset_id}")
    
    try:
        wallet_manager = get_wallet_manager()
        balance_info = await wallet_manager.get_balance(asset_id)
        wallet_address = wallet_manager.get_wallet_address()
        
        # Format response for user
        message = (
            f"Wallet Balance:\n"
            f"Address: {wallet_address}\n"
            f"Balance: {balance_info['formatted_balance']}"
        )
        
        return {
            **balance_info,
            "wallet_address": wallet_address,
            "message": message,
        }
    except Exception as e:
        logger.error(f"[ERROR] check_wallet_balance failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "asset_id": asset_id,
            "message": f"Failed to check balance: {str(e)}",
        }


@function_tool(
    description_override=(
        "Pay an invoice using USDC transfer. "
        "Converts human USDC amount to correct decimal integer using AgentKit. "
        "Uses AgentKit wallet transfer API with gasless=True for Base network. "
        "Waits for confirmation, then returns transaction hash, amount, currency, network, and status. "
        "This tool requires explicit user approval before execution."
    )
)
async def pay_invoice_with_usdc(
    ctx: RunContextWrapper,
    amount_usdc: float,
    destination_address: str,
    memo: str | None = None,
    network: str = "base-sepolia",
) -> dict[str, Any]:
    """
    Pay an invoice using USDC transfer.
    
    This is the core payment tool for USDC transfers. It uses AgentKit to:
    1. Convert the USDC amount to the correct decimal format
    2. Transfer USDC to the destination address (gasless on Base)
    3. Wait for transaction confirmation
    4. Return transaction details
    
    Args:
        amount_usdc: Amount of USDC to transfer (e.g., 0.02 for $0.02)
        destination_address: Recipient wallet address
        memo: Optional memo/description for the payment
        network: Network to use (default: base-sepolia)
        
    Returns:
        dict: Payment result with transaction hash and details
    """
    logger.info(
        f"[TOOL CALL] pay_invoice_with_usdc: {amount_usdc} USDC to {destination_address} "
        f"(memo: {memo})"
    )
    
    try:
        wallet_manager = get_wallet_manager()
        
        # Validate network matches configured network
        configured_network = wallet_manager.get_network_id()
        if network != configured_network:
            logger.warning(
                f"[WALLET] Network mismatch: requested {network}, "
                f"configured {configured_network}. Using configured network."
            )
            network = configured_network
        
        # Check balance before transfer
        balance_info = await wallet_manager.get_balance("usdc")
        current_balance = balance_info.get("balance", 0)
        
        if current_balance < amount_usdc:
            return {
                "success": False,
                "error": "Insufficient balance",
                "current_balance": current_balance,
                "required_amount": amount_usdc,
                "message": (
                    f"Insufficient USDC balance. "
                    f"Current balance: {current_balance:.6f} USDC, "
                    f"Required: {amount_usdc:.6f} USDC"
                ),
            }
        
        # Perform the transfer
        transfer_result = await wallet_manager.transfer_usdc(
            destination_address=destination_address,
            amount_usdc=amount_usdc,
            memo=memo,
            gasless=True,  # Use gasless transfers on Base
        )
        
        return transfer_result
    except Exception as e:
        logger.error(f"[ERROR] pay_invoice_with_usdc failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "amount": amount_usdc,
            "destination": destination_address,
            "message": f"Payment failed: {str(e)}",
        }


@function_tool(
    description_override=(
        "Get recent transaction history for the wallet. "
        "Returns USDC transfers with amount, counterparty, transaction hash, timestamp, and status. "
        "Useful for debugging and for the agent to explain what it did."
    )
)
async def get_wallet_activity(
    ctx: RunContextWrapper,
    limit: int = 10,
) -> dict[str, Any]:
    """
    Get recent transaction history for the wallet.
    
    Args:
        limit: Maximum number of transactions to return (default: 10)
        
    Returns:
        dict: Transaction history with list of recent transactions
    """
    logger.info(f"[TOOL CALL] get_wallet_activity: limit={limit}")
    
    try:
        wallet_manager = get_wallet_manager()
        history = await wallet_manager.get_transaction_history(limit)
        
        return history
    except Exception as e:
        logger.error(f"[ERROR] get_wallet_activity failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "transactions": [],
            "message": f"Failed to get transaction history: {str(e)}",
        }


@function_tool(
    description_override=(
        "Get the wallet address. "
        "Returns the current wallet address for receiving payments."
    )
)
async def get_wallet_address(
    ctx: RunContextWrapper,
) -> dict[str, Any]:
    """
    Get the current wallet address.
    
    Returns:
        dict: Wallet address information
    """
    logger.info("[TOOL CALL] get_wallet_address")
    
    try:
        wallet_manager = get_wallet_manager()
        address = wallet_manager.get_wallet_address()
        
        return {
            "success": True,
            "address": address,
            "message": f"Wallet address: {address}",
        }
    except Exception as e:
        logger.error(f"[ERROR] get_wallet_address failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to get wallet address: {str(e)}",
        }


@function_tool(
    description_override=(
        "Export wallet data (seed phrase) for backup. "
        "WARNING: This reveals sensitive information. Requires user approval."
    )
)
async def export_wallet(
    ctx: RunContextWrapper,
) -> dict[str, Any]:
    """
    Export wallet data for backup.
    
    WARNING: This exposes sensitive wallet information. Use with extreme caution.
    
    Returns:
        dict: Wallet backup data
    """
    logger.info("[TOOL CALL] export_wallet")
    
    try:
        wallet_manager = get_wallet_manager()
        export_data = wallet_manager.export_wallet_data()
        
        return export_data
    except Exception as e:
        logger.error(f"[ERROR] export_wallet failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to export wallet: {str(e)}",
        }
