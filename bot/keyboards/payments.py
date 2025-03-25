from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.i18n import gettext as _

import glv

def get_payment_keyboard(good) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    yoo = glv.config['YOOKASSA_SHOPID'] and glv.config['YOOKASSA_TOKEN']
    tg_stars = glv.config['TELEGRAM_STARS_ENABLED']
    f = yoo or tg_stars
    if not f:
        builder.row(
            InlineKeyboardButton(
                text="Oh no...",
                callback_data=f"none"
            )
        )
        return builder.as_markup()
    if yoo:
        builder.row(
            InlineKeyboardButton(
                text=_("YooKassa - {price}₽").format(
                    price=good['price']['ru']
                ),
                callback_data=f"pay_kassa_{good['callback']}"
            )
        )
    if tg_stars:
        builder.row(
            InlineKeyboardButton(
                text=f"Telegram Stars - {good['price']['en']} ⭐️",
                callback_data=f"pay_tgstars_{good['callback']}"
            )
        )
    return builder.as_markup()
