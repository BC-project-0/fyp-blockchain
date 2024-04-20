import random
import string
import requests
import subprocess
import time
import json
import hashlib
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import hashlib
import base64
import csv

USERNAME_LENGTH = 10
DELAY = 10

def generate_signature(id,xi,yi,i,sk,key):
    concatenated_str = f"{id}{xi}{yi}{i}"
    # Load the private key
    private_key = serialization.load_pem_private_key(
        sk,
        password=None,
        backend=default_backend()
    )

    # Sign the concatenated string using the private key
    signature = private_key.sign(
        concatenated_str.encode(),
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=20
        ),
        hashes.SHA256()
    )

    return signature

def compute_initial_commitment(id, i, pw, sk):
    # Concatenate id, i, pw, and sk
    concatenated_str = f"{id}{i}{pw}{sk}"

    # Apply a hypothetical hash function (replace with a secure hash function like SHA-256)
    initial_commitment = hashlib.sha256(concatenated_str.encode()).hexdigest()

    return initial_commitment

def generate_initial_signature(sk, id, y0 , key):
    concatenated_str = f"{id}{y0}"
    # Load the private key
    private_key = serialization.load_pem_private_key(
        sk,
        password=None,
        backend=default_backend()
    )

    # Sign the concatenated string using the private key
    signature = private_key.sign(
        concatenated_str.encode(),
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=20
        ),
        hashes.SHA256()
    )

    return signature

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

def run(N):
    for i in range(N):
        command = "python3 nodev2.py {} {}".format(i,N)
        subprocess.Popen(['osascript', '-e', 'tell application "System Events" to keystroke "`" using {control down, shift down}'])
        time.sleep(0.5)
        print("Executing command : ", command)
        subprocess.Popen(['osascript', '-e', f'tell application "System Events" to tell process "Visual Studio Code" to keystroke "{command}\\n"'])
        time.sleep(0.5)

def generate_random_username(n):
    characters = string.ascii_letters + string.digits
    random_string = ''.join(random.choice(characters) for _ in range(n))
    return random_string

N = int(input("Enter number of nodes : "))
U = int(input("Enter number of users : "))

run(N)


time.sleep(DELAY)

users = [generate_random_username(USERNAME_LENGTH) for i in range(U)]
nodes = [80 + i for i in range(N)]

keys = dict()

# fetch key pair
for user in users:
    sk,pk = generate_key_pair(random.choice(["high","medium","low"]))
    keys[user] = {
        "privateKey" : sk,
        "publicKey" : pk
    }

# register users
for user in users:
    public_key = keys[user]["publicKey"]
    private_key = keys[user]["privateKey"]
    y0 = compute_initial_commitment(user,0,'1234',private_key)
    signature = generate_initial_signature(private_key,user,y0,"1234")
    body = {
        'id' : user,
        'commitment_value' : y0,
        'public_key' : public_key.decode('utf-8'),
        'signature' : base64.b64encode(signature).decode('latin-1')
    }
    headers = {
    'Content-Type': 'application/json',
    }
    response = requests.post('http://localhost:{}/register'.format(str(random.choice(nodes))) , json = body , headers=headers)
    time.sleep(DELAY)

TRANSACTIONS = 100

FILE_PATH = 'sample-{}.txt'

content = None

with open('sample.txt', 'r') as input_file:
    # Read the content of the input file
    content = input_file.read()

for i in range(TRANSACTIONS):
    with open(FILE_PATH.format(str(i)), 'w') as output_file:
        output_file.write(content)
    payload = {'id': random.choice(users)}
    files=[('file',(FILE_PATH.format(str(i)),open(FILE_PATH.format(str(i)),'rb'),'text/plain'))]
    headers = {}
    response = requests.request("POST", 'http://localhost:{}/upload'.format(str(random.choice(nodes))), headers=headers, data=payload, files=files)
    time.sleep(DELAY)


while True:
    try:
        choice = input("CMD : ")
        if choice == "1":
            id = input("id : ")
            old_otp = input("old otp : ")
            index = int(input("index : "))
            new_otp = compute_initial_commitment(id,index,'1234',private_key)
            signature = generate_signature(id,old_otp,new_otp,index,keys[id]["privateKey"],None)
            public_key = keys[id]["publicKey"]
            headers = {
                'Content-Type': 'application/json'
            }
            file = input("file : ")
            payload = {
                "old_commitment_value" : old_otp,
                "new_commitment_value" : new_otp,
                "signature" : base64.b64encode(signature).decode('latin-1'),
                "file" : file,
                "index" : index,
                "id" : id,
                "pk" : public_key.decode('utf-8')
            }
            print(json.dumps(payload,indent=4))
            print()
            print()
        else:
            exit(1)
    except Exception:
        pass