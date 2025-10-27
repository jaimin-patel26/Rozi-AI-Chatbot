from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app import models, database
from app.routes import router
import os

app = FastAPI()

#ALLOWED_IPS = {"13.41.216.79", "18.132.181.46", "13.204.35.77","15.207.3.181","13.42.143.94","122.162.239.147"}
#@app.middleware("http")
#async def ip_whitelist_middleware(request: Request, call_next):
    #client_ip = request.headers.get("X-Forwarded-For", request.client.host)
    #client_ip = client_ip.split(",")[0].strip()

   # if client_ip not in ALLOWED_IPS:
  #      raise HTTPException(status_code=403, detail="Forbidden: IP not allowed")

 #   response = await call_next(request)
#    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

models.Base.metadata.create_all(bind=database.engine)
PHOTO_UPLOAD_DIR = "photo_uploads"

app.include_router(router)
app.mount("/files", StaticFiles(directory=PHOTO_UPLOAD_DIR), name="files")
