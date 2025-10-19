from web3 import Web3

# Connect to Polygon Amoy testnet
w3 = Web3(Web3.HTTPProvider('https://rpc-amoy.polygon.technology'))

# Sender address from the logs
sender_address = '0xE349349055aFc5Ed2c3E640d60a64cD26Ba0A9b9'
receiver_address = '0xb81c62B02B9C85fA1d8DaB0383d3768E4A4392D1'
usdc_contract = '0x8b0180f2101c8260d49339abfee87927412494b4'

print("=" * 60)
print("BLOCKCHAIN DIAGNOSTICS")
print("=" * 60)

# Check connection
print(f"\n1. RPC Connection:")
print(f"   Connected: {w3.is_connected()}")
print(f"   Chain ID: {w3.eth.chain_id}")

# Check sender balance
matic_balance = w3.eth.get_balance(sender_address)
print(f"\n2. Sender Wallet ({sender_address}):")
print(f"   MATIC Balance: {w3.from_wei(matic_balance, 'ether')} MATIC")
print(f"   Has Gas: {'✅ YES' if matic_balance > 0 else '❌ NO - NEED MATIC FOR GAS'}")

# Check USDC balance
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
    }
]

try:
    usdc = w3.eth.contract(address=Web3.to_checksum_address(usdc_contract), abi=ERC20_ABI)
    usdc_balance_raw = usdc.functions.balanceOf(Web3.to_checksum_address(sender_address)).call()
    usdc_decimals = usdc.functions.decimals().call()
    usdc_balance = usdc_balance_raw / (10 ** usdc_decimals)
    
    print(f"\n3. USDC Token Balance:")
    print(f"   Contract: {usdc_contract}")
    print(f"   Balance: {usdc_balance} USDC")
    print(f"   Has USDC: {'✅ YES' if usdc_balance > 0 else '❌ NO - NEED USDC TOKENS'}")
except Exception as e:
    print(f"\n3. USDC Token Balance:")
    print(f"   ❌ Error: {str(e)}")

# Check gas price
try:
    gas_price = w3.eth.gas_price
    print(f"\n4. Gas Price:")
    print(f"   Current: {w3.from_wei(gas_price, 'gwei')} Gwei")
    estimated_gas_cost = gas_price * 100000  # 100k gas limit
    print(f"   Estimated TX Cost: {w3.from_wei(estimated_gas_cost, 'ether')} MATIC")
    print(f"   Can Afford: {'✅ YES' if matic_balance >= estimated_gas_cost else '❌ NO'}")
except Exception as e:
    print(f"\n4. Gas Price: ❌ Error: {str(e)}")

# Check receiver address
print(f"\n5. Receiver Wallet ({receiver_address}):")
receiver_balance = w3.eth.get_balance(receiver_address)
print(f"   MATIC Balance: {w3.from_wei(receiver_balance, 'ether')} MATIC")
print(f"   Address Valid: {'✅ YES' if w3.is_address(receiver_address) else '❌ NO'}")

print("\n" + "=" * 60)
print("SUMMARY:")
print("=" * 60)

issues = []
if matic_balance == 0:
    issues.append("❌ Sender has NO MATIC for gas fees")
if matic_balance > 0 and matic_balance < estimated_gas_cost:
    issues.append("⚠️  Sender has insufficient MATIC for gas")

if not issues:
    print("✅ All checks passed! Transaction should work.")
else:
    print("❌ Issues found:")
    for issue in issues:
        print(f"   {issue}")
    print("\n💡 Solution: Send testnet MATIC to sender address from faucet:")
    print("   https://faucet.polygon.technology/")
    print(f"   Address: {sender_address}")

print("=" * 60)
