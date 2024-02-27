import sys
import time
from BullyNode import BullyNode
from BullyAlgo import *
import os

id = sys.argv[1]
connections = int(sys.argv[2])
print('Node '+id)
node = BullyNode("127.0.0.1", 8000+int(id), id = id, connections = connections)
node.start()
time.sleep(5)

for i in range(connections):
    if i != id:
        node.connect_with_node('127.0.0.1', 8000+i)

pk = open("pk"+str(node.id)+".pem","wb")
pk.write(node.keys["public_key"])
pk.close()
# Broadcasting public keys to all other nodes connected with us
key_msg = {"event":"Key Exchange Request","message":open("pk"+str(node.id)+".pem").read()}
node.send_to_nodes(key_msg)
os.remove("pk"+str(node.id)+".pem")


while True:
    print("\n\n1) Start Leader Election \n2) Check Prev leader\n3) Terminate Master\n4) Print all nodes \n5) Check Keys \n6) Print Blockchain\n\n")
    
    choice = int(input())
    if choice==1:
        temp = node.prevLeader
        init_leader_election(node)
    if choice==2:
        print("Prev Leader",end="")
        print(node.prevLeader)
    if choice==3:
        node.stop()
        break
    if choice==4:
        print(node.all_nodes)
    if choice==5:
        print("Connected Keys:")
        print(node.connected_keys)
    if choice==6:
        print("Blockchain :\n")
        node.blockchain.print_chain()
