import subprocess
import os
import json
import pexpect 
import re

def run_path_two_unlock():
    # Setup environment
    env = os.environ.copy()
    

    # Absolute path to the directory where ord command should be run
    ORD_DIRECTORY = "/Users/bhanusaienamala/Desktop/bitcoin/runes_sourcecode/ordbtclock/ord-btclock"

    # Construct the command
    burn_cmd = [
        "ord", "--regtest",
        "--cookie-file", "env/regtest/.cookie",
        "--datadir", "env",
        "wallet", "--name","liquidator", "burn", "--dry-run", "1000:UNCOMMONGOODS",
        "--fee-rate", "1"
    ]
    # burn_cmd = [
    #     "ord", "--regtest",
    #     "--cookie-file", "env/regtest/.cookie",
    #     "--datadir", "env",
    #     "wallet", "burn", "--dry-run", "1000:UNCOMMONGOODS",
    #     "--fee-rate", "1"
    # ]

    # Execute the command
    burn_result = subprocess.run(burn_cmd, cwd=ORD_DIRECTORY, env=env, capture_output=True, text=True)

    print("STDOUT:\n", burn_result.stdout)
    print("STDERR:\n", burn_result.stderr)

        # --- Inserted block for extracting PSBT and decoding ---
    burn_output = json.loads(burn_result.stdout)
    psbt = burn_output["psbt"]
    print("PSBT:", psbt)
    decode_cmd = ["bitcoin-cli", "-datadir=env", "decodepsbt", psbt]
    decode_result = subprocess.run(decode_cmd,cwd=ORD_DIRECTORY, capture_output=True, text=True, check=True)
    decoded = json.loads(decode_result.stdout)
    op_return_hex = None

    for vout in decoded["tx"]["vout"]:
        script = vout.get("scriptPubKey", {})
        if script.get("type") == "nulldata":
            hex_field = script.get("hex")
            if hex_field and hex_field.startswith("6a"):  # OP_RETURN prefix
                # Strip '6a' (OP_RETURN) and '5d' (data push opcode if present)
                op_return_hex = hex_field[2:]  # remove just the OP_RETURN
                break

    if op_return_hex:
        print("✅ Extracted OP_RETURN hex data:", op_return_hex)
    else:
        print("❌ OP_RETURN data not found.")
    

