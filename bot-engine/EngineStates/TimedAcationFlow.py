import json

from telegram import Update
from telegram.ext import CallbackContext

from CurrentUser import CurrentUser
from botEngine import BotEngine
from callableBox import *
import userMessages
from EngineStates import *
from api import API
from userGeneratedBot import BOX_TYPE_INTERNAL_VARIABLE


class TimedActionFlow:
    @staticmethod
    def timer_action(update: Update, context: CallbackContext):
        query = update.callback_query
        query.answer()
        text = 'The timer will be activated from when the moment the user will reach that timer-action-box.\n' \
               'Here is your bot, please choose the box to give it the time-action ability.'
        file_path = CurrentUser.get_current_user(update).show_bot(file_name=str(update.effective_user.id))
        query.message.reply_photo(photo=open(file_path, 'rb'), caption=text)
        return TIMER_ACTION2

    @staticmethod
    def timer_action2(update: Update, context: CallbackContext):
        try:
            user_box_selected = int(update.message.text)
            valid_box = CurrentUser.get_current_user(update).is_valid_box(user_box_selected)
            if valid_box:
                CurrentUser.get_current_user(update).user_variables['box-timer'] = user_box_selected
                update.message.reply_text(text='Please enter the interval and finish time for this polling\n'
                                               'Interval in seconds\n'
                                               'Example: 10')
                return TIMER_ACTION3
        except Exception as s:
            update.message.reply_text(text='Wrong box was given please try again')
            return TIMER_ACTION2

    @staticmethod
    def timer_action3(update: Update, context: CallbackContext):
        inetrval_endtime = update.message.text
        try:
            interval = int(inetrval_endtime)
            CurrentUser.get_current_user(update).attach_timer_to_box(
                CurrentUser.get_current_user(update).user_variables['box-timer'],
                interval)
            update.message.reply_text(text='Timer attached successfully!')
        except Exception as s:
            print(s)
        return BotEngine.edit_bot(update, context)
