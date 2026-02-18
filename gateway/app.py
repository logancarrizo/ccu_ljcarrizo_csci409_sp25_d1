from fastapi import FastAPI, Request, HTTPException, Depends
import httpx
import os
from fastapi.security import APIKeyHeader

# ---- API Key Security for ALL gateway endpoints ----
CLIENT_API_KEY = os.getenv("CLIENT_API_KEY", "changeme123")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def require_api_key(api_key: str = Depends(api_key_header)):
    if api_key != CLIENT_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")

app = FastAPI(dependencies=[Depends(require_api_key)])

SERVICE_MAP = {
    "routes": "http://127.0.0.1:8001",
    "lines": "http://127.0.0.1:8002",
    "alerts": "http://127.0.0.1:8003",
    "vehicles": "http://127.0.0.1:8004",
}

@app.get("/")
async def root():
    return {"message": "MBTA API Gateway (proxy)", "services": SERVICE_MAP}

async def _proxy(service_name: str, path: str, request: Request):
    if service_name not in SERVICE_MAP:
        raise HTTPException(status_code=404, detail="Service not found")

    base = SERVICE_MAP[service_name]

    # Forward query params exactly as received
    params = dict(request.query_params)

    # Forward the request to the microservice
    url = f"{base}{path}"

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.get(url, params=params)
        except httpx.RequestError as e:
            # microservice offline / connection issue
            raise HTTPException(status_code=502, detail=f"Upstream service unreachable: {str(e)}")

    # Pass through status code + JSON body
    if resp.status_code == 404:
        raise HTTPException(status_code=404, detail="Not found")

    try:
        resp.raise_for_status()
    except httpx.HTTPStatusError as e:
        # pass through upstream HTTP errors instead of crashing
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)

    return resp.json()

# ROUTES service
@app.get("/routes")
async def gateway_routes(request: Request):
    return await _proxy("routes", "/routes", request)

@app.get("/routes/{route_id}")
async def gateway_route_by_id(route_id: str, request: Request):
    return await _proxy("routes", f"/routes/{route_id}", request)

# LINES service
@app.get("/lines")
async def gateway_lines(request: Request):
    return await _proxy("lines", "/lines", request)

@app.get("/lines/{line_id}")
async def gateway_line_by_id(line_id: str, request: Request):
    return await _proxy("lines", f"/lines/{line_id}", request)

# ALERTS service
@app.get("/alerts")
async def gateway_alerts(request: Request):
    return await _proxy("alerts", "/alerts", request)

@app.get("/alerts/{alert_id}")
async def gateway_alert_by_id(alert_id: str, request: Request):
    return await _proxy("alerts", f"/alerts/{alert_id}", request)

# VEHICLES service
@app.get("/vehicles")
async def gateway_vehicles(request: Request):
    return await _proxy("vehicles", "/vehicles", request)

@app.get("/vehicles/{vehicle_id}")
async def gateway_vehicle_by_id(vehicle_id: str, request: Request):
    return await _proxy("vehicles", f"/vehicles/{vehicle_id}", request)
