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
    return {"service": "lines_service", "status": "ok"}

@app.get("/lines")
async def get_lines():
    lines_list = []
    data = await mbta_get("/routes")
    for route in data["data"]:
        lines_list.append({
            "id": route["id"],
            "text_color": route["attributes"]["text_color"],
            "short_name": route["attributes"].get("short_name"),
            "long_name": route["attributes"]["long_name"],
            "color": route["attributes"]["color"],
        })
    return {"lines": lines_list}

@app.get("/lines/{line_id}")
async def get_line(line_id: str):
    data = await mbta_get(f"/routes/{line_id}")
    line_data = data["data"]
    line = {
        "id": line_data["id"],
        "text_color": line_data["attributes"]["text_color"],
        "short_name": line_data["attributes"].get("short_name"),
        "long_name": line_data["attributes"]["long_name"],
        "color": line_data["attributes"]["color"],
    }
    return {"lines": line}
