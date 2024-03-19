from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
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
    file: str

class StoreUserData(BaseModel):
    id: str
    data: str


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
        if verify_initial_signature(public_key, unique_id, commitment_value, signature):
            blockchain.unique_id_to_commitment_value_mapping[unique_id] = {
                "index": 1, "commitment_value": commitment_value, "public_key": public_key}
            event, data = "Registration", "{}:{}:{}".format(
                unique_id, commitment_value, public_key)
            node.send_encrypted_msg(event, data)
            node.store_user_data(unique_id,"{} registered".format(unique_id))
            node.store_otp_state()
            if(node.pool.is_limit_reached()):
                x = Thread(target=init_leader_election,args=(node,))
                x.start()
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
    fileName = body.file

    if unique_id in blockchain.unique_id_to_commitment_value_mapping:
        result = Blockchain.authenticate(
            blockchain, unique_id, old_commitment_value, new_commitment_value, index, signature, pk)
        if result == "Success":
            event, msg = "Record Update", "{}:{}:{}".format(
                unique_id, index+1, new_commitment_value)
            node.send_encrypted_msg(event, msg)
            node.store_otp_state()
            file = blockchain.get_file(unique_id, fileName)
            if file != None:
                return FileResponse(file)
            else:
                return {"message" : result}
        else:
            return {"message": result}
    else:
        return {"message": "User is not registered"}

@app.post("/data")
async def upload(body: StoreUserData):
    node.store_user_data(body.id, body.data)
    event, msg = "Transaction Pool Update", "{}:{}".format(
        body.id, body.data)
    node.send_encrypted_msg(event, msg)
    if(node.pool.is_limit_reached()):
        x = Thread(target=init_leader_election,args=(node,))
        x.start()
    return {"message": "Success"}


@app.get("/users")
async def users():
    return {"users": list(blockchain.unique_id_to_commitment_value_mapping.keys())}


@app.get("/{unique_id}/files")  # user name
async def files(unique_id: str):
    for block in blockchain.chain:
        if unique_id in block.file_mapping:
            return block.file_mapping[unique_id]
    return []


@app.post("/upload")
async def upload(file: UploadFile = File(...), id: str = Form(...)):
    unique_id = id
    uploaded_file = file

    if unique_id in blockchain.unique_id_to_commitment_value_mapping:
        await blockchain.upload(unique_id, uploaded_file)
        event,data = "File Upload" + ":" + unique_id + ":" + file.filename , blockchain.get_latest_block().base64_mapping[unique_id + ":" + file.filename]
        node.send_encrypted_msg(event,data)
        return {"message": "File uploaded"}
    else:
        return {"message": "User is not registered"}

@app.get("/{id}/files/{filename}")
async def get_file(id: str, filename: str):
    filename = blockchain.get_file(id, filename)
    if filename != None:
        return FileResponse(filename)
    else:
        return {"message": "File retrieval failed"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=80 + int(id))
