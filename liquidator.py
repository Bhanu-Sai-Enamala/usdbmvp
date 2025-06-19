import subprocess
import os
import json

ORD_DIRECTORY = "/Users/bhanusaienamala/Desktop/bitcoin/runes_sourcecode/ordbtclock/ord-btclock"
ORD_WALLET_NAME = "liquidator"

def create_liquidator_wallet():
    cmd = [
        "ord", "--regtest",
        "--cookie-file", "env/regtest/.cookie",
        "--datadir", "env",
        "wallet", "--name", ORD_WALLET_NAME, "create"
    ]
    subprocess.run(cmd, cwd=ORD_DIRECTORY, check=True)
    print("✅ Liquidator wallet created.")

def fund_liquidator_wallet():
    # Get new receive address
    cmd = [
        "ord", "--regtest",
        "--cookie-file", "env/regtest/.cookie",
        "--datadir", "env",
        "wallet", "--name", ORD_WALLET_NAME, "receive"
    ]
    address = subprocess.check_output(cmd, cwd=ORD_DIRECTORY, text=True).strip()
    address = json.loads(address)
    address = address["addresses"][0]
    print(f"📬 Funding address: {address}")
    # Send 10 BTC to it from default ord wallet
    send_cmd = [
        "ord", "--regtest",
        "--cookie-file", "env/regtest/.cookie",
        "--datadir", "env",
        "wallet", "send",
        "--fee-rate", "1",address,"1000000000sat"
    ]
    # ["ord", "--regtest", "--cookie-file", "env/regtest/.cookie", "--data-dir", "env", "wallet", "send", "--fee-rate", "1", address, f"{amount}sat"],
     # Replace with an actual regtest address
    
    subprocess.run(send_cmd, cwd=ORD_DIRECTORY, check=True)
    
    print("💰 Sent 10 BTC to liquidator wallet.")
def mine():
    subprocess.check_output(["bitcoin-cli", "-datadir=env", "generatetoaddress", "10", "bcrt1prk89zmjdchcffnvm5pxw0w5y0cd70d8fujuamfm2tat8svjqrpsqtu5ucx"],cwd=ORD_DIRECTORY,
                    stderr=subprocess.STDOUT,
                    text=True)

def run_mint_with_btc_lock():
    result = subprocess.check_output(
        [
            "./target/release/ord",
            "--regtest",
            "--cookie-file", "env/regtest/.cookie",
            "--data-dir", "env",
            "wallet",
            "--name", "liquidator",
            "mint-with-btc-lock",
            "--fee-rate", "1.0",
            "--rune", "UNCOMMONGOODS",
            "--btc-lock-amount", "10000sat",
            "--fee-amount", "5000sat",
            "--fee-recipient", "bcrt1prk89zmjdchcffnvm5pxw0w5y0cd70d8fujuamfm2tat8svjqrpsqtu5ucx",
            "--destination", "bcrt1prk89zmjdchcffnvm5pxw0w5y0cd70d8fujuamfm2tat8svjqrpsqtu5ucx"
        ],
        cwd=ORD_DIRECTORY,
        stderr=subprocess.STDOUT,
        text=True
    )
    print("🧊 Minted with BTC lock .")
    print(result)

if __name__ == "__main__":
    create_liquidator_wallet()
    fund_liquidator_wallet()
    mine()
    
    run_mint_with_btc_lock()



