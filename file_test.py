from Blockchain import Blockchain
from Blockchain import Block
import json


blocks = []
with open("blockchain_state.json","r") as file:
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

with open("blocks.json","w") as json_file:
            new_blocks = []
            for current_block in blocks :
                new_blocks.append(current_block.__dict__)
            json.dump(new_blocks,json_file,indent=4)