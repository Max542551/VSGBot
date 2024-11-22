from database.database import SentDeliveryMessage, SentMessage, Taxi


def delete_sent_messages(order_id: int):
    SentMessage.delete().where(SentMessage.order_id == order_id).execute()

def delivery_delete_sent_messages(order_id: int):
    SentDeliveryMessage.delete().where(SentDeliveryMessage.order_id == order_id).execute()


async def remove_taxi(user_id: int):
    try:
        taxi = Taxi.get(Taxi.user_id == user_id)
        taxi.delete_instance()
        return True
    except Taxi.DoesNotExist:
        return False