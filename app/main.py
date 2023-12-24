from fastapi import FastAPI

from app.api import health, heatpump, ventilation

app = FastAPI()
app.include_router(health.router)
app.include_router(heatpump.router)
app.include_router(ventilation.router)
