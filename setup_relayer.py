"""
Quick Setup: Create and Configure DARI Relayer Wallet
This script helps you set up a relayer wallet for gasless transactions
"""

from web3 import Web3
import os
from pathlib import Path

print("=" * 60)
print("DARI Relayer Wallet Setup")
print("=" * 60)
print()

# Ask user what they want to do
print("Options:")
print("1. Generate a NEW relayer wallet")
print("2. Use an EXISTING wallet (enter private key)")
print()

choice = input("Enter your choice (1 or 2): ").strip()

if choice == "1":
    # Generate new wallet
    print("\n🔄 Generating new wallet...")
    w3 = Web3()
    account = w3.eth.account.create()
    
    relayer_address = account.address
    relayer_private_key = account.key.hex()
    
    print("\n✅ New Wallet Generated!")
    print(f"Address: {relayer_address}")
    print(f"Private Key: {relayer_private_key}")
    print()
    print("⚠️  IMPORTANT: Save these credentials securely!")
    print("⚠️  Never share your private key with anyone!")
    
elif choice == "2":
    # Use existing wallet
    print("\n📝 Using existing wallet...")
    relayer_private_key = input("Enter your private key (with or without 0x): ").strip()
    
    # Add 0x prefix if missing
    if not relayer_private_key.startswith("0x"):
        relayer_private_key = "0x" + relayer_private_key
    
    # Derive address from private key
    try:
        w3 = Web3()
        account = w3.eth.account.from_key(relayer_private_key)
        relayer_address = account.address
        
        print(f"\n✅ Wallet loaded!")
        print(f"Address: {relayer_address}")
    except Exception as e:
        print(f"\n❌ Error: Invalid private key - {e}")
        exit(1)
else:
    print("❌ Invalid choice")
    exit(1)

# Ask about network
print("\n" + "=" * 60)
print("Network Configuration")
print("=" * 60)
print()
print("Which network will you use?")
print("1. Testnet (Polygon Amoy/Mumbai) - FREE MATIC from faucet")
print("2. Mainnet (Polygon) - Requires real MATIC")
print()

network_choice = input("Enter your choice (1 or 2): ").strip()

if network_choice == "1":
    use_testnet = "true"
    network_name = "Testnet (Polygon Amoy/Mumbai)"
    print(f"\n✅ Selected: {network_name}")
    print("\n💡 Get free testnet MATIC:")
    print(f"   1. Visit: https://faucet.polygon.technology/")
    print(f"   2. Enter your address: {relayer_address}")
    print(f"   3. Request testnet MATIC")
elif network_choice == "2":
    use_testnet = "false"
    network_name = "Mainnet (Polygon)"
    print(f"\n✅ Selected: {network_name}")
    print("\n💡 Fund your wallet with MATIC:")
    print(f"   1. Buy MATIC from an exchange")
    print(f"   2. Send to: {relayer_address}")
    print(f"   3. Recommended: 10-100 MATIC to start")
else:
    print("❌ Invalid choice")
    exit(1)

# Create or update .env file
print("\n" + "=" * 60)
print("Updating .env File")
print("=" * 60)
print()

env_path = Path(".env")
env_content = ""

# Read existing .env if it exists
if env_path.exists():
    with open(env_path, 'r') as f:
        env_content = f.read()

# Update or add relayer configuration
lines = env_content.split('\n')
new_lines = []
found_relayer_key = False
found_relayer_address = False
found_gasless = False
found_testnet = False

for line in lines:
    if line.startswith("RELAYER_PRIVATE_KEY="):
        new_lines.append(f"RELAYER_PRIVATE_KEY={relayer_private_key}")
        found_relayer_key = True
    elif line.startswith("RELAYER_ADDRESS="):
        new_lines.append(f"RELAYER_ADDRESS={relayer_address}")
        found_relayer_address = True
    elif line.startswith("ENABLE_GASLESS="):
        new_lines.append("ENABLE_GASLESS=true")
        found_gasless = True
    elif line.startswith("USE_TESTNET="):
        new_lines.append(f"USE_TESTNET={use_testnet}")
        found_testnet = True
    else:
        new_lines.append(line)

# Add missing variables
if not found_relayer_key:
    new_lines.append(f"\n# DARI Relayer Wallet (for gasless transactions)")
    new_lines.append(f"RELAYER_PRIVATE_KEY={relayer_private_key}")
if not found_relayer_address:
    new_lines.append(f"RELAYER_ADDRESS={relayer_address}")
if not found_gasless:
    new_lines.append("ENABLE_GASLESS=true")
if not found_testnet:
    new_lines.append(f"USE_TESTNET={use_testnet}")

# Write back to .env
with open(env_path, 'w') as f:
    f.write('\n'.join(new_lines))

print("✅ .env file updated successfully!")

# Summary
print("\n" + "=" * 60)
print("Setup Complete!")
print("=" * 60)
print()
print("📋 Configuration Summary:")
print(f"   Relayer Address: {relayer_address}")
print(f"   Network: {network_name}")
print(f"   Gasless Mode: ENABLED")
print()
print("📝 Next Steps:")
print()
if network_choice == "1":
    print("   1. Get free testnet MATIC from faucet:")
    print("      https://faucet.polygon.technology/")
    print()
else:
    print("   1. Fund your relayer wallet with MATIC")
    print(f"      Send MATIC to: {relayer_address}")
    print()
print("   2. Verify your setup:")
print("      python check_relayer.py")
print()
print("   3. Start your server:")
print("      uvicorn app.main:app --reload")
print()
print("   4. Test gasless transaction:")
print("      POST /api/v1/transactions/estimate-fee")
print()
print("=" * 60)
print("✅ You're all set for gasless transactions!")
print("=" * 60)
