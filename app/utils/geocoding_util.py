import requests

NOMINATIM_BASE_URL = "https://nominatim.openstreetmap.org"

def get_location_name_from_coordinates(lat: float, lon: float) -> str:
    if lat is None or lon is None:
        return None
    try:
        url = f"{NOMINATIM_BASE_URL}/reverse"
        params = {
            "format": "json",
            "lat": lat,
            "lon": lon,
            "addressdetails": 1
        }
        headers = {
            "User-Agent": "HeritEdge-Backend/1.0"
        }
        response = requests.get(url, params=params, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get("display_name", None)
    except Exception:
        pass
    return None
