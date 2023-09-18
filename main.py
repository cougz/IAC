from fastapi import FastAPI, HTTPException, APIRouter
from pydantic import BaseModel
from decouple import config
from nginx_api import nginx_router
from hyperv_api import hyperv_router
from cosmos_api import cosmos_router
from cloudflare_api import cloudflare_router

# Instantiate FastAPI
app = FastAPI()
app.include_router(nginx_router, prefix="/nginx", tags=["nginx Config Management"])
app.include_router(hyperv_router, prefix="/hyperv", tags=["Hyper-V VM Management"])
app.include_router(cloudflare_router, prefix="/dns", tags=["DNS Management"])
app.include_router(cosmos_router, prefix="/cosmos", tags=["Cosmos DB Management"])

@app.get("/")
async def root():
    return {"Welcome to": "Infinigate Demo Center"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)