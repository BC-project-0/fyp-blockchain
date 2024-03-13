from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
import sys
import time
import os
from BullyNode import BullyNode
from BullyAlgo import *
from Blockchain import Blockchain
from starlette.responses import FileResponse
from utils import verify_initial_signature
from utils import verify_signature


class RegisterPayload(BaseModel):
    id: str
    commitment_value: str
    public_key: str
    signature: str


class AuthenticationPayload(BaseModel):
    id: str
    old_commitment_value: str
    new_commitment_value: str
    signature: str
    index: int
    pk: str


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

id = sys.argv[1]
connections = int(sys.argv[2])
print('Node '+id)
node = BullyNode("127.0.0.1", 8000+int(id), id=id, connections=connections)
node.start()
time.sleep(5)

pk = open("pk"+str(node.id)+".pem", "wb")
pk.write(node.keys["public_key"])
pk.close()
key_msg = {"event": "Key Exchange Request",
           "message": open("pk"+str(node.id)+".pem").read()}
node.send_to_nodes(key_msg)
os.remove("pk"+str(node.id)+".pem")

blockchain = node.blockchain

for i in range(connections):
    if i != id:
        node.connect_with_node('127.0.0.1', 8000+i)


@app.get("/")
async def root():
    return {"message": "Hello, World!"}


@app.get("/blockchain")
async def get_blockchain():
    return blockchain


@app.get("/stop")
async def stop():
    node.stop()
    return {"message": "Node Stopped"}


@app.post("/register")
async def registration(body: RegisterPayload):
    unique_id = body.id
    commitment_value = body.commitment_value
    public_key = body.public_key
    signature = body.signature
    if unique_id in blockchain.unique_id_to_commitment_value_mapping:
        return {"message": "User Already Exists"}
    else:
        if(verify_initial_signature(public_key,unique_id,commitment_value,signature)):
            blockchain.unique_id_to_commitment_value_mapping[unique_id] = {
                "index": 1, "commitment_value": commitment_value, "public_key": public_key}
            event, data = "Registration", "{}:{}:{}".format(
                unique_id, commitment_value, public_key)
            node.send_encrypted_msg(event, data)
            return {"message": "User Registered"}
        else:
            return {"message": "User Could not be registered"}


@app.get("/authenticate")
async def authenticateFrontend():
    return FileResponse("authenticate.html")

@app.post("/authenticate")
async def authentication(body: AuthenticationPayload):
    unique_id = body.id
    old_commitment_value = body.old_commitment_value
    new_commitment_value = body.new_commitment_value
    signature = body.signature
    index = body.index
    pk = body.pk
    if verify_signature(pk.encode("utf-8"),unique_id,old_commitment_value,new_commitment_value,index,signature) == False: 
        return {"message": "User Authentication Failed"}

    if unique_id in blockchain.unique_id_to_commitment_value_mapping:
        result = Blockchain.authenticate(
            blockchain, unique_id, old_commitment_value, new_commitment_value, index, signature)
        if result == index + 1:
            event, msg = "Record Update", "{}:{}:{}".format(
                unique_id, result, new_commitment_value)
            node.send_encrypted_msg(event, msg)
            return {"message": "User Authentication Success", "index": result}
        else:
            return {"message": "User Authentication Failed", "index": result}
    else:
        return {"message": "User is not registered", "index": result}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=80 + int(id))
