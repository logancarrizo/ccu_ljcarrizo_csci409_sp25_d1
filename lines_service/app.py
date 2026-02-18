from fastapi import FastAPI, HTTPException, Depends
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
