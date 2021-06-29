from telegram import InlineKeyboardButton
from telegram.ext import CallbackQueryHandler, CommandHandler, MessageHandler, Filters
from callableBox import *
from showBot import botToPicture, bot_edge, bot_node

BOX_TYPE_API = 'api'
BOX_TYPE_TEXT = 'text'
BOX_TYPE_QUESTION = 'question'
BOX_TYPE_FOLLOW_UP = 'follow_up'


class UserGeneratedBot:

    # TODO: Change this long constructor and create an Object
    def __init__(self, bot_username=None, api_key=None, conv_handler=None):

        self.bot_username = bot_username
        self.api_key = api_key
        self.conv_handler = conv_handler
        self.updater = None  # Updater(api_key, use_context=True)
        self.dispatcher = None
        self.entry_points = []  # build on the go /start /hi
        self.states = {}  # build on the go
        self.state_key = 1
        self.message_handler_key = '1'
        self.commands = []
        self.build_button = {}
        self.button_key = 0
        # self.bot_pic.bot_edges = set()
        # self.bot_pic.bot_nodes = {}
        self.pattern = 0
        self.bot_pic = botToPicture()
        self.user_variables = {}
        self.apis = []

    def add_button_command(self, state_key, callback, button_text, returned_button_key):
        callback.add_button([InlineKeyboardButton(button_text, callback_data=str(self.button_key))])
        self.states[state_key].append(
            CallbackQueryHandler(callback, pattern='^' + str(self.button_key) + '$')
        )

        # fromBox = (1 ,2 ) => from box 1 button 2 (1.2) to destBox
        # (1,2), 2  1.2->2

    def add_edge(self, fromBox: tuple, destinationBox):
        # self.bot_pic.bot_edges.add((1, 2, 2))
        box = fromBox[0] - 1
        from_button = fromBox[1] - 1
        new_edge = bot_edge(box, from_button, destinationBox - 1)
        if new_edge not in self.bot_pic.bot_edges:
            self.bot_pic.bot_edges.add(new_edge)
        else:
            raise Exception('Cannot add the same edge twice')
        box_callback = self.states[self.state_key][box].callback
        box_buttons = box_callback.reply_buttons
        inlinekeyBoard = box_buttons[from_button]
        inlinekeyBoard.callback_data = str(destinationBox - 1)

    def add_box(self, box_msg, box_type, api_obj=None):
        if self.state_key not in self.states:
            self.states[self.state_key] = []
        if BOX_TYPE_API == box_type:
            self.states[self.state_key].append(
                CallbackQueryHandler(CallableAPI(msg=box_msg, obj=api_obj),
                                     pattern='^' + str(self.pattern) + '$'))
        if BOX_TYPE_QUESTION == box_type:
            self.states[self.state_key].append(
                CallbackQueryHandler(CallableQuestion(api_obj, box_msg, next_state=self.message_handler_key)))
        if BOX_TYPE_TEXT == box_type:
            self.states[self.state_key].append(
                CallbackQueryHandler(CallablePrint(msg=box_msg),
                                     pattern='^' + str(self.pattern) + '$'))

        self.bot_pic.bot_nodes[self.pattern] = bot_node(self.pattern, box_msg)
        self.pattern += 1
        return self.pattern

    def add_message_handler_state(self, obj=None, return_callback=None):
        self.states[self.message_handler_key] = [MessageHandler(filters=Filters.text, callback=CallableFollowUp(
            obj=obj,
            next_state=return_callback))
                                                 ]
        self.message_handler_key = str(int(self.message_handler_key) + 1)

    def find_return_callabck(self, box_number):
        box_number -= 1
        callbackqueryArray = self.states[self.state_key]
        pattern = '^' + str(box_number) + '$'
        for callback in callbackqueryArray:
            try:
                if callback.pattern.pattern == pattern:
                    return callback.callback
            except Exception as e:
                continue
        return None

    def add_box_button(self, box_number, button_text):
        callbackqueryArray = self.states[self.state_key]
        box_number -= 1
        node = self.bot_pic.bot_nodes[box_number]
        node.button_list.append(button_text)
        callbackqueryArray[box_number].callback.add_button(
            InlineKeyboardButton(button_text)
        )
        return len(callbackqueryArray[box_number].callback.reply_buttons)

    def add_starting_point(self, msg):
        callback = CallablePrint(msg=msg)
        callback.add_button(
            InlineKeyboardButton("Start you bot here!", callback_data=str(0))
        )
        self.entry_points.append(
            CommandHandler('start', callback)
        )

    def is_valid_box(self, box_number):
        box_number -= 1
        callbackqueryArray = self.states[self.state_key]
        pattern = '^' + str(box_number) + '$'
        for callback in callbackqueryArray:
            try:
                if callback.pattern.pattern == pattern:
                    return True
            except Exception as e:
                continue
        return False

    def show_bot(self, file_name='111'):
        return self.bot_pic.render_graph(self.bot_pic.bot_nodes.values(), self.bot_pic.bot_edges, file_name)

    def attach_timer_to_box(self, box_number, interval):
        callbackqueryArray = self.states[self.state_key]
        box_number -= 1
        box_callback = callbackqueryArray[box_number].callback
        box_callback.set_timer = TimerAction(box_callback, False, params={'interval': interval})
