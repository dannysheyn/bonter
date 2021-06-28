import collections

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
        self.variables = {}
        self.__name__ = 'callable print class'

    def add_button(self, button):
        self.reply_buttons.append(button)

    def check_query(self, update: Update, context: CallbackContext):
        self.update_msg(update, context)
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

    def update_msg(self, update, context):
        msg = None
        match = r'\$\{([A-Za-z0-9_]+)\}'
        if 'questions' in context.user_data:
            question_dict = context.user_data['questions']
            if question_dict != {} and self.msg is not None:
                variables = re.findall(match, self.msg)
                for var in variables:
                    if var in question_dict:
                        msg = re.sub(match, question_dict[var], self.msg, 1)
        return msg or self.msg


class CallableQuestion(CallablePrint):
    def __init__(self, obj, question, next_state=1):
        super().__init__(question, next_state)
        self.obj = obj

    def __call__(self, update, context):
        update = self.check_query(update, context)
        question = self.msg
        if isinstance(self.obj, API):
            question += ', '.join(['{0}=inset your value here'.format(k) for k in
                                   self.obj.query_params.keys()])  ## text being multiplied self.msg =
            question += '\n in the format above.'
        else:  # this is a question
            if 'questions' not in context.user_data:
                context.user_data['questions'] = {}
        update.message.reply_text(text=question)
        return self.next_state


# Query Params example:
# Question = "Please enter the query params"
# Expected Answer = key=value, key=value


class CallableFollowUp(CallablePrint):
    def __init__(self, obj=None, answer=None, next_state=None, box_number=-1):
        super().__init__(next_state=next_state)
        self.obj = obj
        self.box_number = box_number

    def __call__(self, update, context):
        update = self.check_query(update, context)
        answer = update.message.text
        # context.user_data[]
        # validate answer according to patter

        if isinstance(self.obj, API):
            self.obj.parse_query_params(answer)
        else:
            variable_identifier = self.obj['variable_name']
            context.user_data['questions'][variable_identifier] = answer
        if isinstance(self.next_state, collections.Callable):
            return self.next_state(update, context)
        else:
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
