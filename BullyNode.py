from p2pnetwork.node import Node
import threading
from BullyAlgo import *
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes
from Crypto.Cipher import AES, PKCS1_OAEP
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.exceptions import InvalidSignature
import base64
import os
from Blockchain import Block
from Blockchain import Blockchain
import json
from Blockchain import TransactionPool


class BullyNode(Node):

    def __init__(self, host, port, id=None, callback=None, max_connections=0, connections=10):
        super(BullyNode, self).__init__(
            host, port, id, callback, max_connections)
        self.connections = connections
        self.probability = 50 - ((int(id)*8.1) % 50)
        self.blockchain = Blockchain()
        self.pool = TransactionPool()
        # key pair generation
        key = RSA.generate(1024)  # keys[0] = pub key , keys[1] = pvt key
        self.keys = {"public_key": key.publickey().export_key(),
                     "private_key": key.export_key()}
        self.connected_keys = {}

        try:
            with open("./data/internal_state.json","r") as file:
                self.blockchain.unique_id_to_commitment_value_mapping = json.load(file)
        except IOError as e:
            print(f"Error reading data: {e}")

        try:
            with open("./data/blocks.json","r") as file:
                blocks = []
                data = json.load(file)
                for i in data :
                    json_dict = i
                    index = json_dict.get("index")
                    leader_ip = json_dict.get("leader_ip")
                    previous_hash = json_dict.get("previous_hash")
                    data = json_dict.get("data")
                    digital_signature = json_dict.get("digital_signature")
                    user_data = json_dict.get("user_data")
                    logs = json_dict.get("logs")
                    timestamp = json_dict.get("timestamp")
                    block = Block(index,leader_ip,previous_hash,data,digital_signature,user_data,logs,timestamp)
                    block.base64_mapping = json_dict["base64_mapping"]
                    block.file_mapping = json_dict["file_mapping"]
                    blocks.append(block)
                self.blockchain.chain = blocks
        except IOError as e:
            print(f"Error reading data :{e}")            

    # used to identity whether current node is contesting for leader or not
    electionProcess = False
    votes = 0
    stop_leaderElection = threading.Event()
    is_leader_election_happening = threading.Event();
    leader = None
    prevLeader = None
    published = False
    leader_ip = None

    def node_message(self, node, data):
        def decrypt(self, data):
            data = base64.b64decode(bytes(data, 'utf8'))
            private_key = self.keys['private_key']

            file_temp = open("temp-{}.bin".format(self.id), 'wb')
            file_temp.write(data)
            file_temp.close()

            file_temp = open("temp-{}.bin".format(self.id), "rb")

            priKey = RSA.import_key(private_key)
            enc_session_key, nonce, tag, ciphertext = [
                file_temp.read(x) for x in (priKey.size_in_bytes(), 16, 16, -1)]

            cipher_rsa = PKCS1_OAEP.new(priKey)
            session_key = cipher_rsa.decrypt(enc_session_key)

            cipher_aes = AES.new(session_key, AES.MODE_EAX, nonce)
            plain_text = cipher_aes.decrypt_and_verify(ciphertext, tag)
            file_temp.close()

            return plain_text.decode("utf-8")

        if self.leader == None:
            if node.id > self.id and data['event'] == "Leader Election" and decrypt(self, data['message']) == "I want to be the leader":
                print("Higher node "+str(node.id)+" to be leader")  # debug
                self.stop_leaderElection.set()
            elif data['event'] == "Leader Election" and decrypt(self, data['message']) == "I want to be the leader":
                if self.electionProcess == False:
                    self.electionProcess = True
                    x = threading.Thread(
                        target=leader_election, args=(self, node, data,))
                    x.start()

        if data['event'] == "Key Exchange Request":
            self.connected_keys[node.id] = (RSA.import_key(data["message"]))

            pk = open("pk"+str(self.id)+".pem", "wb")
            pk.write(self.keys["public_key"])
            pk.close()
    # Broadcasting public keys to all other nodes connected with us
            key_msg = {"event": "Key Exchange Reply",
                       "message": open("pk"+str(self.id)+".pem").read()}
            self.send_to_node(node, key_msg)
            os.remove("pk"+str(self.id)+".pem")

        if data['event'] == "Key Exchange Reply":
            self.connected_keys[node.id] = (RSA.import_key(data["message"]))
            return

        # Once leader is set then other nodes's response are invalid
        if data['event'] == "Leader Elected" and decrypt(self, data['message']) == "I am leader":
            print("From "+str(node.id)+" : It is the leader")
            self.prevLeader = node
            self.leader = node
            self.leader_ip = str(node.host) + ":" + str(node.port)
            self.votes = 0
            self.is_leader_election_happening.clear()
            return

        # heartbeat message printing
        if data["event"] == "Heartbeat":
            print(decrypt(self, data["message"]))
            return
            
        if data["event"] == "Record Update":
            unique_id , index , commitment_value = (decrypt(self,data["message"])).split(":")
            record = self.blockchain.unique_id_to_commitment_value_mapping[unique_id]
            record["index"] = int(index)
            record["commitment_value"] = commitment_value
            self.blockchain.unique_id_to_commitment_value_mapping[unique_id] = record
            print("Record Updated")
            return 
        
        # After block is published .. New message is sent to reset leader
        if data['event'] == "Block Published":
            latest_block = self.blockchain.get_latest_block()
            received_data = json.loads(decrypt(self,data["message"]))
            # if not self.verify_signature(node,received_data["pool_data"],received_data["data"],received_data["signature"]) == False:
            #     print("Recevied Block Signature invalid")
            #     return
            new_block = Block(latest_block.index + 1, self.leader_ip,
                              latest_block.hash, received_data["data"], received_data["signature"],received_data["pool_data"], [] , int(time.time()))
            self.blockchain.add_block(new_block)
            self.blockchain.logs = []
            print("Block Published by Leader")
            self.leader = None
            self.electionProcess = False
            self.stop_leaderElection.clear()
            self.published = False
            with open("blocks.json", "w") as json_file:
                blocks = []
                for current_block in self.blockchain.chain:
                    # Exclude hash from serialization
                    block_data = current_block.__dict__.copy()
                    block_data.pop('hash', None)
                    blocks.append(block_data)
                json.dump(blocks, json_file, indent=4)
            return
        
        if data["event"] == "Registration":
            unique_id , commitment_value , public_key = (decrypt(self,data["message"])).split(":")
            self.blockchain.unique_id_to_commitment_value_mapping[unique_id] = {"index" : 1 , "commitment_value" : commitment_value , "public_key" : public_key}
            print("User Registered")
            return
    
        if data['event'] == "Transaction Pool Update":
            unique_id, txn = (decrypt(self,data["message"])).split(":")
            self.store_user_data(unique_id, txn)
    
        if data['event'].split(":")[0] == "File Upload":
            event =  data['event'].split(":")
            unique_id = event[1]
            filename = event[2]
            base64_data = decrypt(self,data['message'])
            if unique_id not in self.blockchain.get_latest_block().file_mapping:
                self.blockchain.get_latest_block().file_mapping[unique_id] = [filename]
            else:
                self.blockchain.get_latest_block().file_mapping[unique_id].append(filename)
            self.blockchain.get_latest_block().base64_mapping[unique_id + ":" + filename] = base64_data
            self.blockchain.get_latest_block().hash = self.blockchain.get_latest_block().calculate_hash()

    def store_user_data(self,unique_id,data):
        pool = self.pool
        pool.add_user_data_to_pool(unique_id,data)
    
    def store_otp_state(self):
        with open("internal_state.json","w") as file:
            json.dump(self.blockchain.unique_id_to_commitment_value_mapping,
                          file,indent=4) 

    def node_disconnect_with_outbound_node(self, node):
        print("Diconnecting from ->", node)
        return

    def send_encrypted_msg(self, event, msg):
        for node in self.all_nodes:
            session_key = get_random_bytes(16)
            pk = self.connected_keys[node.id]
            cipher_rsa = PKCS1_OAEP.new(pk)
            enc_session_key = cipher_rsa.encrypt(session_key)
            cipher_aes = AES.new(session_key, AES.MODE_EAX)
            ciphertext, tag = cipher_aes.encrypt_and_digest(
                msg.encode("utf-8"))

            file_out = open("encrypted_data.bin", "wb")
            [file_out.write(x) for x in (enc_session_key,
                                         cipher_aes.nonce, tag, ciphertext)]
            file_out.close()

            txt = open("encrypted_data.bin", "rb").read()
            # Convterting to string using base64
            b64_txt = str(base64.b64encode(txt), 'utf8')
            data = {"event": event, "message": b64_txt}
            self.send_to_node(node, data)
            # print("sent")
        return

    def get_signature(self,data):
        private_key = self.keys['private_key']
        priKey = serialization.load_pem_private_key(private_key, password=None)
        bytes_data = data.encode('utf-8')

        hasher = hashes.Hash(hashes.SHA256())
        hasher.update(bytes_data)
        digest = hasher.finalize()
        sig = priKey.sign(
            digest,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=20
            ),
            hashes.SHA256()
        )
        return sig.decode("latin-1")
    
    def verify_signature(self,node,pool_data,data,signature):
        print("Verify")
        data = json.dumps({
        "node": str(node.host),
        "pool_data": pool_data,
        "data" : data
        }).encode()

        pk = self.connected_keys[node.id]
        pubKey = serialization.load_pem_public_key(pk.export_key())
        try:
            pubKey.verify(
                signature.encode("latin-1"),
                data,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=20
                ),
                hashes.SHA256()
            )
            return True
        except InvalidSignature as e:
            print(e)
            return False