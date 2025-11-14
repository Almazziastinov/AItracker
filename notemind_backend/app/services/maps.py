import os
import requests
import openrouteservice
from dotenv import load_dotenv
# Импорты для работы со временем (для Участника 2)
from datetime import datetime, timedelta

load_dotenv()
ORS_API_KEY = os.getenv("ORS_API_KEY")

# URL API ORS Geocoding
ORS_GEOCODE_URL = "https://api.openrouteservice.org/geocode/search"

# Инициализация клиента ORS (используется для Directions API)
client_ors = None
if ORS_API_KEY:
    try:
        client_ors = openrouteservice.Client(key=ORS_API_KEY)
    except Exception as e:
        print(f"Error initializing ORS client: {e}. Check your ORS_API_KEY.")
        
# ------------------------------------------------------------
# 1. API ГЕОКОДЕРА (ORS) - АДРЕС -> КООРДИНАТЫ 
# ------------------------------------------------------------

def get_coords_by_address(address: str) -> tuple[float, float] | None:
    """
    Преобразует адрес в координаты (долгота, широта), используя ORS Geocoding HTTP API.
    
    Returns: tuple[longitude, latitude] or None
    """
    if not ORS_API_KEY:
        print("ERROR: ORS API key not found.")
        return None
        
    headers = {
        'Accept': 'application/json',
    }
    params = {
        'api_key': ORS_API_KEY, 
        'text': address,
        'size': 1               
    }

    try:
        response = requests.get(ORS_GEOCODE_URL, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        
        if not data.get('features'):
            print(f"ORS Geocoder: No results found for address: {address}")
            return None
            
        long, lat = data['features'][0]['geometry']['coordinates']
        
        print(f"ORS Geocoder success: {address} -> ({long}, {lat})")
        return long, lat 

    except Exception as e:
        print(f"Error calling ORS Geocoder API via HTTP: {e}")
        return None

# ------------------------------------------------------------
# 2. API МАРШРУТИЗАЦИИ (ORS) - КООРДИНАТЫ -> ВРЕМЯ
# ------------------------------------------------------------

def get_travel_time(origin_coords: tuple[float, float], destination_coords: tuple[float, float]) -> int:
    """
    Возвращает время в пути в минутах, используя ORS Directions API.
    Координаты должны быть (долгота, широта).
    """
    if not client_ors:
        print("WARNING: ORS client not available. Returning 45 minutes fallback.")
        return 45
        
    try:
        route = client_ors.directions(
            coordinates=[origin_coords, destination_coords],
            profile='driving-car'
        )
        
        duration_seconds = route['routes'][0]['summary']['duration']
        time_minutes = round(duration_seconds / 60)
        
        print(f"ORS Directions success: Travel time is {time_minutes} minutes.")
        return time_minutes

    except Exception as e:
        print(f"Error calling ORS Directions API: {e}. Returning fallback time.")
        return 45 

# ------------------------------------------------------------
# 3. ФУНКЦИИ ДЛЯ УЧАСТНИКА 2 (ПЛАНИРОВАНИЕ)
# ------------------------------------------------------------

def calculate_departure_time(event_time: datetime, travel_time_minutes: int) -> datetime:
    """
    Рассчитывает время, когда нужно выехать, чтобы прибыть точно к началу события.
    
    Args:
        event_time (datetime): Планируемое время начала события.
        travel_time_minutes (int): Время в пути в минутах (полученное от get_travel_time).
        
    Returns:
        datetime: Время, когда нужно начать поездку.
    """
    # Вычитаем время в пути из времени начала события
    return event_time - timedelta(minutes=travel_time_minutes)
    
def calculate_arrival_time(departure_time: datetime, travel_time_minutes: int) -> datetime:
    """
    Рассчитывает время прибытия, если известен момент выезда.
    
    Args:
        departure_time (datetime): Фактическое время выезда.
        travel_time_minutes (int): Время в пути в минутах.
        
    Returns:
        datetime: Время прибытия в пункт назначения.
    """
    # Прибавляем время в пути к времени выезда
    return departure_time + timedelta(minutes=travel_time_minutes)


# ------------------------------------------------------------
# ТЕСТОВАЯ ЧАСТЬ
# ------------------------------------------------------------

if __name__ == "__main__":
    
    # --- ТЕСТ 1: ПРОВЕРКА ЛОГИСТИКИ (Геокодер + Маршрутизация) ---
    start_point_coords = (37.5020, 55.6268) # Координаты Теплого Стана (Долгота, Широта)
    destination_address = "Москва, ул Гашека, 7" 
    
    print(f"\n--- 1. Тест Логистики: {destination_address} ---")
    destination_coords = get_coords_by_address(destination_address)
    
    time_minutes = 0
    if destination_coords:
        time_minutes = get_travel_time(start_point_coords, destination_coords)
        print(f"➡️ Расчетное время в пути: {time_minutes} минут.")
    else:
        print("❌ Тест логистики провален.")
        
    # --- ТЕСТ 2: ПРОВЕРКА ФУНКЦИЙ ПЛАНИРОВАНИЯ ---
    
    if time_minutes > 0:
        event_start = datetime(2025, 12, 1, 10, 0, 0) # Событие начинается 01.12.2025 в 10:00
        
        departure = calculate_departure_time(event_start, time_minutes)
        
        print(f"\n--- 2. Тест Планирования ---")
        print(f"Событие начинается:    {event_start.strftime('%H:%M')}")
        print(f"Время в пути:         {time_minutes} минут")
        print(f"✅ Время выезда:       {departure.strftime('%H:%M')}")