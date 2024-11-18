import re
from typing import List
from config_data.config import geolocator


async def get_addresses(query: str) -> List[str]:
    # функция для получения списка адресов
    locations = await geolocator.geocode(query, exactly_one=False)

    addresses = []
    for location in locations:
        addresses.append(get_sorted_address(location.address))

    return addresses


def get_sorted_address(address: str) -> str:
    # Паттерн для поиска почтового индекса
    zip_pattern = r'\d{6}'

    # удаляем индекс, если он есть
    address = re.sub(zip_pattern, '', address)

    # split the address into parts
    parts = address.split(',')

    # remove duplicate parts
    seen = set()
    parts = [x.strip() for x in parts if not (x in seen or seen.add(x))]

    # sort the parts in the desired order
    if len(parts) == 4:
        sorted_parts = [parts[1], parts[0], parts[2], parts[3]]
    elif len(parts) == 3:
        sorted_parts = [parts[1], parts[0], parts[2]]
    elif len(parts) == 2:
        sorted_parts = [parts[1], parts[0]]
    else:
        sorted_parts = parts

    # rejoin the parts into a string and return
    return ', '.join(sorted_parts).strip()
