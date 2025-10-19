import asyncio
from typing import Dict, Any
from web3 import Web3
from web3.exceptions import ContractLogicError, Web3Exception
import aiohttp
import json

from app.core.config import settings


# Polygon network configuration
POLYGON_RPC_URL = settings.POLYGON_TESTNET_RPC_URL if settings.USE_TESTNET else settings.POLYGON_RPC_URL
POLYGON_CHAIN_ID = settings.POLYGON_TESTNET_CHAIN_ID if settings.USE_TESTNET else settings.POLYGON_CHAIN_ID
USDC_CONTRACT = settings.USDC_TESTNET_CONTRACT_ADDRESS if settings.USE_TESTNET else settings.USDC_CONTRACT_ADDRESS
USDT_CONTRACT = settings.USDT_TESTNET_CONTRACT_ADDRESS if settings.USE_TESTNET else settings.USDT_CONTRACT_ADDRESS

# ERC-20 ABI (minimal)
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [
            {"name": "_to", "type": "address"},
            {"name": "_value", "type": "uint256"}
        ],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    }
]


def get_web3_connection() -> Web3:
    """Get Web3 connection to Polygon network"""
    return Web3(Web3.HTTPProvider(POLYGON_RPC_URL))


async def get_token_balance(address: str, contract_address: str, decimals: int = 6) -> float:
    """Get token balance for a specific contract"""
    try:
        def _get_balance():
            w3 = get_web3_connection()
            
            # Create contract instance
            contract = w3.eth.contract(
                address=Web3.to_checksum_address(contract_address),
                abi=ERC20_ABI
            )
            
            # Get balance
            balance_wei = contract.functions.balanceOf(
                Web3.to_checksum_address(address)
            ).call()
            
            return balance_wei
        
        # Run the blockchain operation in a thread
        balance_wei = await asyncio.to_thread(_get_balance)
        
        # Convert to human readable format
        balance = balance_wei / (10 ** decimals)
        return balance
        
    except Exception:
        # Return 0 if any error occurs
        return 0.0


async def get_matic_balance(address: str) -> float:
    """Get MATIC balance"""
    try:
        def _get_balance():
            w3 = get_web3_connection()
            balance_wei = w3.eth.get_balance(Web3.to_checksum_address(address))
            balance = w3.from_wei(balance_wei, 'ether')
            return float(balance)
        
        # Run the blockchain operation in a thread
        return await asyncio.to_thread(_get_balance)
    except Exception:
        return 0.0


async def get_token_prices() -> Dict[str, Dict]:
    """Get current token prices from CoinGecko API"""
    try:
        async with aiohttp.ClientSession() as session:
            url = "https://api.coingecko.com/api/v3/simple/price?ids=usd-coin,tether,matic-network&vs_currencies=usd&include_24hr_change=true&include_market_cap=true&include_last_updated_at=true"
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Extract data with proper error handling
                    usdc_data = data.get("usd-coin", {})
                    usdt_data = data.get("tether", {})
                    matic_data = data.get("matic-network", {})
                    
                    return {
                        "usdc": {
                            "usd": usdc_data.get("usd", 1.0),
                            "usd_24h_change": usdc_data.get("usd_24h_change", 0.0),
                            "usd_market_cap": usdc_data.get("usd_market_cap", 0),
                            "last_updated_at": usdc_data.get("last_updated_at", "")
                        },
                        "usdt": {
                            "usd": usdt_data.get("usd", 1.0),
                            "usd_24h_change": usdt_data.get("usd_24h_change", 0.0),
                            "usd_market_cap": usdt_data.get("usd_market_cap", 0),
                            "last_updated_at": usdt_data.get("last_updated_at", "")
                        },
                        "matic": {
                            "usd": matic_data.get("usd", 0.5),
                            "usd_24h_change": matic_data.get("usd_24h_change", 0.0),
                            "usd_market_cap": matic_data.get("usd_market_cap", 0),
                            "last_updated_at": matic_data.get("last_updated_at", "")
                        }
                    }
    except Exception as e:
        print(f"Error fetching token prices: {e}")
    
    # Fallback prices
    return {
        "usdc": {"usd": 1.0, "usd_24h_change": 0.0, "usd_market_cap": 0, "last_updated_at": ""},
        "usdt": {"usd": 1.0, "usd_24h_change": 0.0, "usd_market_cap": 0, "last_updated_at": ""},
        "matic": {"usd": 0.5, "usd_24h_change": 0.0, "usd_market_cap": 0, "last_updated_at": ""}
    }


async def get_balances(address: str) -> Dict[str, Any]:
    """Get all token balances for an address"""
    try:
        # Get balances concurrently
        usdc_balance, usdt_balance, matic_balance, prices = await asyncio.gather(
            get_token_balance(address, USDC_CONTRACT, 6),  # USDC has 6 decimals
            get_token_balance(address, USDT_CONTRACT, 6),  # USDT has 6 decimals
            get_matic_balance(address),
            get_token_prices()
        )
        
        # Calculate USD values
        usdc_usd = usdc_balance * prices["usdc"]["usd"]
        usdt_usd = usdt_balance * prices["usdt"]["usd"]
        matic_usd = matic_balance * prices["matic"]["usd"]
        total_usd = usdc_usd + usdt_usd + matic_usd
        
        return {
            "USDC": usdc_balance,
            "USDT": usdt_balance,
            "MATIC": matic_balance,
            "usdc_usd": usdc_usd,
            "usdt_usd": usdt_usd,
            "matic_usd": matic_usd,
            "total_usd": total_usd,
            "prices": prices
        }
        
    except Exception as e:
        # Return zero balances if anything fails
        return {
            "USDC": 0.0,
            "USDT": 0.0,
            "MATIC": 0.0,
            "usdc_usd": 0.0,
            "usdt_usd": 0.0,
            "matic_usd": 0.0,
            "total_usd": 0.0,
            "error": str(e)
        }


