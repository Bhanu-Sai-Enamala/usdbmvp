from ecdsa import SigningKey, SECP256k1
import hashlib


# List of user names
names = ["Protocol_Operator","User","Oracle","Liquidation_Agent","internal"]

# Store keypairs
keypairs = {} 

for name in names:
    # Convert name to lowercase, hash with sha256 to derive private key
    name_bytes = name.lower().encode()
    privkey_bytes = hashlib.sha256(name_bytes).digest()

    # Create SigningKey from deterministic private key
    sk = SigningKey.from_string(privkey_bytes, curve=SECP256k1)
    vk = sk.get_verifying_key()

    # Get compressed public key
    x = vk.pubkey.point.x()
    y = vk.pubkey.point.y()
    compressed_pubkey = x.to_bytes(32, 'big')

    keypairs[name] = {
        "private_key": privkey_bytes.hex(),
        "compressed_public_key": compressed_pubkey.hex()
    }

# Print keypairs
for name, keys in keypairs.items():
    print(f"{name}:")
    print(f"  Private Key: {keys['private_key']}")
    print(f"  Compressed Public Key: {keys['compressed_public_key']}")
    print()