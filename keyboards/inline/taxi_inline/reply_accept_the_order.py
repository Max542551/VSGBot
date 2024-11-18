from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def order_acceptance_keyboard(order):
    inline_btn1 = InlineKeyboardButton('✅ Принять заказ', callback_data=f'order_acceptance_{order.id}')
    inline_btn2 = InlineKeyboardButton('💰 Предложить цену', callback_data=f'order_propose_price_{order.id}')
    keyboard = InlineKeyboardMarkup().add(inline_btn1, inline_btn2)
    return keyboard

def order_acceptance_keyboard_def(order):
    inline_btn1 = InlineKeyboardButton('✅ Принять предзаказ', callback_data=f'donfirm_order_defer_{order.id}')
    keyboard = InlineKeyboardMarkup().add(inline_btn1)
    return keyboard

def order_acceptance_keyboard_without_propose_price(order):
    keyboard = InlineKeyboardMarkup(row_width=1)
    start_order_button = InlineKeyboardButton('🚕 Я выезжаю', callback_data=f'start_order_confirmation_{order.id}')
    reject_order_button = InlineKeyboardButton('❌ Отказаться от заказа', callback_data=f'reject_order_confirmation_{order.id}')
    keyboard.add(start_order_button, reject_order_button)
    return keyboard



def get_accept_keyboard(order):
    if order.cost is None:
        return InlineKeyboardMarkup().add(
            InlineKeyboardButton('💰 Предложить цену', callback_data=f'order_propose_price_{order.id}')
        )
    else:
        return order_acceptance_keyboard(order)