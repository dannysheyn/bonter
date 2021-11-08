import collections

from telegram import InlineKeyboardMarkup
from api import *
import helpers
import copy

CALLABLE_QUESTION = "CallableQuestion"
CALLABLE_PRINT = "CallablePrint"
CALLABLE_FOLLOWUP = "CallableFollowUp"
CALLABLE_API = "CallableAPI"
CALLABLE_INTERNAL_API = "CallableInternalAPI"


class ExtendedAction:
    def __init__(self, callback=None, activated=False, params=None):
        self.callback = callback
        self.activated = activated
        self.params = params


class TimerAction(ExtendedAction):
    def __init__(self, callback, activated, params):
        super().__init__(callback, activated, params)

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
    def __init__(self, msg=None, next_state=1, timer_action=None, callback_type=CALLABLE_PRINT,
                 box_number=1):
        self.msg = msg
        self.next_state = next_state
        self.reply_buttons = []
        self.set_timer = timer_action
        self.variables = {}
        self.callback_type = callback_type
        self.__name__ = 'callable print class'
        self.box_number = box_number

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

    @staticmethod
    def log_message(update: Update, context: CallbackContext):
        from botEngine import BotEngine
        helpers.add_chat(BotEngine.mongo_client, update, context)

    def __call__(self, update: Update, context: CallbackContext):
        update = self.check_query(update, context)
        self.log_message(update, context)
        self.extend(update, context)
        msg = self.update_msg(update, context)
        if self.reply_buttons:
            print(self.reply_buttons)
            for button in self.reply_buttons:
                if button.callback_data is None:
                    button.callback_data = 0
            keyboard = InlineKeyboardMarkup([self.reply_buttons])
            update.message.reply_text(text=msg, reply_markup=keyboard)
        else:
            update.message.reply_text(text=msg)
        return self.next_state

    def timer_action(self, context: CallbackContext):
        update = context.job.context['update']
        user_context = context.job.context['context']
        self.__call__(update, user_context)

    @staticmethod
    def __name__():
        return 'callable print class'

    # user_data:{userName:..., city: Tel-Aviv}
    def update_msg(self, update, context, msg=None):
        if msg is None:
            msg = self.msg
        match = r'\$\{([A-Za-z0-9_]+)\}'
        if 'user_data' in context.user_data:
            question_dict = context.user_data['user_data']
            if question_dict != {} and msg is not None:
                variables = re.findall(match, msg)
                for var in variables:
                    if var in question_dict:
                        msg = re.sub(match, question_dict[var], msg, 1)
        if msg is None:
            return self.msg
        else:
            return msg


class CallableQuestion(CallablePrint):
    def __init__(self, question, obj, next_state=1, callback_type=CALLABLE_QUESTION, box_number=1):
        super().__init__(msg=question, next_state=next_state, box_number=box_number)
        self.callback_type = callback_type
        if obj is None:
            self.obj = {}
        else:
            self.obj = obj

    def __call__(self, update, context):
        update = self.check_query(update, context)
        self.log_message(update, context)
        question = self.update_msg(update, context)
        if isinstance(self.obj, API):
            question += ', '.join(['{0}=inset your value here'.format(k) for k in
                                   self.obj.query_params.keys()])  ## text being multiplied self.msg =
            question += '\n in the format above.'
        else:  # this is a question
            if 'user_data' not in context.user_data:
                context.user_data['user_data'] = {}
        update.message.reply_text(text=question)
        return self.next_state


# Query Params example:
# Question = "Please enter the query params"
# Expected Answer = key=value, key=value


class CallableFollowUp(CallablePrint):
    def __init__(self, obj=None, answer=None, next_state=None, box_number=-1, callback_type=CALLABLE_FOLLOWUP,
                 is_box=True):
        super().__init__(next_state=next_state, box_number=box_number)
        self.callback_type = callback_type
        self.obj = obj
        self.is_box = is_box

    def __call__(self, update, context):
        update = self.check_query(update, context)
        answer = update.message.text
        self.log_message(update, context)
        # context.user_data[]
        # validate answer according to patter

        if isinstance(self.obj, API):
            self.obj.parse_query_params(answer)
        else:
            variable_identifier = self.obj['variable_name']
            context.user_data['user_data'][variable_identifier] = answer
        if isinstance(self.next_state, collections.Callable):
            return self.next_state(update, context)
        else:
            return self.next_state


class CallableAPI(CallablePrint):
    def __init__(self, obj, msg, next_state=1, callback_type=CALLABLE_API, box_number=1):
        super().__init__(msg=msg, next_state=next_state, box_number=box_number)
        self.callback_type = callback_type
        self.obj = obj
        self.msg = 'API fetch box'

    def __call__(self, update: Update, context: CallbackContext):
        update = self.check_query(update, context)
        self.log_message(update, context)
        self.extend(update, context)
        temp_obj = copy.deepcopy(self.obj)
        temp_obj.uri = temp_obj.update_uri(self.obj.uri, context.user_data)
        temp_obj.message_to_user = self.update_msg(update, context, self.obj.message_to_user)
        temp_obj.parse_message_to_user()
        text = temp_obj.message_to_user
        keyboard = None
        if self.reply_buttons:
            keyboard = InlineKeyboardMarkup([self.reply_buttons])

        if len(text) > 4096:
            for x in range(0, len(text), 4096):
                update.message.reply_text(text=text[x:x + 4096], reply_markup=keyboard)
        else:
            update.message.reply_text(text=text, reply_markup=keyboard)

        return self.next_state


class CallableInternalAPI(CallableAPI):
    def __init__(self, obj, msg, next_state=1, callback_type=CALLABLE_INTERNAL_API, box_number=1):
        super().__init__(msg=msg, next_state=next_state, box_number=box_number, obj=obj)
        self.callback_type = callback_type
        self.obj = obj
        self.msg = 'Internal API box will not be visible to the user'

    def __call__(self, update: Update, context: CallbackContext):
        self.log_message(update, context)
        self.extend(update, context)
        temp_obj = copy.deepcopy(self.obj)
        temp_obj.uri = temp_obj.update_uri(self.obj.uri, context.user_data)
        temp_obj.validate_keys(True)
        items = list(temp_obj.key_expression.items())
        inner_variable_name = items[0][0]
        inner_variable_value = items[1][1][1]
        if len(temp_obj.key_expression.items()) > 2:
            print('more the 1 time of key_expression was present in the CallableInternalAPI __call__ fucnton')
        else:
            var_name, var_value = temp_obj.key_expression.items()
            if 'user_data' not in context.user_data:
                context.user_data['user_data'] = {}
            context.user_data['user_data'][inner_variable_name] = inner_variable_value
        if isinstance(self.next_state, collections.Callable):
            return self.next_state(update, context)
        else:
            return self.next_state