# Remove first 2 bytes (4 hex chars)
    cleaned_op_return = op_return_hex[4:]

    print("🔹 Cleaned OP_RETURN (no prefix):", cleaned_op_return)
    input_txid = decoded["tx"]["vin"][0]["txid"]
    input_vout = decoded["tx"]["vin"][0]["vout"]
    print("Input TXID:", input_txid)
    print("Input VOUT:", input_vout)
    getraw_cmd = ["bitcoin-cli", "-datadir=env", "getrawtransaction", input_txid, "1"]
    raw_result = subprocess.run(getraw_cmd,cwd=ORD_DIRECTORY, capture_output=True, text=True, check=True)
    raw_tx = json.loads(raw_result.stdout)
    btc_locked_address = "bcrt1prk89zmjdchcffnvm5pxw0w5y0cd70d8fujuamfm2tat8svjqrpsqtu5ucx"
    voutBTClocked = None
    for vout_entry in raw_tx['vout']:
        addresses = vout_entry['scriptPubKey'].get('address', [])
        value = float(vout_entry.get('value', 0))
        if btc_locked_address in addresses and value == 0.0001:
            voutBTClocked = vout_entry['n']
            break
    if voutBTClocked is None:
        raise Exception("No matching vout with 0.0001 BTC to target address found.")
    print("BTC Locked VOUT (BTClocked):", voutBTClocked)

    # Extract and print scriptPubKey hex for both voutBTClocked and input_vout
    input_script_hex = raw_tx["vout"][input_vout]["scriptPubKey"]["hex"]
    voutBTClocked_script_hex = raw_tx["vout"][voutBTClocked]["scriptPubKey"]["hex"]
    print("Input ScriptPubKey Hex:", input_script_hex)
    print("BTC Locked ScriptPubKey Hex (BTClocked):", voutBTClocked_script_hex)
    receive_address = subprocess.check_output(
        [
            "ord", "--regtest", "--cookie-file", "env/regtest/.cookie", "--data-dir", "env",
            "wallet", "--name", "liquidator", "receive"
        ],
        cwd=ORD_DIRECTORY,
        stderr=subprocess.STDOUT,
        text=True
    ).strip()
    receive_address = json.loads(receive_address)
    receive_address = receive_address["addresses"][0]
    print("Receive Address:", receive_address)
    # receive_address = "bcrt1q6azl2g0gmkrqmjzra6cep4lmaq9ymww0djw6qx"  # Replace with actual address if needed
    # getraw_cmd = ["bitcoin-cli", "-datadir=env", "getrawtransaction", input_txid, "1"]
    # raw_result = subprocess.run(getraw_cmd,cwd=ORD_DIRECTORY, capture_output=True, text=True, check=True)
    inputs = [
    {"txid": input_txid, "vout": input_vout},
    {"txid": input_txid, "vout": voutBTClocked}
  ]

    outputs = [
        {"data": cleaned_op_return},
        {receive_address: 0.0001}
    ]

    inputs_json = json.dumps(inputs)
    outputs_json = json.dumps(outputs)

    createraw_cmd = [
        "bitcoin-cli", "-datadir=env", "createrawtransaction",
        inputs_json,
        outputs_json
    ]

    print("Command:", createraw_cmd)

    raw_tx_hex = subprocess.run(
        createraw_cmd,
        cwd=ORD_DIRECTORY,
        capture_output=True,
        text=True,
        check=True
    )
    print("Raw Transaction:", raw_tx_hex.stdout)
    pattern = cleaned_op_return
    raw_tx_hex_str = raw_tx_hex.stdout.strip()
    pattern_index = raw_tx_hex_str.find(pattern)

    if pattern_index == -1:
        raise ValueError("Pattern not found in transaction hex")

    # Step 2: Get the byte positions before the pattern
    byte_before_07 = pattern_index - 2
    byte_before_6a = pattern_index - 4
    byte_09_position = pattern_index - 6

    # Step 3: Validate expected values
    if raw_tx_hex_str[pattern_index - 2:pattern_index] != "07":
        raise ValueError("Byte before pattern is not 07")
    if raw_tx_hex_str[pattern_index - 4:pattern_index - 2] != "6a":
        raise ValueError("Byte before 07 is not 6a")
    if raw_tx_hex_str[pattern_index - 6:pattern_index - 4] != "09":
        raise ValueError("Byte before 6a is not 09")

    # Step 4: Replace 09 with 0a and insert 5d before 07
    modified_tx_hex = (
        raw_tx_hex_str[:pattern_index - 6] +   # before 09
        "0a" +                             # replace 09 with 0a
        "6a" +                             # keep 6a
        "5d" +                             # insert 5d
        "07" +                             # keep 07
        raw_tx_hex_str[pattern_index:]        # from pattern onwards
    )

    print("Modified raw transaction hex:")
    print(modified_tx_hex)
    convert_cmd = [
    "bitcoin-cli", "-datadir=env", "converttopsbt", modified_tx_hex
  ]
    convert_result = subprocess.run(
        convert_cmd, cwd=ORD_DIRECTORY, capture_output=True, text=True, check=True
    )
    psbt = convert_result.stdout.strip()
    print("Converted PSBT:", psbt)

    # Step 2: Process PSBT with wallet (sign it)
    process_cmd = [
        "bitcoin-cli", "-datadir=env", "-rpcwallet=liquidator", "walletprocesspsbt", psbt
    ]
    process_result = subprocess.run(
        process_cmd, cwd=ORD_DIRECTORY, capture_output=True, text=True, check=True
    )
    processed_data = json.loads(process_result.stdout)
    final_psbt = processed_data["psbt"]
    print("Final PSBT:", final_psbt)
    decode_cmd = [
    "bitcoin-cli", "-datadir=env", "decodepsbt", final_psbt
]
    decode_result = subprocess.run(
        decode_cmd, cwd=ORD_DIRECTORY, capture_output=True, text=True, check=True
    )

    decoded = json.loads(decode_result.stdout)

    # Extract final_scriptwitness from the first input
    final_witness = decoded["inputs"][0].get("final_scriptwitness", [])

    # Optionally, store it to a variable or file
    if final_witness:
        script_witness_hex = final_witness[0]
        print("Extracted final_scriptwitness:", script_witness_hex)
        # Example: Write to file
    else:
        print("final_scriptwitness not found in the decoded PSBT.")
    #insert sighash generation  command - @anshika
