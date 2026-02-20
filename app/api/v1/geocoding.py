from fastapi import APIRouter, HTTPException
import requests
import os

router = APIRouter(prefix="/geocoding", tags=["geocoding"])

# Using Nominatim (OpenStreetMap) for free geocoding
NOMINATIM_BASE_URL = "https://nominatim.openstreetmap.org"

@router.get("/reverse")
async def reverse_geocode(lat: float = None, lng: float = None, lon: float = None):
    """
    Reverse geocoding: Get address from coordinates
    """
    # Use lng if lon is not provided (frontend sends lng)
    longitude = lon if lon is not None else lng
    
    if lat is None or longitude is None:
        raise HTTPException(status_code=400, detail="lat and lng/lon parameters are required")
    
    try:
        url = f"{NOMINATIM_BASE_URL}/reverse"
        params = {
            "format": "json",
            "lat": lat,
            "lon": longitude,
            "addressdetails": 1
        }
        
        # Add user agent as required by Nominatim
        headers = {
            "User-Agent": "HeritEdge-Backend/1.0"
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if "error" in data:
            raise HTTPException(status_code=404, detail="Location not found")
        
        return {
            "address": data.get("display_name", ""),
            "country": data.get("address", {}).get("country", ""),
            "region": data.get("address", {}).get("state", ""),
            "city": data.get("address", {}).get("city", ""),
            "coordinates": {
                "lat": lat,
                "lon": lon
            }
        }
        
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=503, detail="Geocoding service unavailable")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search")
async def search_location(q: str, limit: int = 5):
    """
    Search for locations by address/name
    """
    try:
        url = f"{NOMINATIM_BASE_URL}/search"
        params = {
            "format": "json",
            "q": q,
            "limit": limit,
            "addressdetails": 1
        }
        
        headers = {
            "User-Agent": "HeritEdge-Backend/1.0"
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        results = []
        for item in data:
            results.append({
                "display_name": item.get("display_name", ""),
                "lat": float(item.get("lat", 0)),
                "lon": float(item.get("lon", 0)),
                "country": item.get("address", {}).get("country", ""),
                "region": item.get("address", {}).get("state", ""),
                "city": item.get("address", {}).get("city", ""),
            })
        
        return {"results": results}
        
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=503, detail="Geocoding service unavailable")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
