import hashlib
import json
import time


class Block:
    def __init__(self, index, leader_ip, previous_hash, data, digital_signature, user_data, logs):
        self.index = index
        self.leader_ip = leader_ip
        self.previous_hash = previous_hash
        self.data = data
        self.digital_signature = digital_signature
        self.user_data = user_data
        self.logs = logs
        self.timestamp = time.time()
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
            "timestamp": self.timestamp
        }
        block_string = json.dumps(block_data, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()

    def print_block(self):
        block_data = json.dumps(self.__dict__, sort_keys=True, indent=4)
        print(block_data)


class Blockchain:
    def __init__(self):
        self.chain = []
        self.create_genesis_block()

    def create_genesis_block(self):
        genesis_block = Block(0, "0", "0", "Genesis Block",
                              "0", "Genesis User Data", "Genesis Logs")
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
