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
    return {"service": "alerts_service", "status": "ok"}

# Dependency to fetch all alerts
async def get_all_alerts(route: str = None, stop: str = None):
    params = {}
    if route:
        params["filter[route]"] = route
    if stop:
        params["filter[stop]"] = stop
    return await mbta_get("/alerts", params=params)

# Dependency to fetch a specific alert by ID
async def get_alert_by_id(alert_id: str):
    return await mbta_get(f"/alerts/{alert_id}")

@app.get("/alerts")
async def read_alerts(route: str = None, stop: str = None, alerts=Depends(get_all_alerts)):
    return alerts

@app.get("/alerts/{alert_id}")
async def read_alert(alert_id: str, alert=Depends(get_alert_by_id)):
    return alert
