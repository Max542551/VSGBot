from database.database import Taxi, User


async def update_sent_item(sent_item, **kwargs):
    for key, value in kwargs.items():
        setattr(sent_item, key, value)
    sent_item.save()


def update_or_create_taxi(user_id, **kwargs):
    Taxi.update(**kwargs).where(Taxi.user_id == user_id).execute()
    Taxi.get_or_create(user_id=user_id, defaults=kwargs)


def update_user_address(user_id: int, home_address=None, work_address=None):
    user = User.get(User.user_id == user_id)
    if home_address:
        user.home_address = home_address
    if work_address:
        user.work_address = work_address
    user.save()