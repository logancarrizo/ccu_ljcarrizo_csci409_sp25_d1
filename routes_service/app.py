from fastapi import FastAPI, HTTPException
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
    return {"service": "routes_service", "status": "ok"}

@app.get("/routes")
async def get_routes():
    routes_list = []
    data = await mbta_get("/routes")
    for route in data["data"]:
        routes_list.append({
            "id": route["id"],
            "color": route["attributes"]["color"],
            "text_color": route["attributes"]["text_color"],
            "description": route["attributes"]["description"],
            "long_name": route["attributes"]["long_name"],
            "type": route["attributes"]["type"],
        })
    return {"routes": routes_list}

@app.get("/routes/{route_id}")
async def get_route(route_id: str):
    data = await mbta_get(f"/routes/{route_id}")
    route_data = data["data"]
    route = {
        "id": route_data["id"],
        "color": route_data["attributes"]["color"],
        "text_color": route_data["attributes"]["text_color"],
        "description": route_data["attributes"]["description"],
        "long_name": route_data["attributes"]["long_name"],
        "type": route_data["attributes"]["type"],
    }
    return {"routes": route}
