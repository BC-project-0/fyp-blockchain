import time
from threading import Thread
from random import choices
from Blockchain import Block
import json

flag = False

# An event triggers the init_leader_election
def init_leader_election(currNode):
    if currNode.is_leader_election_happening.is_set():
        return
    currNode.is_leader_election_happening.set()
    print()
    print("I want to be the leader")
    if currNode.leader == None:  # Broadcasting message to other nodes stating this nodes wants to stand for leadere
        event,data = "Leader Election","I want to be the leader"
        currNode.send_encrypted_msg(event,data)
    time.sleep(5)  # waits for 15 seconds for replies

    # If some higher node wants to be leader then stop_leaderElection is set to True
    if not currNode.stop_leaderElection.is_set():        
            
        event,data = "Leader Elected","I am leader"
        currNode.send_encrypted_msg(event,data)  
        currNode.probability = 0;     
        print("I am the leader")

        # proceed to publish the block
        x = Thread(target=publish_block,args=(currNode,))
        x.start()
        # y = Thread(target=heartbeat,args= (currNode,))
        # y.start()

    # Clean up Code
    currNode.pool.pool = []
    currNode.stop_leaderElection.clear()
    currNode.is_leader_election_happening.clear()
    currNode.votes = 0
    currNode.leader = None    
    currNode.electionProcess = False

# Function to generate True or false based on conditional probability
def random_value_gen(node):
    if(node.probability < 50) and (node.probability + (50 / node.connections) < 50):
        node.probability += (10 / node.connections)
    num  = choices(['true','false'],[node.probability,50 - node.probability], k=5).count('true')
    ans  = num / 5 ;
    if ans < 0.7:
        return False
    else:
        return True

# to choose whether the current node standing for leader should be elected or not
def leader_election(currNode,senderNode,data):
    print()
    print("In Leader Election")
    wantToBeLeader =  random_value_gen(currNode) 
    if senderNode.id < currNode.id :
        if wantToBeLeader == True:
            init_leader_election(currNode)
    
    if wantToBeLeader == False:
        currNode.electionProcess = False

def heartbeat(currNode):
    while not currNode.published:
        print("heartbeat testing ...")
        event,data = "Heartbeat","Heartbeat from leader -> " + str(currNode.host) + ":" +  str(currNode.port)
        currNode.send_encrypted_msg(event,data)
        time.sleep(3)

def publish_block(currNode):
    pool_data = json.dumps(currNode.pool.pool)
    data = ""

    signature = currNode.get_signature(json.dumps({
        "node": str(currNode.host),
        "pool_data": pool_data,
        "data" : data
        }))
    block_data = {"pool_data": pool_data, "signature": signature, "data": data}
    event,node_data = "Block Published", json.dumps(block_data)
    currNode.send_encrypted_msg(event,node_data)
    currNode.published = True
    latest_block = currNode.blockchain.get_latest_block()
    currNode.blockchain.add_block(Block(latest_block.index + 1, str(currNode.host) + ":" +  str(currNode.port), latest_block.hash, data, signature, pool_data, [] , int(time.time())))
    print("BLOCK PUBLISHED")
    with open(f"blocks-{str(currNode.id)}.json","w") as json_file:
        blocks = []
        for current_block in currNode.blockchain.chain:
                    # Exclude hash from serialization
            block_data = current_block.__dict__.copy()
            block_data.pop('hash', None)
            blocks.append(block_data)
        json.dump(blocks, json_file, indent=4)
    # with open("./data/blocks.json", "w") as json_file:
    #     blocks = []
    #     for current_block in currNode.blockchain.chain:
    #                 # Exclude hash from serialization
    #         block_data = current_block.__dict__.copy()
    #         block_data.pop('hash', None)
    #         blocks.append(block_data)
    #     json.dump(blocks, json_file, indent=4)