from datetime import datetime, timedelta

from aiogram import Router, F
from aiogram import Dispatcher
from aiogram.types import CallbackQuery, LabeledPrice, PreCheckoutQuery
from aiogram.utils.i18n import gettext as _
from aiogram.utils.i18n import lazy_gettext as __

from keyboards import get_payment_keyboard, get_pay_keyboard, get_main_menu_keyboard
from utils import goods, yookassa, telegram_stars, marzban_api
from db.methods import get_telegram_stars_payment, get_marzban_profile_db, delete_payment
from utils.lang import get_i18n_string
import glv

router = Router(name="callbacks-router") 

@router.callback_query(F.data.startswith("pay_kassa_"))
async def callback_payment_method_select(callback: CallbackQuery):
    await callback.message.delete()
    data = callback.data.replace("pay_kassa_", "")
    if data not in goods.get_callbacks():
        await callback.answer()
        return
    result = await yookassa.create_payment(
        callback.from_user.id, 
        data, 
        callback.message.chat.id, 
        callback.from_user.language_code)
    await callback.message.answer(
        _("To be paid - {amount}₽ ⬇️").format(
            amount=result['amount']
        ),
        reply_markup=get_pay_keyboard(result['url']))
    await callback.answer()

@router.callback_query(F.data.startswith("pay_tgstars_"))
async def callback_payment_method_select(callback: CallbackQuery):
    await callback.message.delete()
    data = callback.data.replace("pay_tgstars_", "")
    if data not in goods.get_callbacks():
        await callback.answer()
        return
    result = await telegram_stars.create_payment(
        callback.from_user.id, 
        data, 
        callback.message.chat.id, 
        callback.from_user.language_code)
    
    # Создаем счет для оплаты через Telegram Stars
    good = goods.get(data)
    prices = [LabeledPrice(label="XTR", amount=int(float(result['amount'])))]
    
    await callback.message.answer_invoice(
        title=_("Payment for {name}").format(name=good['name']),
        description=_("Purchase subscription {name}").format(name=good['name']),
        prices=prices,
        provider_token="",  # Для Telegram Stars используется пустая строка
        payload=result['order_id'],  # Используем order_id как payload для идентификации платежа
        currency="XTR",  # Валюта для Telegram Stars
        start_parameter="tgstars_payment"
    )
    await callback.answer()

@router.callback_query(lambda c: c.data in goods.get_callbacks())
async def callback_payment_method_select(callback: CallbackQuery):
    await callback.message.delete()
    good = goods.get(callback.data)
    await callback.message.answer(text=_("Select payment method ⬇️"), reply_markup=get_payment_keyboard(good))
    await callback.answer()

@router.pre_checkout_query()
async def pre_checkout_handler(pre_checkout_query: PreCheckoutQuery):
    # Подтверждаем предпродажную проверку
    await pre_checkout_query.answer(ok=True)

@router.message(F.successful_payment)
async def success_payment_handler(message):
    # Получаем информацию о платеже
    payment_info = message.successful_payment
    order_id = payment_info.invoice_payload
    
    # Получаем информацию о платеже из базы данных
    payment = await get_telegram_stars_payment(order_id)
    if payment is None:
        return
    
    # Получаем информацию о товаре и пользователе
    good = goods.get(payment.callback)
    user = await get_marzban_profile_db(payment.tg_id)
    
    # Генерируем подписку
    result = await marzban_api.generate_marzban_subscription(user.vpn_id, good)
    
    # Отправляем сообщение пользователю
    text = get_i18n_string("Thank you for your choice ❤️\n️\n<a href=\{link}\">Subscribe</a> so you don't miss any announcements ✅\n️\nYour subscription is purchased and available in \"My subscription 👤\".", payment.lang)
    await message.answer(
        text.format(
            link=glv.config['PANEL_GLOBAL'] + result['subscription_url']
        ),
        reply_markup=get_main_menu_keyboard(payment.lang)
    )
    
    # Удаляем информацию о платеже из базы данных
    await delete_payment(order_id)

def register_callbacks(dp: Dispatcher):
    dp.include_router(router)
