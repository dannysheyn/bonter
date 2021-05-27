from telegram import Update, InlineKeyboardMarkup
from telegram.ext import CallbackContext


class CallablePrint:
    def __init__(self, msg=None, next_state=1):
        self.msg = msg
        self.next_state = next_state
        self.reply_buttons = []

    def add_button(self, button):
        self.reply_buttons.append(button)

    def check_query(self, update: Update, context: CallbackContext):
        query = update.callback_query
        if query is not None:
            query.answer()
            return query
        else:
            return update

    def __call__(self, update: Update, context: CallbackContext):
        update = self.check_query(update, context)
        if self.reply_buttons:
            print(self.reply_buttons)
            keyboard = InlineKeyboardMarkup([self.reply_buttons])
            update.message.reply_text(text=self.msg, reply_markup=keyboard)
        else:
            update.message.reply_text(text=self.msg)
        return self.next_state


class CallableAPI(CallablePrint):
    def __init__(self, api, msg, next_state=1):
        super().__init__(msg, next_state)
        self.api = api

    def check_query(self, update: Update, context: CallbackContext):
        query = update.callback_query
        if query is not None:
            query.answer()
            return query
        else:
            return update

    def __call__(self, update: Update, context: CallbackContext):
        update = self.check_query(update, context)
        self.api.parse_message_to_user()
        text = self.api.message_to_user
        if self.reply_buttons:
            print(self.reply_buttons)
            keyboard = InlineKeyboardMarkup([self.reply_buttons])
            update.message.reply_text(text=text, reply_markup=keyboard)
        else:
            update.message.reply_text(text=text)
        return self.next_state
