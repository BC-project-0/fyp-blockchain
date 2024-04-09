from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend
import base64
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend

def decodeBase64(base64_string):
    base64_bytes = base64_string.encode("latin-1")
    return base64.b64decode(base64_bytes)

def generate_key_pair(security_parameter="high"):
    # Determine the key size based on the security parameter
    if security_parameter == "high":
        key_size = 4096
    elif security_parameter == "medium":
        key_size = 2048
    elif security_parameter == "low":
        key_size = 1024
    else:
        raise ValueError(
            "Invalid security parameter. Use 'high', 'medium', or 'low'.")

    # Generate RSA key pair
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=key_size,
        backend=default_backend()
    )

    # Serialize private key
    private_key_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    # Get the corresponding public key
    public_key = private_key.public_key()
    public_key_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    return private_key_bytes, public_key_bytes

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
