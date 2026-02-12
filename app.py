from fastapi import FastAPI, Depends, HTTPException
import httpx
from typing import Optional, Dict, Any

API_KEY = "b320b4d35b154cb784259e15d9fa5e78"  # Fill in with your API Key
ENDPOINT_URL = "https://api-v3.mbta.com/"  # DO NOT CHANGE THIS

app = FastAPI()  # Initialize the end point


# Helper: always attach api_key + perform GET request
def _auth_params() -> Dict[str, str]:
    return {"api_key": API_KEY} if API_KEY else {}


async def mbta_get(path: str, params: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    if params is None:
        params = {}
    params.update(_auth_params())

    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(f"{ENDPOINT_URL}{path}", params=params)
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="Not found")
        response.raise_for_status()
        return response.json()


@app.get("/")  # Create a default route
async def read_root():
    return {"message": "Welcome to my FastAPI Application!"}


# Get a list of all routes
@app.get("/routes")
async def get_routes():
    routes_list = list()
    data = await mbta_get("/routes")  # Send a request to the endpoint
    # Convert the response to JSON and extract the data key
    routes = data["data"]
    for route in routes:
        # Loop through all routes extracting relevant information
        routes_list.append(
            {
                "id": route["id"],
                "color": route["attributes"]["color"],
                "text_color": route["attributes"]["text_color"],
                "description": route["attributes"]["description"],
                "long_name": route["attributes"]["long_name"],
                "type": route["attributes"]["type"],
            }
        )
    # Return the routes_list in JSON format
    return {"routes": routes_list}


# Get information on a specific route
@app.get("/routes/{route_id}")
async def get_route(route_id: str):
    data = await mbta_get(f"/routes/{route_id}")  # Send a request to the endpoint
    # Convert the response to JSON and extract the data key
    route_data = data["data"]
    # Extract the relevant data
    route = {
        "id": route_data["id"],
        "color": route_data["attributes"]["color"],
        "text_color": route_data["attributes"]["text_color"],
        "description": route_data["attributes"]["description"],
        "long_name": route_data["attributes"]["long_name"],
        "type": route_data["attributes"]["type"],
    }
    # Return the data to the user
    return {"routes": route}


# Get a list of all lines
@app.get("/lines")
async def get_lines():
    lines_list = list()
    data = await mbta_get("/routes")
    routes = data["data"]

    for route in routes:
        lines_list.append(
            {
                "id": route["id"],
                "text_color": route["attributes"]["text_color"],
                "short_name": route["attributes"].get("short_name"),
                "long_name": route["attributes"]["long_name"],
                "color": route["attributes"]["color"],
            }
        )

    return {"lines": lines_list}


# Get info on a specific line
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


# Create a Route to Fetch All Alerts:
# Inject the get_all_alerts dependency into the route to fetch and return all alerts.
@app.get("/alerts")
async def read_alerts(route: str = None, stop: str = None, alerts=Depends(get_all_alerts)):
    return alerts


# Create a Route to Fetch a Specific Alert by ID:
# Inject the get_alert_by_id dependency and pass the alert_id to fetch specific alert details.
@app.get("/alerts/{alert_id}")
async def read_alert(alert_id: str, alert=Depends(get_alert_by_id)):
    return alert


# On Your Own
# Implement the /vehicles route
# Add query parameters for the route and revenue filters
async def get_all_vehicles(route: str = None, revenue: str = None):
    params = {}
    if route:
        params["filter[route]"] = route
    if revenue:
        params["filter[revenue]"] = revenue

    return await mbta_get("/vehicles", params=params)


# Implement the /vehicles/{id} route
async def get_vehicle_by_id(vehicle_id: str):
    return await mbta_get(f"/vehicles/{vehicle_id}")


@app.get("/vehicles")
async def read_vehicles(route: str = None, revenue: str = None, vehicles=Depends(get_all_vehicles)):
    return vehicles


@app.get("/vehicles/{vehicle_id}")
async def read_vehicle(vehicle_id: str, vehicle=Depends(get_vehicle_by_id)):
    return vehicle
