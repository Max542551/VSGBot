from database.database import SentMessage, Taxi


def delete_sent_messages(order_id: int):
    SentMessage.delete().where(SentMessage.order_id == order_id).execute()


async def remove_taxi(user_id: int):
    try:
        taxi = Taxi.get(Taxi.user_id == user_id)
        taxi.delete_instance()
        return True
    except Taxi.DoesNotExist:
        return False