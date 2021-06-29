from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import CallbackContext


class Callback:
    def __init__(self, msg, next_state, replay_button=None):
        self.msg = msg
        self.next_state = next_state
        self.replay_buttons = [replay_button]

    def add_button(self, button: list):
        if self.replay_buttons is None:
            replay_buttons = [button]
        elif isinstance(self.replay_buttons, str):
            temp = self.replay_buttons
            self.replay_buttons = [[temp], button]
        else:
            self.replay_buttons.append(button)

    @staticmethod
    def check_query(update: Update, context: CallbackContext):
        query = update.callback_query
        if query is not None:
            query.answer()
            return query
        else:
            return update


class Start(Callback):
    def __call__(self, update: Update, context: CallbackContext):
        text = self.msg
        keyboard = ReplyKeyboardMarkup([['Press here to start the bot']])
        update.message.reply_text(text=text, reply_markup=keyboard)
        return self.next_state

class Button(Callback):
    def __call__(self, update: Update, context: CallbackContext):
        update = Callback.check_query(update, context)
        if self.replay_buttons:
            print(self.replay_buttons)
            keyboard = ReplyKeyboardMarkup(self.replay_buttons)
            text = "Pick one of the following:"
            update.message.reply_text(text=text, reply_markup=keyboard)
        return self.next_state


class Answer:
    def __init__(self, msg, next_state, replay_buttons=None):
        self.msg = msg
        self.next_state = next_state
        self.replay_buttons = replay_buttons

    def add_button(self, button):
        if self.replay_buttons is None:
            replay_buttons = [button]
        elif isinstance(self.replay_buttons, str):
            temp = self.replay_buttons
            self.replay_buttons = [temp, button]
        else:
            self.replay_buttons.append(button)

    def __call__(self, update: Update, context: CallbackContext):
        update = Callback.check_query(update, context)
        if self.replay_buttons:
            print(self.replay_buttons)
            keyboard = ReplyKeyboardMarkup(self.replay_buttons)
            update.message.reply_text(text=self.msg, reply_markup=keyboard)
        else:
            update.message.reply_text(text=self.msg)
        return self.next_state

#
# class CallableAPI:
#     def __init__(self, uri, next_state):
#         self.uri = uri
#         self.next_state = next_state
#         self.replay_buttons = []
#         self.json_value = None
#
#     def add_button(self, button):
#         self.replay_buttons.append(button)
#
#     def check_query(self, update: Update, context: CallbackContext):
#         query = update.callback_query
#         if query is not None:
#             query.answer()
#             return query
#         else:
#             return update
#
#     def __call__(self, update: Update, context: CallbackContext):
#         update = self.check_query(update, context)
#         response = requests.get(self.uri)
#         update.message.reply_text(text=self.msg)
#         if self.replay_buttons:
#             print(self.replay_buttons)
#             keyboard = InlineKeyboardMarkup(self.replay_buttons)
#             text = "What would you like to do next"
#             update.message.reply_text(text=text, reply_markup=keyboard)
#         return self.next_state
