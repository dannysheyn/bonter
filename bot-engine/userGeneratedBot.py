from telegram import InlineKeyboardButton
from telegram.ext import CallbackQueryHandler, CommandHandler, MessageHandler, Filters
from callableBox import *
from showBot import botToPicture, bot_edge, bot_node


class UserGeneratedBot:
    box_type_api = 'api'
    box_type_text = 'text'
    box_type_question = 'question'
    box_type_follow_up = 'follow_up'

    def __init__(self, bot_username=None, bot_api_key=None, conv_handler=None):
        self.bot_username = bot_username
        self.bot_api_key = bot_api_key
        self.conv_handler = conv_handler
        self.updater = None  # Updater(bot_api_key, use_context=True)
        self.dispatcher = None
        self.entry_points = []  # build on the go /start /hi
        self.states = {}  # build on the go
        self.fallbacks = []  # build on the go
        self.state_key = 1
        self.message_handler_key = '1'
        self.commands = []
        self.button_key = 0
        self.build_button = {}
        self.edges = set()
        self.nodes = {}
        self.pattern = 0
        self.bot_pic = botToPicture()
        self.user_variables = {}
        self.client_variables = set()
        self.apis = []

    def add_button_command(self, state_key, callback, button_text, returned_button_key):
        callback.add_button([InlineKeyboardButton(button_text, callback_data=str(self.button_key))])
        self.states[state_key].append(
            CallbackQueryHandler(callback, pattern='^' + str(self.button_key) + '$')
        )

        # fromBox = (1 ,2 ) => from box 1 button 2 (1.2) to destBox
        # (1,2), 2  1.2->2

    def add_edge(self, fromBox: tuple, destinationBox):
        # self.edges.add((1, 2, 2))
        box = fromBox[0] - 1
        from_button = fromBox[1] - 1
        destinationBox = destinationBox - 1
        new_edge = bot_edge(box, from_button, destinationBox)
        if self.nodes[box].query_handler and self.nodes[destinationBox].query_handler:  # if the from box is a query
            # handler and the destination box is also a query handler callback type
            box_callback = self.nodes[box].callback
            box_buttons = box_callback.reply_buttons
            inlinekeyBoard = box_buttons[from_button]
            inlinekeyBoard.callback_data = str(destinationBox)
        elif self.nodes[box].query_handler and self.nodes[destinationBox].message_handler:
            box_callback = self.nodes[box].callback
            box_callback.next_state = self.nodes[destinationBox].state_value
            # box_buttons = box_callback.reply_buttons
            # inlinekeyBoard = box_buttons[from_button]
            # inlinekeyBoard.callback_data = str(destinationBox)
        elif self.nodes[box].message_handler and self.nodes[destinationBox].query_handler:
            # if the from box is a message handler and the destination is a query handler
            self.nodes[box].message_handler.callback.next_state = self.nodes[
                destinationBox].query_handler.callback  # return value of the message query
            # check if edge already exits for the print graph update
            for edge in self.edges:
                if edge.box == box:
                    self.edges.remove(edge)
                    break
            # should be the key in the state dictionary
            # message_handler_button = self.nodes[box].message_handler.callback.reply_buttons[from_button]  # get the
            # button of the message handler
            # message_handler_button.callback_data = str(destinationBox)  # set the callback data value of the dest box.
        else:
            raise Exception('Cannot add edge from a user variable getter to another user variable getter,'
                            'only to a regular box, because the box origin is dependent on user input.')
        if new_edge not in self.edges:
            self.edges.add(new_edge)
        else:
            raise Exception('Cannot add the same edge twice')

            # of if wer are from message handler to message handler

    def add_box(self, box_msg, box_type, api_obj=None):
        query_handler = None
        callback = None
        if self.state_key not in self.states:
            self.states[self.state_key] = []
        if self.box_type_api == box_type:
            callback = CallableAPI(msg=box_msg, api=api_obj)
            query_handler = CallbackQueryHandler(CallableAPI(msg=box_msg, api=api_obj),
                                                 pattern='^' + str(self.pattern) + '$')
        if self.box_type_question == box_type:
            query_handler = CallbackQueryHandler(
                CallableQuestion(api_obj, box_msg, next_state=self.message_handler_key),
                pattern='^' + str(self.pattern) + '$')
        if self.box_type_text == box_type:
            query_handler = CallbackQueryHandler(CallablePrint(msg=box_msg),
                                                 pattern='^' + str(self.pattern) + '$')
        self.states[self.state_key].append(query_handler)
        self.nodes[self.pattern] = bot_node(self.pattern, box_msg, query_handler=query_handler,
                                            state_value=self.state_key,
                                            box_type=box_type)
        self.pattern += 1
        return self.pattern

    def add_state(self, obj=None, return_callback=None, add_as_box=False):
        box_state_key = self.message_handler_key
        message_handler = MessageHandler(filters=Filters.text, callback=CallableFollowUp(
            obj=obj,
            next_state=return_callback))
        self.states[self.message_handler_key] = [
            message_handler
        ]
        if add_as_box:
            self.states[self.message_handler_key][0].callback.box_number = self.pattern
            var_name = self.states[self.message_handler_key][0].callback.obj['variable_name']
            self.nodes[self.pattern] = bot_node(self.pattern, f'user input of variable "{var_name}"',
                                                message_handler=message_handler,
                                                state_value=self.message_handler_key)
            self.pattern += 1
            box_state_key = self.pattern

        self.message_handler_key = str(int(self.message_handler_key) + 1)
        return box_state_key

    def find_return_callback(self, box_number):
        box_number -= 1
        return self.nodes[box_number].callback
        # before simplify
        # callbackqueryArray = self.states[self.state_key]
        # pattern = '^' + str(box_number) + '$'
        # for callback in callbackqueryArray:
        #     try:
        #         if callback.pattern.pattern == pattern:
        #             return callback.callback
        #     except Exception as e:
        #         continue
        # return None

    def add_box_button(self, box_number, button_text):
        box_number -= 1
        callback = self.nodes[box_number].callback
        callback.add_button(
            InlineKeyboardButton(button_text)
        )
        node = self.nodes[box_number]
        node.button_list.append(button_text)
        # callbackqueryArray = self.states[self.state_key]
        # box_number -= 1
        # node = self.nodes[box_number]
        # node.button_list.append(button_text)
        # callbackqueryArray[box_number].callback.add_button(
        #
        # )
        return len(callback.reply_buttons)

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
        if box_number in self.nodes:
            return True
        else:
            return False
        # callbackqueryArray = self.states[self.state_key]
        # pattern = '^' + str(box_number) + '$'
        # for callback in callbackqueryArray:
        #     try:
        #         if callback.pattern.pattern == pattern:
        #             return True
        #     except Exception as e:
        #         continue
        # return False

    def show_bot(self, file_name='111'):
        return self.bot_pic.render_graph(self.nodes.values(), self.edges, file_name)

    def attach_timer_to_box(self, box_number, interval):
        callbackqueryArray = self.states[self.state_key]
        box_number -= 1
        box_callback = callbackqueryArray[box_number].callback
        box_callback.set_timer = TimerAction(box_callback, False, params={'interval': interval})

    def add_client_variable_state(self, question, variable_name):
        self.client_variables.add(variable_name)
        question_box_number = self.add_box(box_msg=question,
                                           box_type=UserGeneratedBot.box_type_question,
                                           api_obj=None)
        question_box_callback = self.find_return_callback(question_box_number)
        self.add_state(obj={'variable_name': variable_name}, add_as_box=True)

    # def get_all_boxes(self):
    #     callbackqueryArray = self.states[self.state_key]
    #     for msg_query in self.states.values():
