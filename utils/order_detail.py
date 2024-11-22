from geopy.distance import geodesic
from database.get_to_db import get_address_from_coordinates


async def calculate_order_details(order):
    first_location = (order.first_latitude, order.first_longitude)
    second_location = (order.second_latitude, order.second_longitude)
    first_address = await get_address_from_coordinates(first_location[0], first_location[1])
    second_address = await get_address_from_coordinates(second_location[0], second_location[1])

    return first_address, second_address
