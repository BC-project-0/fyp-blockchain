import hashlib
import json
from utils import verify_signature
import time
import base64
from base64 import b64encode,b64decode
from Crypto.Cipher import ChaCha20_Poly1305

class Block:
    def __init__(self, index, leader_ip, previous_hash, data, digital_signature, user_data, logs, timestamp):
        self.index = index
        self.leader_ip = leader_ip
        self.previous_hash = previous_hash
        self.data = data
        self.digital_signature = digital_signature
        self.user_data = user_data
        self.logs = logs
        self.timestamp = timestamp
        self.file_mapping = dict()
        self.base64_mapping = dict()
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        block_data = {
            "index": self.index,
            "leader_ip": self.leader_ip,
            "previous_hash": self.previous_hash,
            "data": self.data,
            "digital_signature": self.digital_signature,
            "user_data": self.user_data,
            "logs": self.logs,
            "timestamp": self.timestamp,
            "file_mapping": str(self.file_mapping),
            "base64_mapping": str(self.base64_mapping)
        }
        block_string = json.dumps(block_data, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()

    def print_block(self):
        block_data = json.dumps(self.__dict__, sort_keys=True, indent=4)
        print(block_data)


# Transaction contains the unique_id ,data and timestamp
class TransactionPool:
    def __init__(self):
        self.pool = []
        self.max_no_of_transaction = 3
   
    def add_user_data_to_pool(self,unique_id, data):
        self.pool.append({"unique_id": unique_id, "data": data, "timestamp": int(time.time())})
    
    def is_limit_reached(self):
        if(len(self.pool) >= self.max_no_of_transaction):
            return True
        else:
            return False

class Blockchain:
    def __init__(self):
        self.chain = []
        self.create_genesis_block()
        self.unique_id_to_commitment_value_mapping = dict()

    def create_genesis_block(self):
        genesis_block = Block(0, "0", "0", "Genesis Block",
                              "0", "Genesis User Data", [], 0)
        self.chain.append(genesis_block)

    def get_latest_block(self):
        return self.chain[-1]

    def add_block(self, new_block):
        new_block.previous_hash = self.get_latest_block().hash
        new_block.hash = new_block.calculate_hash()
        self.chain.append(new_block)

    def is_chain_valid(self):
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]

            if current_block.hash != current_block.calculate_hash():
                print(current_block.hash, current_block.calculate_hash())
                return False

            if current_block.previous_hash != previous_block.hash:
                return False

        return True

    def print_chain(self):
        for block in self.chain:
            block.print_block()

    def authenticate(self, id, xi, yi, i, s, pk):
        record = self.unique_id_to_commitment_value_mapping[id]
        j = record["index"]
        y_prev = record["commitment_value"]
        pk_record = record["public_key"]
        if y_prev != xi:
            return "Wrong Commitment Value"
    
        if pk != pk_record:
            return "Wrong Public Key"
        
        if i == j:
            if y_prev == xi and verify_signature(pk.encode("utf-8"),id,xi,yi,i,s):
                record = {"index": j + 1,"commitment_value": yi, "public_key": pk}
                self.unique_id_to_commitment_value_mapping[id] = record
                return "Success"
            else:
                # The client should only increment the index value, not the server
                return "Auth failed"
                # record = {"index": j + 1,"commitment_value": y_prev, "public_key": pk}
                # self.unique_id_to_commitment_value_mapping[id] = record
        else:
            return "Need Sync"
            # Sync should take place
            # record = {"index": j + 1,"commitment_value": y_prev, "public_key": pk}
            # self.unique_id_to_commitment_value_mapping[id] = record
        
    async def upload(self, id, file, key):
        header = b"header"
        cipher = ChaCha20_Poly1305.new(key=key)
        cipher.update(header)
        contents = await file.read()
        encoded_contents = base64.b64encode(contents)  # Decode bytes to string
        ciphertext,tag = cipher.encrypt_and_digest(encoded_contents)
        jk = [ 'nonce', 'header', 'ciphertext', 'tag' ]
        jv = [ b64encode(x).decode('utf-8') for x in (cipher.nonce, header, ciphertext, tag) ]
        result = json.dumps(dict(zip(jk, jv)))
        block = self.get_latest_block()
        if block is not None:
            if id not in block.file_mapping:
                block.file_mapping[id] = [file.filename]
            else:
                block.file_mapping[id].append(file.filename)
            block.base64_mapping[id + ":" + file.filename] = result
            block.hash = block.calculate_hash()

            # Serialize the blockchain to JSON and write to file
            with open("./data/blocks.json", "w") as json_file:
                blocks = []
                for current_block in self.chain:
                    # Exclude hash from serialization
                    block_data = current_block.__dict__.copy()
                    block_data.pop('hash', None)
                    blocks.append(block_data)
                json.dump(blocks, json_file, indent=4)     
        else:
            print("Error: Could not get the latest block.")
            return None

    def get_file(self,id,filename, key):
        for block in self.chain:
            if id + ":" +filename in block.base64_mapping:
                b64 = json.loads(block.base64_mapping[id+":"+filename])
                jk = [ 'nonce', 'header', 'ciphertext', 'tag' ]
                jv = {k:b64decode(b64[k]) for k in jk}
                cipher = ChaCha20_Poly1305.new(key=key, nonce=jv['nonce'])
                cipher.update(jv['header'])
                decrypted_contents = cipher.decrypt_and_verify(jv['ciphertext'], jv['tag'])
                decoded_contents = base64.b64decode(decrypted_contents)
                print("File Found !!!!")
                with open(filename, 'wb') as file:
                    file.write(decoded_contents)
                return filename
        return None