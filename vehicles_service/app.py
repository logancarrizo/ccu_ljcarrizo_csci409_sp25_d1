from fastapi import FastAPI, Depends, HTTPException
import httpx
from typing import Dict, Any, Optional

API_KEY = "b320b4d35b154cb784259e15d9fa5e78"
ENDPOINT_URL = "https://api-v3.mbta.com/"

app = FastAPI()

def _auth_params() -> Dict[str, str]:
    return {"api_key": API_KEY} if API_KEY else {}

async def mbta_get(path: str, params: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    params = params or {}
    params.update(_auth_params())
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.get(f"{ENDPOINT_URL}{path}", params=params)
        if r.status_code == 404:
            raise HTTPException(status_code=404, detail="Not found")
        r.raise_for_status()
        return r.json()

@app.get("/")
async def health():
    return {"service": "vehicles_service", "status": "ok"}

async def get_all_vehicles(route: str = None, revenue: str = None):
    params = {}
    if route:
        params["filter[route]"] = route
    if revenue:
        params["filter[revenue]"] = revenue
    return await mbta_get("/vehicles", params=params)

async def get_vehicle_by_id(vehicle_id: str):
    return await mbta_get(f"/vehicles/{vehicle_id}")

@app.get("/vehicles")
async def read_vehicles(route: str = None, revenue: str = None, vehicles=Depends(get_all_vehicles)):
    return vehicles

@app.get("/vehicles/{vehicle_id}")
async def read_vehicle(vehicle_id: str, vehicle=Depends(get_vehicle_by_id)):
    return vehicle
