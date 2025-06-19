# tap_utils.py
import subprocess

def generate_bech32m_address():
    cmd = [
        "tap",
        "5bf08d58a430f8c222bffaf9127249c5cdff70a2d68b2b45637eb662b6b88eb5",
        "3",
        '[25f1a245ff572ac11fc1e5da5f6a5a93c946f17c20f1c317c5bae2a0ef2d821c OP_CHECKSIGVERIFY d2c1cb1575d323b6120b6e5bcc9ce5ad373e88e73e675030f1c2c5261b4dbc86 OP_CHECKSIG]',
        '[5bbe3b001504f3cba1d4cfdf4fa4289cde1c6eab9a935bf80a7f47c5038cbad1 OP_CHECKSIGVERIFY bd9888e4ae4256ced593c2c609cf5b5e391bf7b11dcb8588c3845b9a1f3a7776 OP_CHECKSIG]',
        '[d2c1cb1575d323b6120b6e5bcc9ce5ad373e88e73e675030f1c2c5261b4dbc86 OP_CHECKSIGVERIFY 12960 OP_CHECKSEQUENCEVERIFY]',
    ]

    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

    for line in result.stdout.splitlines():
        if "Resulting Bech32m address:" in line:
            return line.split(":")[1].strip()

    raise Exception("Address generation failed.\nOutput:\n" + result.stdout)

print(generate_bech32m_address())