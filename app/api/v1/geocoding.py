from fastapi import APIRouter, HTTPException, Query
import requests

router = APIRouter(
    prefix="/geocoding",
    tags=["geocoding"],
)

def _format_short_address(addr: dict) -> str:
    """Return a concise, Google-like address string from Nominatim address dict.

    Preference order tries to pick the most human-friendly locality names.
    """
    if not isinstance(addr, dict):
        return ""
    parts_priority = [
        # locality
        ["suburb", "neighbourhood", "hamlet", "village", "town", "city_district", "city", "municipality"],
        # region/state
        ["county"],
        ["state_district"],
        ["state"],
        # country
        ["country"],
    ]

    parts: list[str] = []
    seen = set()
    for group in parts_priority:
        for key in group:
            val = addr.get(key)
            if val and val not in seen:
                parts.append(str(val))
                seen.add(val)
                break  # one per group
    return ", ".join(parts) or addr.get("display_name", "")

@router.get("/forward")
def forward_geocoding(q: str = Query(..., title="Location Name", description="The address to geocode")):
    """Performs forward geocoding using Nominatim."""
    try:
        params = {
            "q": q,
            "countrycodes": "np",
            "format": "json",
            "limit": 10,
            "addressdetails": 1,
        }
        response = requests.get("https://nominatim.openstreetmap.org/search", params=params, headers={"User-Agent": "HeritEdge/1.0"})
        response.raise_for_status()

        data = response.json()
        if not data:
            raise HTTPException(status_code=404, detail="No results found")

        results = [
            {
                "display_name": item.get("display_name"),
                "lat": item.get("lat"),
                "lng": item.get("lon"),
                "formatted": _format_short_address(item.get("address", {})),
            }
            for item in data
        ]
        return {"message": "Location fetched successfully", "data": results}
    except requests.exceptions.RequestException as error:
        raise HTTPException(status_code=502, detail=f"Failed to fetch data from external API: {error}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected server error occurred: {e}")


@router.get("/reverse")
def reverse_geocoding(
    lat: float = Query(..., title="Latitude", description="The latitude to geocode"),
    lng: float = Query(..., title="Longitude", description="The longitude to geocode"),
):
    """Performs reverse geocoding using Nominatim."""
    try:
        params = {
            "lat": lat,
            "lon": lng,
            "format": "json",
            "addressdetails": 1,
            "zoom": 15,
        }
        response = requests.get("https://nominatim.openstreetmap.org/reverse", params=params, headers={"User-Agent": "HeritEdge/1.0"})
        response.raise_for_status()
        data = response.json()
        if not data or "error" in data:
            raise HTTPException(status_code=404, detail="No address found for these coordinates")
        result = {
            "display_name": data.get("display_name"),
            "lat": data.get("lat"),
            "lng": data.get("lon"),
            "address": data.get("address", {}),
            "formatted": _format_short_address(data.get("address", {})),
        }
        return {"message": "Address fetched successfully", "data": result}
    except requests.exceptions.RequestException as error:
        raise HTTPException(status_code=502, detail=f"Failed to fetch data from external API: {error}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected server error occurred: {e}")
