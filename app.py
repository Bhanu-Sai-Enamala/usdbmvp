from flask import Flask, render_template_string, request
import subprocess
import os
from indexer import validate_mint, run_block_watcher_once
import json
from generateP2TRaddress import generate_bech32m_address
from pathOneUnclock import run_path_one_unlock
from pathTwoUnlock import run_path_two_unlock
app = Flask(__name__)


ORD_DIRECTORY = "/Users/bhanusaienamala/Desktop/bitcoin/runes_sourcecode/ordbtclock/ord-btclock"


HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>USDB stable coin</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 30px; }
        .section { border: 1px solid #ddd; border-radius: 8px; padding: 18px 22px; margin-bottom: 25px; background: #f8f8f8; }
        h2 { margin-top: 0; }
        form { margin-bottom: 12px; }
        input[type="text"], input[type="number"] { padding: 5px; border-radius: 4px; border: 1px solid #bbb; margin-right: 7px; }
        button { margin-right: 8px; padding: 7px 14px; border-radius: 5px; border: none; cursor: pointer; font-size: 1em; }
    </style>
</head>
<body>
    <h1>USDB Stable Coin</h1>
    <div class="section">
        <h2>Admin Section</h2>
        <form method="post" style="display:inline;">
            <button name="action" value="get_balance" style="background-color:#4CAF50;color:white">Get Wallet Balance</button>
        </form>
        <form method="post" style="display:inline;">
            <button name="action" value="start_env" style="background-color:#4CAF50;color:white">Start ord,bitcoin test server</button>
        </form>
        <form method="post" style="display:inline;">
            <button name="action" value="etch_rune" style="background-color:#2196F3;color:white">Etch Rune</button>
        </form>
        <form method="post" style="display:inline;">
            <button name="action" value="get_receive_address">Generate Admin BTC Receive Address</button>
        </form>
    </div>
    <div class="section">
        <h2>User Section</h2>
        <form method="post" style="display:inline;">
            <button name="action" value="get_user_receive_address">Get User Wallet Receive Address</button>
        </form>
        <form method="post" style="display:inline;">
            <button name="action" value="create_user">Create User</button>
        </form>
        <form method="post" style="display:inline;">
            <button name="action" value="get_user_balance">Get User Wallet Balance</button>
        </form>
        <form method="post">
            <input type="text" name="mint_rune_name" placeholder="Rune Name" required>
            <input type="text" name="mint_destination" placeholder="Destination Address" required>
            <button name="action" value="mint_with_btc_lock">Mint with BTC Lock</button>
        </form>
        <form method="post">
            <input type="text" name="validate_txid" placeholder="Transaction ID" required>
            <input type="text" name="validate_admin" placeholder="Admin Address" required>
            <button name="action" value="validate_transaction">Validate Transaction</button>
        </form>
    </div>
    <div class="section">
        <h2>Other</h2>
        <form method="post">
            <input type="number" name="block_count" placeholder="Number of blocks" required>
            <button name="action" value="mine_blocks">Mine Blocks</button>
        </form>
        <form method="post">
            <input type="text" name="send_address" placeholder="Destination address" required>
            <input type="text" name="send_amount" placeholder="Amount in sats" required>
            <button name="action" value="send_ordinal">Send Sats</button>
        </form>
        <form method="post">
            <button name="action" value="run_block_watcher">Run USDB Watcher</button>
        </form>
    </div>
    <div class="section">
    <h2>Liquidation with User and Protocol Coordination</h2>
    <h3>🧾 User constructs a transaction burning the runes he received by locking BTC and includes in the same transaction the unlocking of the locked BTC</h3>
    <h3>✍️ User signs and submits it to the protocol.</h3>
    <h3>✅ Protocol checks and provides its signature for unlock of the BTC locked UTXO using script path.n</h3>
    <form method="post">
        <!-- Placeholder for logic to be added -->
        <button name="action" value="burn_runes_unlock_btc">Burn Runes and Unlock BTC</button>
    </form>
    </div>
    <div class="section">
    <h2>Oracle Attested Liquidation</h2>
    <h3>Protocol detects an undercollateralised debt.Construsts a transaction to auction off the locked BTC and sends to oracle </h3>
    <h3>oracle provides signature for liquidation</h3>
    <h3>The auctionee(liquidation provider) receives the partially signed transaction, signs and brodcasts. Thus the BTC is unlocked through different path and corresponding runes burnt in same transaction. n</h3>
    <form method="post">
        <!-- Placeholder for logic to be added -->
        <button name="action" value="auction_btc">Auction BTC</button>
    </form>
    </div>
    {% if result %}
        <h2>Result:</h2>
        <pre>{{ result }}</pre>
    {% endif %}
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    if request.method == "POST":
        action = request.form.get("action")
        try:
            if action == "get_balance":
                result = subprocess.check_output(
                    ["ord", "--datadir", "env", "wallet", "balance"],
                    cwd=ORD_DIRECTORY,
                    stderr=subprocess.STDOUT,
                    text=True
                )
            elif action == "start_env":
                subprocess.Popen(
                    ["ord", "env"],
                    cwd=ORD_DIRECTORY,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                ) 
                import time
                time.sleep(10)
                result = "ord and bitcoin test server started."
            elif action == "stop_env":
                result = subprocess.check_output(
                    ["pkill", "-f", "ord.*env"],
                    stderr=subprocess.STDOUT,
                    text=True
                )
            elif action == "etch_rune":
                result = subprocess.check_output(
                    ["ord", "--regtest", "--cookie-file", "env/regtest/.cookie", "--data-dir", "env", "wallet", "batch", "--batch", "env/batch.yaml", "--fee-rate", "1", "--no-backup"],
                    cwd=ORD_DIRECTORY,
                    stderr=subprocess.STDOUT,
                    text=True
                )
            elif action == "mine_blocks":
                block_count = request.form.get("block_count")
                address = "bcrt1psynxtwkl9538helj3ll74ydz09yuvh509szcus3elsf6aykc9ghsafwd2z"  # Replace with an actual regtest address
                result = subprocess.check_output(
                    ["bitcoin-cli", "-datadir=env", "generatetoaddress", block_count, address],
                    cwd=ORD_DIRECTORY,
                    stderr=subprocess.STDOUT,
                    text=True
                )
            elif action == "get_receive_address":
                result = generate_bech32m_address()
            elif action == "get_user_receive_address":
                result = subprocess.check_output(
                    ["ord", "--regtest", "--cookie-file", "env/regtest/.cookie", "--data-dir", "env", "wallet","--name", "user", "receive"],
                    cwd=ORD_DIRECTORY,
                    stderr=subprocess.STDOUT,
                    text=True
                )
            elif action == "create_user":
                result = subprocess.check_output(
                    ["ord", "--regtest", "--cookie-file", "env/regtest/.cookie", "--data-dir", "env", "wallet", "--name", "user","create",],
                    cwd=ORD_DIRECTORY,
                    stderr=subprocess.STDOUT,
                    text=True
                )
            elif action == "get_user_balance":
                result = subprocess.check_output(
                    ["ord", "--regtest", "--cookie-file", "env/regtest/.cookie", "--data-dir", "env", "wallet", "--name", "user", "balance"],
                    cwd=ORD_DIRECTORY,
                    stderr=subprocess.STDOUT,
                    text=True
                )
            elif action == "send_ordinal":
                address = request.form.get("send_address")
                amount = request.form.get("send_amount")
                result = subprocess.check_output(
                    ["ord", "--regtest", "--cookie-file", "env/regtest/.cookie", "--data-dir", "env", "wallet", "send", "--fee-rate", "1", address, f"{amount}sat"],
                    cwd=ORD_DIRECTORY,
                    stderr=subprocess.STDOUT,
                    text=True
                )
            elif action == "mint_with_btc_lock":
                rune_name = request.form.get("mint_rune_name")
                destination = request.form.get("mint_destination")
                result = subprocess.check_output(
                    [
                        "./target/release/ord",
                        "--regtest",
                        "--cookie-file", "env/regtest/.cookie",
                        "--data-dir", "env",
                        "wallet",
                        "--name", "user",
                        "mint-with-btc-lock",
                        "--fee-rate", "1.0",
                        "--rune", rune_name,
                        "--btc-lock-amount", "10000sat",
                        "--fee-amount", "5000sat",
                        "--fee-recipient", destination,
                        "--destination", destination
                    ],
                    cwd=ORD_DIRECTORY,
                    stderr=subprocess.STDOUT,
                    text=True
                )
            elif action == "validate_transaction":
                txid = request.form.get("validate_txid")
                admin_address = request.form.get("validate_admin")
                result_dict = validate_mint(txid, admin_address)
                result = json.dumps(result_dict, indent=2) if result_dict else "❌ Invalid or no mint detected."
            elif action == "run_block_watcher":
                mints = run_block_watcher_once()
                if mints:
                    result = json.dumps(mints, indent=2)
                    result += "\n\n✅ Valid mint confirmed and BTC lock to protocol provided address verified."
                else:
                    result = "❌ No valid mints found during block scan."
            elif action == "burn_runes_unlock_btc":
                
                    # Replace with actual logic to run the script
                output = run_path_one_unlock()
                if output:
                    result = f"✅ BTC Unlocked and corresponding Runes Burnt:\n{output}"
                else:
                    result = f"❌ No BTC to unlock or error in unlocking process.\nDetails:\n{output}"
            elif action == "auction_btc":
        
            # Replace with actual logic to run the script
                output = run_path_two_unlock()
                if output:
                    result = f"✅ BTC auctioned off and corresponding Runes Burnt:\n{output}"
                else:
                    result = f"❌ No BTC to unlock or error in unlocking process.\nDetails:\n{output}"
        except subprocess.CalledProcessError as e:
            result = f"Error:\n{e.output}"
    return render_template_string(HTML_TEMPLATE, result=result)

if __name__ == "__main__":
    app.run(debug=True, port=9050)