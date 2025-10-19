from web3 import Web3

# Connect to Polygon Amoy testnet
w3 = Web3(Web3.HTTPProvider('https://rpc-amoy.polygon.technology'))

# Relayer address from .env
relayer_address = '0x3e1ac401EB1d85D8D9d337F838E514eCE552313C'

print("=" * 60)
print("RELAYER WALLET DIAGNOSTICS")
print("=" * 60)

# Check relayer balance
matic_balance = w3.eth.get_balance(relayer_address)
print(f"\nRelayer Address: {relayer_address}")
print(f"MATIC Balance: {w3.from_wei(matic_balance, 'ether')} MATIC")

if matic_balance == 0:
    print(f"\n❌ RELAYER HAS NO MATIC!")
    print(f"   The gasless transaction system won't work.")
    print(f"\n💡 Solution: Fund the relayer wallet with testnet MATIC:")
    print(f"   1. Go to: https://faucet.polygon.technology/")
    print(f"   2. Request MATIC for: {relayer_address}")
else:
    gas_price = w3.eth.gas_price
    estimated_cost = w3.from_wei(gas_price * 100000, 'ether')
    num_transactions = int(w3.from_wei(matic_balance, 'ether') / estimated_cost)
    print(f"\n✅ RELAYER IS FUNDED!")
    print(f"   Can sponsor ~{num_transactions} transactions")
    print(f"   Current gas cost: {estimated_cost} MATIC per tx")

print("=" * 60)