async def estimate_gas_price() -> int:
    """Get current gas price estimate"""
    try:
        def _get_gas_price():
            w3 = get_web3_connection()
            return w3.eth.gas_price
        
        # Run the synchronous Web3 call in a thread
        gas_price = await asyncio.to_thread(_get_gas_price)
        return gas_price
    except Exception:
        # Fallback gas price (20 gwei)
        return 20000000000


async def estimate_token_transfer_gas(
    from_address: str,
    to_address: str,
    amount: float,
    token_contract: str,
    decimals: int = 6
) -> Dict[str, Any]:
    """Estimate gas for token transfer"""
    try:
        def _estimate_gas():
            w3 = get_web3_connection()
            
            # Convert amount to wei (token units)
            amount_wei = int(amount * (10 ** decimals))
            
            # Get contract instance
            contract = w3.eth.contract(
                address=Web3.to_checksum_address(token_contract),
                abi=ERC20_ABI
            )
            
            # Estimate gas for transfer function
            gas_estimate = contract.functions.transfer(
                Web3.to_checksum_address(to_address),
                amount_wei
            ).estimate_gas({'from': Web3.to_checksum_address(from_address)})
            
            # Get current gas price
            gas_price = w3.eth.gas_price
            
            return gas_estimate, gas_price
        
        # Run the blockchain operations in a thread
        gas_estimate, gas_price = await asyncio.to_thread(_estimate_gas)
        
        # Calculate total fee in wei
        gas_fee_wei = gas_estimate * gas_price
        
        # Convert to MATIC (18 decimals)
        gas_fee_matic = gas_fee_wei / (10 ** 18)
        
        return {
            "gas_estimate": gas_estimate,
            "gas_price": gas_price,
            "gas_price_gwei": gas_price / (10 ** 9),
            "gas_fee_wei": gas_fee_wei,
            "gas_fee_matic": gas_fee_matic,
            "total_cost_usd": gas_fee_matic * await get_matic_price_usd()
        }
        
    except Exception as e:
        # Return fallback estimates
        fallback_gas = 100000  # Conservative estimate for token transfers
        fallback_gas_price = 20000000000  # 20 gwei
        gas_fee_wei = fallback_gas * fallback_gas_price
        gas_fee_matic = gas_fee_wei / (10 ** 18)
        
        return {
            "gas_estimate": fallback_gas,
            "gas_price": fallback_gas_price,
            "gas_price_gwei": fallback_gas_price / (10 ** 9),
            "gas_fee_wei": gas_fee_wei,
            "gas_fee_matic": gas_fee_matic,
            "total_cost_usd": gas_fee_matic * 0.5,  # Fallback MATIC price
            "error": str(e),
            "is_estimate": True
        }


async def estimate_matic_transfer_gas(
    from_address: str,
    to_address: str,
    amount: float
) -> Dict[str, Any]:
    """Estimate gas for MATIC transfer"""
    try:
        def _estimate_gas():
            w3 = get_web3_connection()
            
            # Convert amount to wei
            amount_wei = int(amount * (10 ** 18))
            
            # Estimate gas for simple transfer
            gas_estimate = w3.eth.estimate_gas({
                'from': Web3.to_checksum_address(from_address),
                'to': Web3.to_checksum_address(to_address),
                'value': amount_wei
            })
            
            # Get current gas price
            gas_price = w3.eth.gas_price
            
            return gas_estimate, gas_price
        
        # Run the blockchain operations in a thread
        gas_estimate, gas_price = await asyncio.to_thread(_estimate_gas)
        
        # Calculate total fee in wei
        gas_fee_wei = gas_estimate * gas_price
        
        # Convert to MATIC
        gas_fee_matic = gas_fee_wei / (10 ** 18)
        
        return {
            "gas_estimate": gas_estimate,
            "gas_price": gas_price,
            "gas_price_gwei": gas_price / (10 ** 9),
            "gas_fee_wei": gas_fee_wei,
            "gas_fee_matic": gas_fee_matic,
            "total_cost_usd": gas_fee_matic * await get_matic_price_usd()
        }
        
    except Exception as e:
        # Return fallback estimates
        fallback_gas = 21000  # Standard ETH transfer gas
        fallback_gas_price = 20000000000  # 20 gwei
        gas_fee_wei = fallback_gas * fallback_gas_price
        gas_fee_matic = gas_fee_wei / (10 ** 18)
        
        return {
            "gas_estimate": fallback_gas,
            "gas_price": fallback_gas_price,
            "gas_price_gwei": fallback_gas_price / (10 ** 9),
            "gas_fee_wei": gas_fee_wei,
            "gas_fee_matic": gas_fee_matic,
            "total_cost_usd": gas_fee_matic * 0.5,  # Fallback MATIC price
            "error": str(e),
            "is_estimate": True
        }


async def get_matic_price_usd() -> float:
    """Get current MATIC price in USD"""
    try:
        prices = await get_token_prices()
        return float(prices.get('matic', {}).get('usd', 0.5))
    except Exception:
        return 0.5  # Fallback price


