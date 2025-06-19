import os
import json
import time
import requests
from base64 import b64encode
from bip_utils import Bip39SeedGenerator, Bip44, Bip44Coins, Bip44Changes
from bs4 import BeautifulSoup
from typing import List

# ---------------- CONFIG ---------------- #
BITCOIN_RPC_URL = "http://localhost:9000"
ORD_SERVER_URL = "http://localhost:9001"
COOKIE_PATH = "/Users/bhanusaienamala/Desktop/bitcoin/runes_sourcecode/ordbtclock/ord-btclock/env/regtest/.cookie"
MNEMONIC = "degree evidence predict noble episode color stable chimney barrel drum badge gun"  # 🔑 Replace
LOCK_AMOUNT_BTC = 0.0001
FEE_AMOUNT_BTC = 0.00005
CHECK_INTERVAL = 5  # seconds

# ---------------- SETUP ---------------- #
with open(COOKIE_PATH, "r") as f:
    rpc_user, rpc_pass = f.read().strip().split(":", 1)
    auth_header = b64encode(f"{rpc_user}:{rpc_pass}".encode()).decode()

def bitcoin_rpc(method, params=[]):
    payload = {
        "jsonrpc": "1.0",
        "id": "indexer",
        "method": method,
        "params": params
    }
    response = requests.post(
        BITCOIN_RPC_URL,
        headers={"Authorization": f"Basic {auth_header}"},
        data=json.dumps(payload)
    )
    response.raise_for_status()
    return response.json()["result"]

def derive_admin_addresses(mnemonic, count=500):
    seed_bytes = Bip39SeedGenerator(mnemonic).Generate()
    bip44 = Bip44.FromSeed(seed_bytes, Bip44Coins.BITCOIN_TESTNET)
    account = bip44.Purpose().Coin().Account(0)
    addresses = []
    for i in range(count):
        ext_addr = account.Change(Bip44Changes.CHAIN_EXT).AddressIndex(i).PublicKey().ToAddress()
        addresses.append(ext_addr)
    return addresses

wallet_addresses = derive_admin_addresses(MNEMONIC)
validated_mints = {}

def check_transaction(txid, admin_address):
    try:
        tx = bitcoin_rpc("getrawtransaction", [txid, True])
    except Exception as e:
        print(f"❌ Failed to fetch tx {txid}: {e}")
        return None

    outputs = tx["vout"]
    op_return_found = False
    total_received_by_admin = 0.0
    rune_owner_address = None

    print(f"\n🔍 Checking transaction: {txid}")
    for vout in outputs:
        script = vout["scriptPubKey"]
        script_type = script["type"]
        value = vout["value"]
        address = script.get("address", "")
        asm = script.get("asm", "")

        print(f"  → VOUT: type={script_type}, value={value}, address={address}")

        if script_type == "nulldata" and asm.startswith("OP_RETURN 13"):
            op_return_found = True
            print("  ✅ OP_RETURN Runestone found")

        if script_type == "witness_v1_taproot":
            if not rune_owner_address:
                rune_owner_address = address
            if admin_address is None or address == admin_address:
                total_received_by_admin += value
           

    if op_return_found and total_received_by_admin >= (LOCK_AMOUNT_BTC + FEE_AMOUNT_BTC):
        try:
            ord_res = requests.get(f"{ORD_SERVER_URL}/address/{rune_owner_address}")
            if ord_res.status_code != 200:
                print(f"❌ Failed to reach ord server for {rune_owner_address}")
                return None

            soup = BeautifulSoup(ord_res.text, 'html.parser')
            rune_label = soup.find("dt", string="rune balances")
            if rune_label:
                balances_dd = rune_label.find_next_sibling("dd")
                rune_links = balances_dd.find_all("a") if balances_dd else []
                runes_found = [link.text.strip() for link in rune_links]
            else:
                runes_found = []
            if "UNCOMMONGOODS" not in runes_found:
                print(f"❌ Rune not found in ord server HTML: {runes_found}")
                return None

            print(f"✅ Valid Rune Mint confirmed (HTML-parsed) and BTC lock verified!")
        except Exception as e:
            print(f"❌ Error parsing HTML from ord server: {e}")
            return None

        validated_mints[txid] = {
            "txid": txid,
            "address": rune_owner_address,
            "coin": "UNCOMMONGOODS",
            "confirmed_by_ord": True
        }
        return validated_mints[txid]
    else:
        print(f"❌ BTC lock condition not met or OP_RETURN missing")
    return None

def validate_mint(txid, admin_address):
    return check_transaction(txid, admin_address)


# Run block watcher once and return valid mints
def run_block_watcher_once() -> List[dict]:
    seen = set()
    valid_mints = []
    try:
        blockcount = bitcoin_rpc("getblockcount")
        for height in range(blockcount + 1):
            blockhash = bitcoin_rpc("getblockhash", [height])
            block = bitcoin_rpc("getblock", [blockhash, 2])
            for tx in block["tx"]:
                txid = tx["txid"]
                if txid not in seen:
                    seen.add(txid)
                    result = check_transaction(txid, None)
                    if result:
                        valid_mints.append(result)
    except Exception as e:
        print(f"Watcher error: {e}")
    return valid_mints

# Optionally enable watcher
def block_watcher():
    seen = set()
    while True:
        try:
            blockcount = bitcoin_rpc("getblockcount")
            for height in range(blockcount + 1):
                blockhash = bitcoin_rpc("getblockhash", [height])
                block = bitcoin_rpc("getblock", [blockhash, 2])
                for tx in block["tx"]:
                    txid = tx["txid"]
                    if txid not in seen:
                        seen.add(txid)
                        check_transaction(txid, None)
        except Exception as e:
            print(f"Watcher error: {e}")
        time.sleep(CHECK_INTERVAL)