# ./target/release/ord --regtest   --cookie-file env/regtest/.cookie   --data-dir env   script-path-sighash   --rawtxhex 02000000014eeb7466e814a86fbadd776b027ff66d5452ca6cb35b617ccb9f988297ba89520000000000fdffffff01905f010000000000160014eb8ad234e24b89225c1f75e2abc8c01d3523e95500000000   --rawspendscriptpathhex 2025f1a245ff572ac11fc1e5da5f6a5a93c946f17c20f1c317c5bae2a0ef2d821cad20d2c1cb1575d323b6120b6e5bcc9ce5ad373e88e73e675030f1c2c5261b4dbc86ac   --script-pubkey-hex-one 51201d8e516e4dc5f094cd9ba04ce7ba847e1be7b4e9e4b9dda76a5f567832401860   --script-pubkey-hex-two 51201d8e516e4dc5f094cd9ba04ce7ba847e1be7b4e9e4b9dda76a5f567832401860   --input-index 0
    inputindex="1"
    print(input_script_hex)
    print(voutBTClocked_script_hex)
    # Replace with actual values
    sighash =subprocess.check_output(
                    [
                        "./target/release/ord",
                        "--regtest",
                        "--cookie-file", "env/regtest/.cookie",
                        "--data-dir", "env",
                        "script-path-sighash",
                        "--rawtxhex", modified_tx_hex,
                        "--rawspendscriptpathhex", "205bbe3b001504f3cba1d4cfdf4fa4289cde1c6eab9a935bf80a7f47c5038cbad1ad20bd9888e4ae4256ced593c2c609cf5b5e391bf7b11dcb8588c3845b9a1f3a7776ac",
                        "--script-pubkey-hex-one", input_script_hex,
                        "--script-pubkey-hex-two", voutBTClocked_script_hex,
                        "--input-index", inputindex
                    ],
                    cwd=ORD_DIRECTORY,
                    stderr=subprocess.STDOUT,
                    text=True
                )
    print("Sighash:", sighash.strip())
    sighash = sighash.strip()
    match = re.search(r"Taproot Script Path Sighash:\s*([0-9a-fA-F]{64})", sighash)
    if match:
        sighash = match.group(1)
        print("✅ Extracted sighash:", sighash)
    else:
        print("❌ Sighash not found.")
    privkey = "9202af6ce925b26ae6b25adfff0b2705147e195fa38dd58ae6ecc58ed263751f"

    # Spawn a btcdeb shell session
    child = pexpect.spawn("btcdeb")

    # Wait for the btcdeb prompt
    child.expect("btcdeb>")

    # Run the sign_schnorr command
    child.sendline(f"tf sign_schnorr {sighash} {privkey}")

    # Wait for the response
    child.expect("btcdeb>")

    # Extract the output
    output = child.before.decode("utf-8")
    print("Output from btcdeb:\n", output)
    # Parse the output to extract the signature
    protocol_signature = ""
    for line in output.strip().splitlines():
        if len(line.strip()) == 128:
            protocol_signature = line.strip()
            break

    # Display results
    # print("✅ Protocol Schnorr Signature:", protocol_signature)
    if protocol_signature:
        print("✅ Protocol Schnorr Signature:", protocol_signature)
    else:
        print("❌ Signature not found in output.")

    # Exit btcdeb
    child.sendline("exit")
    privkey = "d1600e70c9aa547440eae896de8841628ddfe9eb3c1e49d715b28ad1e4d79c04"

    # Spawn a btcdeb shell session
    child = pexpect.spawn("btcdeb")

    # Wait for the btcdeb prompt
    child.expect("btcdeb>")

    # Run the sign_schnorr command
    child.sendline(f"tf sign_schnorr {sighash} {privkey}")

    # Wait for the response
    child.expect("btcdeb>")

    # Extract the output
    output = child.before.decode("utf-8")

    # Parse the output to extract the signature
    liquidator_signature = ""
    for line in output.strip().splitlines():
        if len(line.strip()) == 128:
            liquidator_signature = line.strip()
            break

    # Display results
    if liquidator_signature:
        print("✅ Liquidator Schnorr Signature:", liquidator_signature)
    else:
        print("❌ Signature not found in output.")

    # Exit btcdeb
    child.sendline("exit")
    controlblock = "44205bbe3b001504f3cba1d4cfdf4fa4289cde1c6eab9a935bf80a7f47c5038cbad1ad20bd9888e4ae4256ced593c2c609cf5b5e391bf7b11dcb8588c3845b9a1f3a7776ac61c15bf08d58a430f8c222bffaf9127249c5cdff70a2d68b2b45637eb662b6b88eb5cae3444ac843ef763e83e4ec08b00011700502ae6795cb10e8027d700f2d3ff2d29ab618193c0908c50339f77cce4b89935f4df11ed45f3bdff6f7395edd59fb"
    # Build final transaction
    final_tx_hex = ""
    final_tx_hex += modified_tx_hex[:8]               # version
    final_tx_hex += "0001"                       # marker & flag for segwit
    final_tx_hex += modified_tx_hex[8:-8]             # all except final locktime
    final_tx_hex += "0140" + script_witness_hex  # witness 1
    final_tx_hex += "0440" + liquidator_signature      # witness 2
    final_tx_hex += "40" + protocol_signature    # witness 3
    final_tx_hex += controlblock
    final_tx_hex += "00000000"                   # locktime

    print("✅ Final signed Transaction Hex:\n", final_tx_hex)

    sendrawtransaction_cmd = [
    "bitcoin-cli", "-datadir=env", "sendrawtransaction", final_tx_hex
]
    result = subprocess.run(
        sendrawtransaction_cmd, cwd=ORD_DIRECTORY, capture_output=True, text=True, check=True
    )
    return f"✅ Transaction broadcasted!\nTXID: {result.stdout.strip()}"