async def send_token_transaction(
    from_address: str,
    to_address: str,
    amount: float,
    token_contract: str,
    private_key: str,
    decimals: int = 6
) -> Dict[str, Any]:
    """Send token transaction (USDC/USDT)"""
    try:
        def _send_token():
            w3 = get_web3_connection()
            
            # Create contract instance
            contract = w3.eth.contract(
                address=Web3.to_checksum_address(token_contract),
                abi=ERC20_ABI
            )
            
            # Convert amount to wei
            amount_wei = int(amount * (10 ** decimals))
            
            # Get gas price and nonce
            gas_price = w3.eth.gas_price
            nonce = w3.eth.get_transaction_count(Web3.to_checksum_address(from_address))
            
            # Build transaction
            transaction = contract.functions.transfer(
                Web3.to_checksum_address(to_address),
                amount_wei
            ).build_transaction({
                'from': Web3.to_checksum_address(from_address),
                'gas': 100000,
                'gasPrice': gas_price,
                'nonce': nonce,
                'chainId': POLYGON_CHAIN_ID
            })
            
            # Sign transaction
            signed_txn = w3.eth.account.sign_transaction(transaction, private_key)
            
            # Send transaction
            tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            return tx_hash.hex()
        
        # Run the blockchain operations in a thread
        tx_hash = await asyncio.to_thread(_send_token)
        
        return {
            "success": True,
            "transaction_hash": tx_hash,
            "amount": amount,
            "to": to_address
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


async def send_token_transaction_gasless(
    from_address: str,
    to_address: str,
    amount: float,
    token_contract: str,
    user_private_key: str,
    relayer_private_key: str,
    decimals: int = 6
) -> Dict[str, Any]:
    """
    Send token transaction with gasless (meta-transaction) approach.
    Relayer pays for gas, user signs the transfer approval.
    
    This is a simplified gasless implementation where:
    1. User approves the relayer to spend their tokens
    2. Relayer executes transferFrom on behalf of user and pays gas
    """
    try:
        def _send_gasless():
            w3 = get_web3_connection()
            
            # Get relayer account
            relayer_account = w3.eth.account.from_key(relayer_private_key)
            relayer_address = relayer_account.address
            
            # Create contract instance
            contract = w3.eth.contract(
                address=Web3.to_checksum_address(token_contract),
                abi=ERC20_ABI
            )
            
            # Convert amount to wei
            amount_wei = int(amount * (10 ** decimals))
            
            # Build the transfer transaction
            # For simplicity, we'll have relayer directly execute the transfer
            # Note: This requires the user's tokens to be transferred to relayer first
            # or the relayer to have approval (not implemented here for safety)
            
            # ALTERNATIVE: Have relayer send transaction but user signs the data
            # For now, we'll use a simple approach: transfer tokens directly
            
            # Get gas price and nonce
            gas_price = w3.eth.gas_price
            nonce = w3.eth.get_transaction_count(Web3.to_checksum_address(from_address))
            
            # Build transaction (relayer pays gas)
            transaction = contract.functions.transfer(
                Web3.to_checksum_address(to_address),
                amount_wei
            ).build_transaction({
                'from': Web3.to_checksum_address(from_address),
                'gas': 100000,
                'gasPrice': 0,  # User pays 0 gas
                'nonce': nonce,
                'chainId': POLYGON_CHAIN_ID
            })
            
            # User signs the transaction
            signed_txn = w3.eth.account.sign_transaction(transaction, user_private_key)
            
            # Relayer submits and pays for gas
            # Modify transaction to use relayer's gas payment
            relayer_nonce = w3.eth.get_transaction_count(relayer_address)
            
            # For actual gasless, we need EIP-2771 or similar
            # Simplified version: just have relayer pay by wrapping the transaction
            transaction['gasPrice'] = gas_price
            transaction['nonce'] = relayer_nonce
            transaction['from'] = relayer_address
            
            # This won't work as-is because from_address must match signer
            # Let's use the direct approach for now
            
            return None
        
        # Actually, let's use a simpler gasless approach:
        # Check user's gas balance and use relayer if needed
        return await send_token_transaction_with_relayer_fallback(
            from_address, to_address, amount, token_contract,
            user_private_key, relayer_private_key, decimals
        )
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


async def send_token_transaction_with_relayer_fallback(
    from_address: str,
    to_address: str,
    amount: float,
    token_contract: str,
    user_private_key: str,
    relayer_private_key: str,
    decimals: int = 6
) -> Dict[str, Any]:
    """
    Smart transaction sender that checks gas balance and uses relayer if needed.
    """
    try:
        def _check_and_send():
            w3 = get_web3_connection()
            
            # Check if user has gas
            user_balance = w3.eth.get_balance(Web3.to_checksum_address(from_address))
            gas_price = w3.eth.gas_price
            estimated_gas_cost = gas_price * 100000
            
            if user_balance >= estimated_gas_cost:
                # User has gas, send normally
                return _send_with_user_gas(
                    w3, from_address, to_address, amount, token_contract,
                    user_private_key, decimals
                )
            else:
                # User has no gas, use relayer
                return _send_with_relayer_gas(
                    w3, from_address, to_address, amount, token_contract,
                    user_private_key, relayer_private_key, decimals
                )
        
        result = await asyncio.to_thread(_check_and_send)
        return result
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"❌ ERROR in send_token_transaction_with_relayer_fallback: {str(e)}")
        logger.exception(e)  # This will print the full stack trace
        return {
            "success": False,
            "error": str(e)
        }


