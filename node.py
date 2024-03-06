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

blockchain = node.blockchain

while True:
    print("\n\n1) Start Leader Election \n2) Check Prev leader\n3) Terminate Master\n4) Print all nodes \n5) Check Keys \n6) Print Blockchain\n7) Register\n\n")
    
    choice = int(input())
    if choice == 1:
        temp = node.prevLeader
        init_leader_election(node)
    if choice == 2:
        print("Prev Leader",end="")
        print(node.prevLeader)
    if choice == 3:
        node.stop()
        break
    if choice == 4:
        print(node.all_nodes)
    if choice == 5:
        print("Connected Keys:")
        print(node.connected_keys)
    if choice == 6:
        print("Blockchain :\n")
        node.blockchain.print_chain()
    if choice == 7:
        unique_id = input("Enter Unique Id :")
        commitment_value = input("Enter Commitment value :")
        public_key = input("Enter Public Key :")
        if unique_id in blockchain.unique_id_to_commitment_value_mapping:
            print("User Already Exists")
        else:
            blockchain.unique_id_to_commitment_value_mapping[unique_id] = {"index" : 0 , "commitment_value" : commitment_value , "public_key" : public_key}
            event,data = "Registration","{}:{}:{}".format(unique_id,commitment_value,public_key)
            node.send_encrypted_msg(event,data)
            print("User Registered")
    if choice == 8:
        unique_id = input("Enter Unique Id :")
        otp = input("Enter OTP :")
        signature = input("Enter Signature :")
        index = int(input("Enter Index :"))
        if unique_id in blockchain.unique_id_to_commitment_value_mapping:
            record = blockchain.unique_id_to_commitment_value_mapping[unique_id]
            previous_commitment_value = record["commitment_value"]
            index = record["index"]
            result = Blockchain.authenticate(blockchain,unique_id,previous_commitment_value,otp,index,signature)
            if result == index + 1 :
                event,msg = "Record Update","{}:{}:{}".format(unique_id,result,otp)
                node.send_encrypted_msg(event,msg)
                print("Authentication Successfull")
            elif result: 
                print(result)
                print("Out of Sync")
            else:
                print("Authentication Failed")
        else:
            print("User is not registered")
    if choice == 0:
        print(node.blockchain.unique_id_to_commitment_value_mapping)