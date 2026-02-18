from fastapi import FastAPI, Depends, HTTPException
import httpx
from typing import Dict, Any, Optional
import os
from fastapi.security import APIKeyHeader

API_KEY = "b320b4d35b154cb784259e15d9fa5e78"
ENDPOINT_URL = "https://api-v3.mbta.com/"

# ---- API Key Security for ALL endpoints ----
CLIENT_API_KEY = os.getenv("CLIENT_API_KEY", "changeme123")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def require_api_key(api_key: str = Depends(api_key_header)):
    if api_key != CLIENT_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")

app = FastAPI(dependencies=[Depends(require_api_key)])

def _auth_params() -> Dict[str, str]:
    return {"api_key": API_KEY} if API_KEY else {}

async def mbta_get(path: str, params: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    params = params or {}
    params.update(_auth_params())
    async with httpx.AsyncClient(timeout=20) as client:
        try:
            r = await client.get(f"{ENDPOINT_URL}{path}", params=params)
            if r.status_code == 404:
                raise HTTPException(status_code=404, detail="Not found")
            r.raise_for_status()
            return r.json()

        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=e.response.text)

        except httpx.RequestError as e:
            raise HTTPException(status_code=502, detail=f"Upstream request failed: {str(e)}")

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