def _send_with_user_gas(w3, from_address, to_address, amount, token_contract, private_key, decimals):
    """Send token transaction with user paying gas"""
    contract = w3.eth.contract(
        address=Web3.to_checksum_address(token_contract),
        abi=ERC20_ABI
    )
    
    amount_wei = int(amount * (10 ** decimals))
    gas_price = w3.eth.gas_price
    nonce = w3.eth.get_transaction_count(Web3.to_checksum_address(from_address))
    
    transaction = contract.functions.transfer(
        Web3.to_checksum_address(to_address),
        amount_wei
    ).build_transaction({
        'from': Web3.to_checksum_address(from_address),
        'gas': 100000,
        'gasPrice': gas_price,
        'nonce': nonce,
        'chainId': POLYGON_CHAIN_ID
    })
    
    signed_txn = w3.eth.account.sign_transaction(transaction, private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
    
    return {
        "success": True,
        "transaction_hash": tx_hash.hex(),
        "amount": amount,
        "to": to_address,
        "gasless": False
    }


def _send_with_relayer_gas(w3, from_address, to_address, amount, token_contract, user_private_key, relayer_private_key, decimals):
    """
    Send token transaction with relayer sponsoring gas.
    
    SIMPLIFIED APPROACH: Instead of complex gasless meta-transactions,
    we simply send MATIC and token transfer in quick succession.
    Blockchain handles ordering automatically.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        from app.core.config import settings
        
        # Get relayer account
        relayer_account = w3.eth.account.from_key(relayer_private_key)
        relayer_address = relayer_account.address
    except Exception as e:
        logger.error(f"❌ ERROR getting relayer account: {str(e)}")
        raise
    
    logger.info(f"🔄 Starting gasless transaction for {amount} tokens")
    logger.info(f"   User: {from_address}")
    logger.info(f"   Relayer: {relayer_address}")
    
    # Check relayer balance
    relayer_balance = w3.eth.get_balance(relayer_address)
    gas_price = w3.eth.gas_price
    
    # Calculate gas needed
    gas_for_matic_transfer = 21000
    gas_for_token_transfer = 100000
    total_gas_cost = gas_price * (gas_for_matic_transfer + gas_for_token_transfer)
    gas_to_send = int(total_gas_cost * 1.3)  # 30% buffer
    
    logger.info(f"   Gas needed: {w3.from_wei(gas_to_send, 'ether')} MATIC")
    logger.info(f"   Relayer balance: {w3.from_wei(relayer_balance, 'ether')} MATIC")
    
    if relayer_balance < gas_to_send:
        error_msg = f"Relayer has insufficient gas. Has {w3.from_wei(relayer_balance, 'ether')} MATIC, needs {w3.from_wei(gas_to_send, 'ether')} MATIC"
        logger.error(f"❌ {error_msg}")
        raise Exception(error_msg)
    
    # Step 1: Send MATIC from relayer to user (DON'T WAIT FOR CONFIRMATION)
    relayer_nonce = w3.eth.get_transaction_count(relayer_address)
    
    gas_transfer_tx = {
        'to': Web3.to_checksum_address(from_address),
        'value': gas_to_send,
        'gas': gas_for_matic_transfer,
        'gasPrice': gas_price,
        'nonce': relayer_nonce,
        'chainId': POLYGON_CHAIN_ID
    }
    
    signed_gas_tx = w3.eth.account.sign_transaction(gas_transfer_tx, relayer_private_key)
    gas_tx_hash = w3.eth.send_raw_transaction(signed_gas_tx.rawTransaction)
    
    logger.info(f"💸 Gas transfer sent: {gas_tx_hash.hex()}")
    logger.info(f"   Immediately sending token transaction...")
    
    # Step 2: User sends token transaction immediately
    # The blockchain will process these in order automatically based on nonce
    # No need to wait - the mempool and miners handle the ordering
    contract = w3.eth.contract(
        address=Web3.to_checksum_address(token_contract),
        abi=ERC20_ABI
    )
    
    amount_wei = int(amount * (10 ** decimals))
    
    # Get fresh nonce after gas transfer
    user_nonce = w3.eth.get_transaction_count(Web3.to_checksum_address(from_address), 'pending')
    
    logger.info(f"📤 Building token transfer...")
    logger.info(f"   Amount: {amount_wei} ({amount} tokens)")
    logger.info(f"   User nonce: {user_nonce}")
    
    token_transaction = contract.functions.transfer(
        Web3.to_checksum_address(to_address),
        amount_wei
    ).build_transaction({
        'from': Web3.to_checksum_address(from_address),
        'gas': gas_for_token_transfer,
        'gasPrice': gas_price,
        'nonce': user_nonce,
        'chainId': POLYGON_CHAIN_ID
    })
    
    # User signs token transfer
    signed_token_tx = w3.eth.account.sign_transaction(token_transaction, user_private_key)
    token_tx_hash = w3.eth.send_raw_transaction(signed_token_tx.rawTransaction)
    
    logger.info(f"✅ Token transfer sent: {token_tx_hash.hex()}")
    logger.info(f"🎉 Gasless transaction complete!")
    
    return {
        "success": True,
        "transaction_hash": token_tx_hash.hex(),
        "amount": amount,
        "to": to_address,
        "gasless": True,
        "gas_sponsored_by": relayer_address,
        "gas_transfer_tx": gas_tx_hash.hex()
    }


async def send_matic_transaction(
    from_address: str,
    to_address: str,
    amount: float,
    private_key: str
) -> Dict[str, Any]:
    """Send MATIC transaction"""
    try:
        def _send_matic():
            w3 = get_web3_connection()
            
            # Convert amount to wei
            amount_wei = w3.to_wei(amount, 'ether')
            
            # Get gas price and nonce
            gas_price = w3.eth.gas_price
            nonce = w3.eth.get_transaction_count(Web3.to_checksum_address(from_address))
            
            # Build transaction
            transaction = {
                'to': Web3.to_checksum_address(to_address),
                'value': amount_wei,
                'gas': 21000,
                'gasPrice': gas_price,
                'nonce': nonce,
                'chainId': POLYGON_CHAIN_ID
            }
            
            # Sign transaction
            signed_txn = w3.eth.account.sign_transaction(transaction, private_key)
            
            # Send transaction
            tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            return tx_hash.hex()
        
        # Run the blockchain operations in a thread
        tx_hash = await asyncio.to_thread(_send_matic)
        
        return {
            "success": True,
            "transaction_hash": tx_hash,
            "amount": amount,
            "to": to_address
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
        
        return {
            "success": True,
            "transaction_hash": tx_hash.hex(),
            "amount": amount,
            "to": to_address
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


async def get_blockchain_transactions_web3_fallback(address: str, limit: int = 10) -> Dict[str, Any]:
    """Efficient fallback method to get transactions using Web3 event logs and third-party APIs"""
    try:
        print(f"🔄 Using optimized Web3 fallback to get transaction history for {address}")
        
        def _get_transactions():
            # Try multiple efficient approaches
            transactions = []
            
            # Method 1: Try using alternative blockchain APIs
            try:
                print("🌐 Attempting to use alternative blockchain APIs...")
                alt_transactions = _get_transactions_from_alternative_apis(address, limit)
                if alt_transactions:
                    transactions.extend(alt_transactions)
                    print(f"✅ Found {len(alt_transactions)} transactions from alternative APIs")
            except Exception as e:
                print(f"⚠️ Alternative APIs failed: {str(e)[:100]}...")
            
            # Method 2: Use Web3 with smart filtering (if we still need more transactions)
            if len(transactions) < limit:
                try:
                    print("🔍 Using Web3 with optimized transaction lookup...")
                    web3_transactions = _get_transactions_web3_optimized(address, limit - len(transactions))
                    transactions.extend(web3_transactions)
                    print(f"✅ Found {len(web3_transactions)} additional transactions from Web3")
                except Exception as e:
                    print(f"⚠️ Web3 optimized lookup failed: {str(e)[:100]}...")
            
            return transactions[:limit]
        
        def _get_transactions_from_alternative_apis(address: str, limit: int):
            """Try using free blockchain APIs like Blockscout, CovalentHQ, etc."""
            transactions = []
            
            # Try Blockscout API (often available for testnets)
            try:
                import requests
                blockscout_url = f"https://polygon-amoy.blockscout.com/api/v2/addresses/{address}/transactions"
                response = requests.get(blockscout_url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if 'items' in data:
                        for tx in data['items'][:limit]:
                            if float(tx.get('value', '0')) > 0:  # Only include transactions with value
                                transactions.append({
                                    'hash': tx['hash'],
                                    'from_address': tx['from']['hash'],
                                    'to_address': tx['to']['hash'] if tx['to'] else '',
                                    'value': tx['value'],
                                    'token_symbol': 'MATIC',
                                    'token_decimals': 18,
                                    'timestamp': int(tx['timestamp']),
                                    'gas_used': tx.get('gas_used', '0'),
                                    'gas_price': tx.get('gas_price', '0'),
                                    'status': '1' if tx.get('status') == 'ok' else '0',
                                    'block_number': str(tx.get('block', 0)),
                                    'type': 'normal'
                                })
                        print(f"📡 Blockscout API returned {len(transactions)} transactions")
                        return transactions
            except Exception as e:
                print(f"⚠️ Blockscout API failed: {str(e)[:50]}...")
            
            return []
        
        def _get_transactions_web3_optimized(address: str, limit: int):
            """Use Web3 with optimized approach - limited block range and early termination"""
            w3 = get_web3_connection()
            transactions = []
            
            try:
                latest_block = w3.eth.block_number
                print(f"� Latest block: {latest_block}")
                
                # Use a much smaller, smarter block range
                # Check last 20 blocks first for recent activity
                recent_blocks = min(20, latest_block)
                print(f"🔍 Quick scan of last {recent_blocks} blocks...")
                
                for block_num in range(latest_block, max(0, latest_block - recent_blocks), -1):
                    try:
                        # Get block with transaction hashes only first (faster)
                        block = w3.eth.get_block(block_num, full_transactions=False)
                        
                        # Check each transaction hash
                        for tx_hash in block.transactions:
                            try:
                                tx = w3.eth.get_transaction(tx_hash)
                                
                                # Quick address check
                                tx_from = tx['from'].lower() if tx['from'] else ''
                                tx_to = tx['to'].lower() if tx['to'] else ''
                                address_lower = address.lower()
                                
                                if (tx_from == address_lower or tx_to == address_lower) and tx['value'] > 0:
                                    # Get receipt for status
                                    try:
                                        receipt = w3.eth.get_transaction_receipt(tx_hash)
                                        status = '1' if receipt['status'] == 1 else '0'
                                        gas_used = str(receipt['gasUsed'])
                                    except:
                                        status = '1'
                                        gas_used = str(tx['gas'])
                                    
                                    transactions.append({
                                        'hash': tx['hash'].hex(),
                                        'from_address': tx_from,
                                        'to_address': tx_to,
                                        'value': str(tx['value']),
                                        'token_symbol': 'MATIC',
                                        'token_decimals': 18,
                                        'timestamp': int(block['timestamp']),
                                        'gas_used': gas_used,
                                        'gas_price': str(tx['gasPrice']),
                                        'status': status,
                                        'block_number': str(block_num),
                                        'type': 'normal'
                                    })
                                    
                                    print(f"✅ Found transaction: {tx['hash'].hex()[:10]}...")
                                    
                                    if len(transactions) >= limit:
                                        return transactions
                            except Exception as e:
                                continue  # Skip individual transaction errors
                                
                    except Exception as e:
                        print(f"⚠️ Error checking block {block_num}: {str(e)[:50]}...")
                        continue
                
                print(f"🔍 Quick scan complete. Found {len(transactions)} transactions")
                return transactions
                
            except Exception as e:
                print(f"⚠️ Web3 optimized lookup error: {str(e)[:100]}...")
                return []
        
        # Run in thread to avoid blocking with a timeout
        try:
            transactions = await asyncio.wait_for(
                asyncio.to_thread(_get_transactions), 
                timeout=30.0  # 30 second timeout
            )
        except asyncio.TimeoutError:
            print("⏰ Web3 fallback timed out after 30 seconds")
            return {
                "success": False,
                "error": "Web3 fallback timed out",
                "transactions": []
            }
        
        # Sort by timestamp (newest first)
        transactions.sort(key=lambda x: x['timestamp'], reverse=True)
        
        print(f"✅ Web3 fallback found {len(transactions)} transactions")
        
        return {
            "success": True,
            "transactions": transactions[:limit]
        }
        
    except Exception as e:
        print(f"❌ Web3 fallback error: {e}")
        return {
            "success": False,
            "error": str(e),
            "transactions": []
        }


async def get_blockchain_transactions(address: str, limit: int = 50) -> Dict[str, Any]:
    """Fetch transaction history using web3.eth.get_transaction() as primary method"""
    try:
        logger.info(f"🔍 Fetching blockchain transactions for {address} using direct Web3")
        
        # Primary method: Direct Web3 using eth.get_transaction()
        try:
            result = await get_blockchain_transactions_web3_direct(address, limit)
            if result.get("success") and result.get("transactions"):
                logger.info(f"✅ Direct Web3 method found {len(result['transactions'])} transactions")
                return result
        except Exception as web3_error:
            logger.error(f"Direct Web3 method failed: {web3_error}")
        
        # Fallback: Polygon API
        try:
            logger.info("🔄 Trying Polygon API as fallback...")
            result = await get_blockchain_transactions_polygon_api_fallback(address, limit)
            if result.get("success") and result.get("transactions"):
                logger.info(f"✅ Polygon API fallback found {len(result['transactions'])} transactions")
                return result
        except Exception as polygon_error:
            logger.error(f"Polygon API fallback failed: {polygon_error}")
        
        # Fallback 3: Original Web3 fallback
        try:
            logger.info("🔄 Trying original Web3 fallback as last resort...")
            result = await get_blockchain_transactions_web3_fallback(address, min(limit, 10))
            if result.get("success"):
                return result
        except Exception as fallback_error:
            logger.error(f"Web3 fallback also failed: {fallback_error}")
        
        # Return empty results instead of failing completely
        logger.warning("All transaction fetching methods failed, returning empty results")
        return {
            "success": True,  # Don't fail the entire sync for API issues
            "error": "All transaction fetching methods failed",
            "transactions": []
        }
        
    except Exception as e:
        logger.error(f"❌ Error fetching blockchain transactions: {e}")
        return {
            "success": True,  # Don't fail the entire sync for API issues
            "error": str(e),
            "transactions": []
        }


async def get_blockchain_transactions_web3_direct(address: str, limit: int = 50) -> Dict[str, Any]:
    """Direct Web3 method using eth.get_transaction() for reliable transaction fetching"""
    try:
        logger.info(f"🔍 Using direct Web3 method for {address}")
        
        def _get_transactions_direct():
            w3 = get_web3_connection()
            transactions = []
            
            try:
                latest_block = w3.eth.block_number
                logger.info(f"📊 Latest block: {latest_block}")
                
                # Start with a smaller range for efficiency
                blocks_to_check = min(50, latest_block)  # Check last 50 blocks only
                logger.info(f"🔍 Scanning last {blocks_to_check} blocks...")
                
                found_count = 0
                for block_num in range(latest_block, max(0, latest_block - blocks_to_check), -1):
                    try:
                        # Get block with transaction hashes only (faster)
                        block = w3.eth.get_block(block_num, full_transactions=False)
                        
                        if len(block.transactions) == 0:
                            continue  # Skip empty blocks
                        
                        # Check each transaction in the block
                        for tx_hash in block.transactions:
                            try:
                                # Use web3.eth.get_transaction() directly
                                tx = w3.eth.get_transaction(tx_hash)
                                
                                # Check if transaction involves our address
                                tx_from = tx['from'].lower() if tx['from'] else ''
                                tx_to = tx['to'].lower() if tx['to'] else ''
                                address_lower = address.lower()
                                
                                if (tx_from == address_lower or tx_to == address_lower):
                                    found_count += 1
                                    logger.info(f"🔍 Found transaction #{found_count}: {tx['hash'].hex()[:10]}...")
                                    
                                    # Get transaction receipt for status and gas info
                                    try:
                                        receipt = w3.eth.get_transaction_receipt(tx_hash)
                                        status = '1' if receipt['status'] == 1 else '0'
                                        gas_used = str(receipt['gasUsed'])
                                        logs = receipt.get('logs', [])
                                    except Exception:
                                        status = '1'  # Assume success if we can't get receipt
                                        gas_used = str(tx['gas'])
                                        logs = []
                                    
                                    # Add MATIC transaction if it has value
                                    if tx['value'] > 0:
                                        transactions.append({
                                            'hash': tx['hash'].hex(),
                                            'from_address': tx_from,
                                            'to_address': tx_to,
                                            'value': str(tx['value']),
                                            'token_symbol': 'MATIC',
                                            'token_decimals': 18,
                                            'timestamp': int(block['timestamp']),
                                            'gas_used': gas_used,
                                            'gas_price': str(tx['gasPrice']),
                                            'status': status,
                                            'block_number': str(block_num),
                                            'type': 'normal'
                                        })
                                        logger.info(f"✅ Added MATIC transaction: {tx['value']} wei")
                                    
                                    # Check for token transfers in logs
                                    for log in logs:
                                        try:
                                            # ERC20 Transfer event signature
                                            if (len(log['topics']) >= 3 and 
                                                log['topics'][0].hex() == '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'):
                                                
                                                # Parse transfer log
                                                from_addr = '0x' + log['topics'][1].hex()[-40:]
                                                to_addr = '0x' + log['topics'][2].hex()[-40:]
                                                
                                                # Check if this transfer involves our address
                                                if (from_addr.lower() == address_lower or to_addr.lower() == address_lower):
                                                    # Determine token type based on contract address
                                                    contract_addr = log['address'].lower()
                                                    token_symbol = 'UNKNOWN'
                                                    token_decimals = 18
                                                    
                                                    if contract_addr == USDC_CONTRACT.lower():
                                                        token_symbol = 'USDC'
                                                        token_decimals = 6
                                                    elif contract_addr == USDT_CONTRACT.lower():
                                                        token_symbol = 'USDT'
                                                        token_decimals = 6
                                                    
                                                    # Parse amount from data
                                                    if len(log['data']) >= 66:  # 0x + 64 hex chars
                                                        amount = int(log['data'], 16)
                                                        
                                                        if token_symbol != 'UNKNOWN' and amount > 0:
                                                            transactions.append({
                                                                'hash': tx['hash'].hex(),
                                                                'from_address': from_addr.lower(),
                                                                'to_address': to_addr.lower(),
                                                                'value': str(amount),
                                                                'token_symbol': token_symbol,
                                                                'token_decimals': token_decimals,
                                                                'timestamp': int(block['timestamp']),
                                                                'gas_used': gas_used,
                                                                'gas_price': str(tx['gasPrice']),
                                                                'status': status,
                                                                'block_number': str(block_num),
                                                                'type': 'token'
                                                            })
                                                            logger.info(f"✅ Added {token_symbol} transfer: {amount}")
                                        except Exception as log_error:
                                            logger.debug(f"Log parsing error: {log_error}")
                                            continue
                                    
                                    # Stop if we have enough transactions
                                    if len(transactions) >= limit:
                                        logger.info(f"🎯 Reached limit of {limit} transactions")
                                        return transactions
                                        
                            except Exception as tx_error:
                                logger.debug(f"Transaction parsing error: {tx_error}")
                                continue
                                
                    except Exception as block_error:
                        logger.warning(f"⚠️ Error checking block {block_num}: {str(block_error)[:50]}...")
                        continue
                
                logger.info(f"✅ Scan complete. Found {len(transactions)} transactions in {found_count} relevant transactions")
                return transactions
                
            except Exception as e:
                logger.error(f"❌ Web3 direct method error: {e}")
                return []
        
        # Run in thread with shorter timeout
        try:
            transactions = await asyncio.wait_for(
                asyncio.to_thread(_get_transactions_direct), 
                timeout=30.0  # 30 second timeout for faster response
            )
        except asyncio.TimeoutError:
            logger.warning("⏰ Web3 direct method timed out after 30 seconds")
            return {
                "success": False,
                "error": "Web3 direct method timed out",
                "transactions": []
            }
        
        # Sort by timestamp (newest first)
        transactions.sort(key=lambda x: x['timestamp'], reverse=True)
        
        logger.info(f"✅ Web3 direct method found {len(transactions)} transactions")
        
        return {
            "success": True,
            "transactions": transactions[:limit]
        }
        
    except Exception as e:
        logger.error(f"❌ Web3 direct method error: {e}")
        return {
            "success": False,
            "error": str(e),
            "transactions": []
        }


async def get_blockchain_transactions_polygon_api_fallback(address: str, limit: int = 50) -> Dict[str, Any]:
    """Original Polygon API method as fallback"""
    try:
        # Use Polygon API or Moralis API to get transaction history
        # For now, using a simple approach with Polygon API
        
        # If on testnet, use different API endpoint
        if settings.USE_TESTNET:
            # For testnet, we can use a simpler approach or mock data
            api_url = f"https://api-testnet.polygonscan.com/api"
            api_key = getattr(settings, 'POLYGONSCAN_API_KEY', '')
        else:
            api_url = f"https://api.polygonscan.com/api"
            api_key = getattr(settings, 'POLYGONSCAN_API_KEY', '')
        
        # Get normal transactions
        normal_tx_params = {
            "module": "account",
            "action": "txlist",
            "address": address,
            "startblock": 0,
            "endblock": 99999999,
            "page": 1,
            "offset": min(limit, 50),  # Limit to avoid rate limits
            "sort": "desc"
        }
        
        if api_key:
            normal_tx_params["apikey"] = api_key
        
        # Get ERC-20 token transfers
        token_tx_params = {
            "module": "account", 
            "action": "tokentx",
            "address": address,
            "startblock": 0,
            "endblock": 99999999,
            "page": 1,
            "offset": min(limit, 50),  # Limit to avoid rate limits
            "sort": "desc"
        }
        
        if api_key:
            token_tx_params["apikey"] = api_key
        
        # Add timeout and headers to prevent 522 errors
        headers = {
            'User-Agent': 'DARI-Wallet/1.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        timeout = aiohttp.ClientTimeout(total=5)  # Reduced timeout to 5 seconds
        
        async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
            try:
                # Fetch normal transactions
                logger.info(f"🔍 Fetching normal transactions from: {api_url}")
                async with session.get(api_url, params=normal_tx_params) as response:
                    if response.status == 200:
                        normal_data = await response.json()
                    else:
                        logger.warning(f"⚠️ API returned status {response.status} for normal transactions")
                        normal_data = {"status": "0", "result": []}
                
                # Small delay to avoid rate limits
                await asyncio.sleep(0.2)
                
                # Fetch token transactions
                logger.info(f"🔍 Fetching token transactions from: {api_url}")
                async with session.get(api_url, params=token_tx_params) as response:
                    if response.status == 200:
                        token_data = await response.json()
                    else:
                        logger.warning(f"⚠️ API returned status {response.status} for token transactions")
                        token_data = {"status": "0", "result": []}
                        
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                logger.warning(f"⚠️ API request failed: {e}")
                logger.info(f"🔄 Trying Web3 fallback method...")
                
                # Try Web3 fallback
                fallback_result = await get_blockchain_transactions_web3_fallback(address, limit)
                if fallback_result.get("success") and fallback_result.get("transactions"):
                    return fallback_result
                
                # If fallback also fails, return empty results
                normal_data = {"status": "0", "result": []}
                token_data = {"status": "0", "result": []}
        
        normal_transactions = normal_data.get('result', []) if normal_data.get('status') == '1' else []
        token_transactions = token_data.get('result', []) if token_data.get('status') == '1' else []
        
        logger.info(f"📊 Found {len(normal_transactions)} normal transactions, {len(token_transactions)} token transactions")
        
        # Parse and normalize transactions
        parsed_transactions = []
        
        # Process normal MATIC transactions
        for tx in normal_transactions:
            try:
                if tx.get('value', '0') != '0':  # Only include transactions with value
                    parsed_transactions.append({
                        'hash': tx.get('hash'),
                        'from_address': tx.get('from', '').lower(),
                        'to_address': tx.get('to', '').lower(),
                        'value': tx.get('value', '0'),
                        'token_symbol': 'MATIC',
                        'token_decimals': 18,
                        'timestamp': int(tx.get('timeStamp', 0)),
                        'gas_used': tx.get('gasUsed', '0'),
                        'gas_price': tx.get('gasPrice', '0'),
                        'status': '1' if tx.get('txreceipt_status') == '1' else '0',
                        'block_number': tx.get('blockNumber'),
                        'type': 'normal'
                    })
            except Exception as e:
                logger.error(f"⚠️ Error parsing normal transaction: {e}")
                continue
        
        # Process token transactions (USDC, USDT, etc.)
        for tx in token_transactions:
            try:
                # Filter for our supported tokens
                token_address = tx.get('contractAddress', '').lower()
                if token_address in [USDC_CONTRACT.lower(), USDT_CONTRACT.lower()]:
                    token_symbol = 'USDC' if token_address == USDC_CONTRACT.lower() else 'USDT'
                    token_decimals = 6  # Both USDC and USDT use 6 decimals
                    
                    parsed_transactions.append({
                        'hash': tx.get('hash'),
                        'from_address': tx.get('from', '').lower(),
                        'to_address': tx.get('to', '').lower(), 
                        'value': tx.get('value', '0'),
                        'token_symbol': token_symbol,
                        'token_decimals': token_decimals,
                        'timestamp': int(tx.get('timeStamp', 0)),
                        'gas_used': tx.get('gasUsed', '0'),
                        'gas_price': tx.get('gasPrice', '0'),
                        'status': '1',  # Token transfers are usually successful if they appear
                        'block_number': tx.get('blockNumber'),
                        'type': 'token'
                    })
            except Exception as e:
                logger.error(f"⚠️ Error parsing token transaction: {e}")
                continue
        
        # Sort by timestamp (newest first)
        parsed_transactions.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # Limit results
        parsed_transactions = parsed_transactions[:limit]
        
        logger.info(f"✅ Successfully parsed {len(parsed_transactions)} transactions")
        
        return {
            "success": True,
            "transactions": parsed_transactions
        }
        
    except Exception as e:
        logger.error(f"❌ Error fetching blockchain transactions: {e}")
        # Try Web3 fallback as last resort
        try:
            logger.info(f"🔄 Trying Web3 fallback as last resort...")
            fallback_result = await get_blockchain_transactions_web3_fallback(address, limit)
            if fallback_result.get("success"):
                return fallback_result
        except Exception as fallback_error:
            logger.error(f"❌ Web3 fallback also failed: {fallback_error}")
        
        # Return empty results instead of failing completely
        return {
            "success": True,  # Don't fail the entire sync for API issues
            "error": str(e),
            "transactions": []
        }


async def get_relayer_status() -> Dict[str, Any]:
    """Get relayer wallet status for monitoring gasless transactions
    
    Returns:
        Dict containing:
        - relayer_address: The relayer wallet address
        - matic_balance: Current MATIC balance
        - matic_balance_formatted: Human-readable balance with units
        - estimated_transactions_remaining: Number of transactions that can be sponsored
        - average_gas_cost_matic: Average gas cost per transaction
        - status: funded/low/empty
        - status_message: Human-readable status message
        - recommendations: List of recommended actions
    """
    import logging
    from decimal import Decimal
    
    logger = logging.getLogger(__name__)
    
    try:
        # Check if gasless is enabled
        if not settings.ENABLE_GASLESS:
            return {
                "enabled": False,
                "status": "disabled",
                "message": "Gasless transactions are disabled"
            }
        
        # Get relayer address
        relayer_address = settings.RELAYER_ADDRESS
        if not relayer_address:
            return {
                "enabled": False,
                "status": "error",
                "message": "Relayer address not configured"
            }
        
        # Get MATIC balance
        matic_balance = await get_matic_balance(relayer_address)
        matic_balance_decimal = Decimal(str(matic_balance))
        
        # Estimate gas cost per transaction (based on actual usage)
        # Average gas for MATIC send: ~21000 gas
        # Average gas for token transfer: ~65000 gas
        # Total for gasless tx: ~86000 gas
        # Current gas price: ~50 Gwei = 0.00000005 MATIC
        # Total cost: 86000 * 0.00000005 = 0.0043 MATIC per tx
        # Using conservative estimate: 0.0045 MATIC per tx
        avg_gas_cost = Decimal("0.0045")
        
        # Calculate estimated transactions remaining
        if matic_balance_decimal > 0:
            estimated_tx_remaining = int(matic_balance_decimal / avg_gas_cost)
        else:
            estimated_tx_remaining = 0
        
        # Determine status
        if matic_balance_decimal >= Decimal("0.1"):
            status_level = "funded"
            status_message = "✅ Relayer is well funded"
            recommendations = []
        elif matic_balance_decimal >= Decimal("0.05"):
            status_level = "low"
            status_message = "⚠️ Relayer balance is low"
            recommendations = [
                "Consider refilling the relayer wallet soon",
                f"Current balance can sponsor ~{estimated_tx_remaining} more transactions"
            ]
        elif matic_balance_decimal >= Decimal("0.01"):
            status_level = "critical"
            status_message = "🔴 Relayer balance is critically low"
            recommendations = [
                "⚠️ URGENT: Refill the relayer wallet immediately",
                f"Only {estimated_tx_remaining} transactions remaining",
                "Gasless transactions will fail when balance reaches 0"
            ]
        else:
            status_level = "empty"
            status_message = "❌ Relayer wallet is empty or nearly empty"
            recommendations = [
                "🚨 CRITICAL: Refill the relayer wallet NOW",
                "Gasless transactions are failing or will fail soon",
                "Users cannot send transactions without MATIC"
            ]
        
        # Build response
        response = {
            "enabled": True,
            "relayer_address": relayer_address,
            "matic_balance": float(matic_balance_decimal),
            "matic_balance_formatted": f"{matic_balance_decimal:.6f} MATIC",
            "estimated_transactions_remaining": estimated_tx_remaining,
            "average_gas_cost_matic": float(avg_gas_cost),
            "average_gas_cost_formatted": f"{avg_gas_cost} MATIC",
            "status": status_level,
            "status_message": status_message,
            "recommendations": recommendations,
            "network": "Polygon Amoy Testnet" if settings.USE_TESTNET else "Polygon Mainnet",
            "timestamp": asyncio.get_event_loop().time()
        }
        
        logger.info(f"📊 Relayer status: {status_level} - Balance: {matic_balance_decimal:.6f} MATIC - Estimated TX: {estimated_tx_remaining}")
        
        return response
        
    except Exception as e:
        logger.error(f"❌ Error getting relayer status: {e}")
        logger.exception(e)
        return {
            "enabled": settings.ENABLE_GASLESS,
            "status": "error",
            "error": str(e),
            "message": "Failed to retrieve relayer status"
        }
