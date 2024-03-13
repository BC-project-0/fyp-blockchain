from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend
import base64

def decodeBase64(base64_string):
    base64_bytes = base64_string.encode("latin-1")
    return base64.b64decode(base64_bytes)

def verify_initial_signature(pubKey, id, y0, signature):
    
    signature = decodeBase64(signature)
    # Load the public key
    public_key = serialization.load_pem_public_key(
        pubKey.encode("utf-8"),
        backend=default_backend()
    )

    concatenated_str = f"{id}{y0}"

    try:
        # Verify the signature
        public_key.verify(
            signature,
            concatenated_str.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=20
            ),
            hashes.SHA256()
        )
        # If verification is successful, return True
        return True
    except Exception as e:
        # If verification fails, return False
        print(f"Verification failed: {e}")
        return False


def verify_signature(public_key, id, xi, yi, i, signature):
    
    signature = decodeBase64(signature)
    # Load the public key
    public_key = serialization.load_pem_public_key(
        public_key,
        backend=default_backend()
    )

    concatenated_str = f"{id}{xi}{yi}{i}"

    try:
        # Verify the signature
        public_key.verify(
            signature,
            concatenated_str.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=20
            ),
            hashes.SHA256()
        )
        # If verification is successful, return True
        return True
    except Exception as e:
        # If verification fails, return False
        print(f"Verification failed: {e}")
        return False
