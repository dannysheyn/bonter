from telegram import Update, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from api import *



class ExtendedAction:
    def __init__(self, callback=None, activated=None, params=None):
        self.callback = callback
        self.activated = activated
        self.params = params


class TimerAction(ExtendedAction):
    def __init__(self, callback, activated, params):
        super(TimerAction, self).__init__(callback, activated, params)

    def __call__(self, update: Update, context: CallbackContext, callable_origin):
        interval = self.params['interval']
        chat_id = update.message.chat_id
        context.job_queue.run_repeating(callback=callable_origin.timer_action,
                                        interval=interval,
                                        first=5,
                                        last=31536000,
                                        context={'update': update, 'context': context},
                                        name=str(chat_id))
        self.activated = True

    @staticmethod
    def __name__():
        return 'timer action class'


class CallablePrint:
    def __init__(self, msg=None, next_state=1, timer_action=None):
        self.msg = msg
        self.next_state = next_state
        self.reply_buttons = []
        self.set_timer = timer_action
        self.__name__ = 'callable print class'

    def add_button(self, button):
        self.reply_buttons.append(button)

    def check_query(self, update: Update, context: CallbackContext):
        if hasattr(update, 'callback_query'):
            query = update.callback_query
            if query is not None:
                query.answer()
                return query
        return update

    def extend(self, update, context):
        if self.set_timer is not None:
            if not self.set_timer.activated:
                self.set_timer(update, context, self)

    def __call__(self, update: Update, context: CallbackContext):
        update = self.check_query(update, context)
        self.extend(update, context)
        if self.reply_buttons:
            print(self.reply_buttons)
            keyboard = InlineKeyboardMarkup([self.reply_buttons])
            update.message.reply_text(text=self.msg, reply_markup=keyboard)
        else:
            update.message.reply_text(text=self.msg)
        return self.next_state

    def timer_action(self, context: CallbackContext):
        update = context.job.context['update']
        user_context = context.job.context['context']
        self.__call__(update, user_context)

    @staticmethod
    def __name__():
        return 'callable print class'


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

    def __call__(self, update, context):
        update = self.check_query(update, context)
        answer = update.message.text

        # validate answer according to pattern

        if isinstance(self.obj, API):
            self.obj.parse_query_params(answer)

        return self.next_state


class CallableAPI(CallablePrint):
    def __init__(self, api, msg, next_state=1):
        super().__init__(msg, next_state)
        self.api = api
        self.msg = 'API fetch box'

    def __call__(self, update: Update, context: CallbackContext):
        update = self.check_query(update, context)
        self.extend(update, context)
        self.api.parse_message_to_user()
        text = self.api.message_to_user
        if self.reply_buttons:
            print(self.reply_buttons)
            keyboard = InlineKeyboardMarkup([self.reply_buttons])
            update.message.reply_text(text=text, reply_markup=keyboard)
        else:
            update.message.reply_text(text=text)
        return self.next_state
