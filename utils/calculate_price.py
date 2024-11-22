async def calculate_cost(distance, current_time):
    if distance <= 2:
        cost = 150
    else:
        if 6 <= current_time.hour < 21:
            cost = 150 + (distance - 2) * 20
        else:
            cost = 150 + (distance - 2) * 30
    return cost