import googlemaps
import os
import json
from dotenv import load_dotenv
from ..settings import *
import logging

# Load environment variables from .env file
load_dotenv()

# Get a logger for this module
logger = logging.getLogger(__name__)

def find_restaurants(location:str, radius_km:int=1):
    """
    Finds restaurants near a given location within a specified radius.

    Args:
        location (str): The address or landmark to search near.
        radius_km (int): The search radius in kilometers.

    Returns:
        str: A JSON string representing a list of restaurants with detailed information.
    """
    logger.info(f"Finding restaurants near '{location}' with radius {radius_km}km.")
    api_key = os.environ.get("GOOGLE_MAPS_API_KEY") or GOOGLE_MAPS_API_KEY

    if not api_key:
        raise ValueError("Google Maps API key not found. Make sure to create a .env file with GOOGLE_MAPS_API_KEY=<YOUR_API_KEY>.")

    gmaps = googlemaps.Client(key=api_key)

    # Geocode the location to get latitude and longitude
    try:
        geocode_result = gmaps.geocode(location)
        if not geocode_result:
            return json.dumps({"error": "Could not geocode the provided location. Please provide a more specific address or landmark."})
        lat = geocode_result[0]['geometry']['location']['lat']
        lng = geocode_result[0]['geometry']['location']['lng']
    except Exception as e:
        return json.dumps({"error": f"An error occurred during geocoding: {e}"})

    # Search for nearby restaurants
    try:
        places_result = gmaps.places_nearby(
            location=(lat, lng),
            radius=radius_km * 1000,  # Convert km to meters
            type='restaurant'
        )
    except Exception as e:
        return json.dumps({"error": f"An error occurred while searching for restaurants: {e}"})

    restaurants = []
    for place in places_result.get('results', []):
        place_id = place.get('place_id')
        if not place_id:
            continue

        try:
            place_details = gmaps.place(
                place_id=place_id,
                fields=['name', 'vicinity', 'rating', 'website', 'reviews', 'user_ratings_total']
            )['result']
            
            restaurant_info = {
                'name': place_details.get('name'),
                'address': place_details.get('vicinity'),
                'rating': place_details.get('rating'),
                'total_reviews': place_details.get('user_ratings_total'),
                'website': place_details.get('website'),
                'reviews': place_details.get('reviews')
            }
            restaurants.append(restaurant_info)

        except Exception as e:
            logger.warning(f"Could not fetch details for place_id {place_id}: {e}")

    logger.info(f"Found {len(restaurants)} restaurants. Returning JSON output.")
    return json.dumps(restaurants, indent=4)

if __name__ == '__main__':
    # Example usage:
    # 1. Create a .env file in the root of the project
    # 2. Add the following line to the .env file:
    #    GOOGLE_MAPS_API_KEY="YOUR_API_KEY"
    # 3. Run this script

    location = "Eiffel Tower, Paris, France"
    radius = 1

    restaurants_json = find_restaurants(location, radius)
    
    # The output is a JSON string, so we can parse it to inspect it.
    restaurants_list = json.loads(restaurants_json)

    if restaurants_list:
        print(f"Found {len(restaurants_list)} restaurants within {radius}km of {location}:")
        for r in restaurants_list:
            print("\n----------------------------------------")
            print(f"Name: {r.get('name')}")
            print(f"Address: {r.get('address')}")
            print(f"Rating: {r.get('rating')} ({r.get('total_reviews')} reviews)")
            print(f"Website: {r.get('website', 'N/A')}")
            if r.get('reviews'):
                print("Reviews:")
                for review in r.get('reviews'):
                    print(f"  - {review.get('author_name')}: \"{review.get('text')}\"")
    else:
        print(f"No restaurants found within {radius}km of {location}.")
