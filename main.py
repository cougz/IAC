from fastapi import FastAPI, HTTPException, APIRouter
from pydantic import BaseModel
from decouple import config
import os, re, asyncio, cloudflare
from nginx_api import nginx_router
from hyperv_api import hyperv_router
from cloudflare_api import cloudflare_router

# Instantiate FastAPI
app = FastAPI()
app.include_router(nginx_router, prefix="/nginx", tags=["nginx Config Updates"])
app.include_router(hyperv_router, prefix="/hyperv", tags=["Hyper-V Updates"])
app.include_router(cloudflare_router, prefix="/dns", tags=["DNS Updates"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)