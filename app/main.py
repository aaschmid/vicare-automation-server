from fastapi import FastAPI

from app.api import health, heatpump

app = FastAPI()
app.include_router(health.router)
app.include_router(heatpump.router)
