import time
import hashlib

from db.methods import add_telegram_stars_payment
from utils import goods
import glv

async def create_payment(tg_id: int, callback: str, chat_id: int, lang_code: str) -> dict:
    good = goods.get(callback)
    prepared_str = str(tg_id) + str(time.time()) + callback
    o_id = hashlib.md5(prepared_str.encode()).hexdigest()
    
    # Для Telegram Stars не нужно делать внешний API-запрос, так как оплата происходит внутри Telegram
    # Сохраняем информацию о платеже в базу данных
    await add_telegram_stars_payment(tg_id, callback, chat_id, lang_code, o_id)
    
    # Возвращаем только необходимую информацию для создания счета
    return {
        "amount": str(good['price']['en']),
        "order_id": o_id
    }