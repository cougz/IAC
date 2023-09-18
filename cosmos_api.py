from azure.cosmos.aio import CosmosClient
from azure.cosmos import PartitionKey, exceptions
from fastapi import FastAPI, HTTPException, APIRouter, Request
from fastapi.encoders import jsonable_encoder
from typing import List
from models import User, Gender, Role, UserUpdateRequest
from uuid import UUID
import requests
from decouple import config

# Read Cosmos credentials from environment variables using decouple
container = config('COSMOS_CONTAINER_NAME')
key = config('COSMOS_KEY')
uri = config('COSMOS_URI')
db = config('COSMOS_DATABASE_NAME')

cosmos_router = APIRouter()

async def startup_db_client():
     cosmos_router.cosmos_client = CosmosClient(uri, credential = key)
     await get_or_create_db(db)
     await get_or_create_container(container)

async def get_or_create_db(db_name):
    try:
        cosmos_router.database  = cosmos_router.cosmos_client.get_database_client(db_name)
        return await cosmos_router.database.read()
    except exceptions.CosmosResourceNotFoundError:
        print("Creating database")
        return await cosmos_router.cosmos_client.create_database(db_name)
     
async def get_or_create_container(container_name):
    try:        
        cosmos_router.user_items_container = cosmos_router.database.get_container_client(container_name)
        return await cosmos_router.user_items_container.read()   
    except exceptions.CosmosResourceNotFoundError:
        print("Creating container with id as partition key")
        return await cosmos_router.database.create_container(id=container_name, partition_key=PartitionKey(path="/id"))
    except exceptions.CosmosHttpResponseError:
        raise

#Request routing
@cosmos_router.on_event("startup")
async def startup_db_client():
     cosmos_router.cosmos_client = CosmosClient(uri, credential = key)
     await get_or_create_db(db)
     await get_or_create_container(container)

@cosmos_router.post("/users", response_model=User)
async def register_cosmos_user(request: Request, user_item: User):
    user_item = jsonable_encoder(user_item)
    new_user = await request.app.user_items_container.create_item(user_item)
    return new_user

@cosmos_router.get("/users", response_description="List of all Cosmos users", response_model=List[User])
async def list_cosmos_users(request: Request):
    users = [user async for user in request.app.user_items_container.read_all_items()]
    return users