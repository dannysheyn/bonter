from typing import Optional
from telegram import Update, CallbackQuery
import userGeneratedBot


class CurrentUser:
    _current_user_bot = {}

    @staticmethod
    def get_id(update: Optional[Update, CallbackQuery]):
        if isinstance(update, Update):
            return update.message.chat.id
        else:
            return update.from_user.id

    @staticmethod
    def get_current_user(update: Optional[Update, CallbackQuery]):
        user_id = CurrentUser.get_id(update)
        if user_id not in CurrentUser._current_user_bot:
            CurrentUser._current_user_bot[user_id] = userGeneratedBot.UserGeneratedBot()
        return CurrentUser._current_user_bot[user_id]

    @staticmethod
    def set_current_user(update: Optional[Update, CallbackQuery], bot: userGeneratedBot.UserGeneratedBot):
        user_id = CurrentUser.get_id(update)
        CurrentUser._current_user_bot[user_id] = bot
