from telegram import Update, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from api import *




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


class CallableQuestion(CallablePrint):
    def __init__(self, obj, question, next_state=1):
        super().__init__(question, next_state)
        self.obj = obj

    def __call__(self, update, context):
        update = self.check_query(update, context)

        if isinstance(self.obj, API):
            self.msg += ', '.join(['{0}'.format(k) for k in self.obj.query_params.keys()])
        update.message.reply_text(text=self.msg)
        return self.next_state

# Query Params example:
# Question = "Please enter the query params"
# Expected Answer = key=value, key=value


class CallableFollowUp(CallablePrint):
    def __init__(self, obj, answer, next_state=1):
        super().__init__(next_state)
        self.obj = obj

    def __call__(self, update , context):
        update = self.check_query(update, context)
        answer = update.message.text

        #validate answer according to pattern

        if isinstance(self.obj, API):
            self.obj.parse_query_params(answer)

        return self.next_state


class CallableAPI(CallablePrint):
    def __init__(self, api, msg, next_state=1):
        super().__init__(msg, next_state)
        self.api = api

    def __call__(self, update: Update, context: CallbackContext):
        update = self.check_query(update, context) # text = "Please provide the query params "
        # update.message.reply_text(text = )

        self.api.parse_message_to_user()
        text = self.api.message_to_user
        if self.reply_buttons:
            print(self.reply_buttons)
            keyboard = InlineKeyboardMarkup([self.reply_buttons])
            update.message.reply_text(text=text, reply_markup=keyboard)
        else:
            update.message.reply_text(text=text)
        return self.next_state
