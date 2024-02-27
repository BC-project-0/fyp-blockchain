import random
import time
from threading import Thread
from random import choices

flag = False

# An event triggers the init_leader_election
def init_leader_election(currNode):
    print()
    print("I want to be the leader")
    if currNode.leader == None:  # Broadcasting message to other nodes stating this nodes wants to stand for leadere
        event,data = "Leader Election","I want to be the leader"
        currNode.send_encrypted_msg(event,data)
    time.sleep(15)  # waits for 15 seconds for replies

    # If some higher node wants to be leader then stop_leaderElection is set to True
    if not currNode.stop_leaderElection.is_set():        
            
        event,data = "Leader Elected","I am leader"
        currNode.send_encrypted_msg(event,data)  
        currNode.probability = 0;     
        print("I am the leader")

        # proceed to publish the block
        x = Thread(target=publish_block,args=(currNode,))
        y = Thread(target=heartbeat,args= (currNode,))
        x.start()
        y.start()

    # Clean up Code
    currNode.stop_leaderElection.clear()
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
    wantToBeLeader =  random_value_gen(currNode) 
    if senderNode.id < currNode.id :
        if wantToBeLeader == True:
            init_leader_election(currNode)
            currNode.electionProcess = False
    
    if wantToBeLeader == False:
        currNode.electionProcess = False
    


def heartbeat(currNode):
    while not currNode.published:
        print("heartbeat testing ...")
        event,data = "Heartbeat","Heartbeat from leader =>" + str(currNode.host) + ":" +  str(currNode.port)
        currNode.send_encrypted_msg(event,data)
        time.sleep(3)

def publish_block(currNode):
    time.sleep(15)
    event,data = "Block Published",""
    currNode.send_encrypted_msg(event,data)
    currNode.published = True
    print("BLOCK PUBLISHED")