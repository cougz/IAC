from fastapi import FastAPI, HTTPException, APIRouter
from pydantic import BaseModel
from decouple import config
import os, re, asyncio, cloudflare
from nginx_api import nginx_router

# Instantiate FastAPI
app = FastAPI()
app.include_router(nginx_router, prefix="/nginx", tags=["nginx Config Updates"])

class WaitGuacamoleResponse(BaseModel):
    guacamole_ip: str





# Use the routers in the main app
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)