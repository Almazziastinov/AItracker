import os
from ymaps import Geocoder, Directions
from max_bot import config

# Initialize Yandex Maps API clients
# You need to obtain a Yandex Maps API key and set it as an environment variable.
# YANDEX_MAPS_API_KEY
geocoder = Geocoder(api_key=os.getenv("YANDEX_MAPS_API_KEY"))
directions = Directions(api_key=os.getenv("YANDEX_MAPS_API_KEY"))

async def get_travel_time(origin: str, destination: str) -> int | None:
    """
    Calculates travel time in minutes between two locations using Yandex.Maps Directions API.
    
    Args:
        origin: The starting point (address or coordinates).
        destination: The destination point (address or coordinates).

    Returns:
        Travel time in minutes, or None if calculation fails.
    """
    try:
        # Geocode origin and destination to coordinates if they are addresses
        # The Directions API usually works better with coordinates
        origin_coords = await geocoder.geocode(origin)
        destination_coords = await geocoder.geocode(destination)

        if not origin_coords or not destination_coords:
            return None

        # Get directions
        # The ymaps library might have a direct way to get duration.
        # Assuming it returns a route object from which duration can be extracted.
        route = await directions.get_route(
            origin=origin_coords[0].point, # Assuming point is (lon, lat)
            destination=destination_coords[0].point,
            mode="driving" # Or "transit", "walking"
        )
        
        # Extract duration from the route. This is highly dependent on the ymaps library's structure.
        # I'll assume a common structure where duration is in seconds.
        if route and route.duration:
            return route.duration // 60 # Convert seconds to minutes
        
        return None

    except Exception as e:
        print(f"Error calculating travel time: {e}")
        return None

# TODO: Add a function to store/retrieve user's home address
# For now, we'll assume a default or ask the user every time.
