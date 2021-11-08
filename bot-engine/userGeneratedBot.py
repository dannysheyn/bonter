from telegram import InlineKeyboardButton
from telegram.ext import CallbackQueryHandler, CommandHandler, MessageHandler, Filters
import callableBox
from showBot import BotGraph, bot_edge, bot_node

BOX_TYPE_API = 'api'
BOX_TYPE_TEXT = 'text'
BOX_TYPE_QUESTION = 'question'
BOX_TYPE_FOLLOW_UP = 'follow_up'
BOX_TYPE_INTERNAL_VARIABLE: str = 'internal_variable'


class UserGeneratedBot:

    # TODO: Change this long constructor and create an Object
    def __init__(self, bot_username=None, api_key=None, conv_handler=None):

        self.bot_username = bot_username
        self.api_key = api_key
        self.conv_handler = conv_handler
        self.updater = None  # Updater(api_key, use_context=True)
        self.dispatcher = None
        self.entry_point = None  # build on the go /start /hi
        self.states = {}  # build on the go
        self.state_key = 1
        self.message_handler_key = '1'
        self.commands = []
        self.build_button = {}
        self.button_key = 0
        self.pattern = 0
        self.bot_graph = BotGraph()
        self.user_variables = {}
        self.client_variables = set()
        self.apis = []
        self.internal_client_variables = {}

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
        destinationBox = destinationBox - 1
        new_edge = bot_edge(box, from_button, destinationBox)
        box_callback = self.bot_graph.bot_nodes[box].callback
        if isinstance(box_callback, callableBox.CallableInternalAPI):
            box_callback.next_state = self.bot_graph.bot_nodes[destinationBox].callback
        elif self.bot_graph.bot_nodes[box].query_handler and self.bot_graph.bot_nodes[
            destinationBox].query_handler:  # if the from box is a query
            # handler and the destination box is also a query handler callback type
            box_callback = self.bot_graph.bot_nodes[box].callback
            box_buttons = box_callback.reply_buttons
            inlinekeyBoard = box_buttons[from_button]
            inlinekeyBoard.callback_data = str(destinationBox)
        elif self.bot_graph.bot_nodes[box].query_handler and self.bot_graph.bot_nodes[destinationBox].message_handler:
            box_callback = self.bot_graph.bot_nodes[box].callback
            box_callback.next_state = self.bot_graph.bot_nodes[destinationBox].state_value
            # box_buttons = box_callback.reply_buttons
            # inlinekeyBoard = box_buttons[from_button]
            # inlinekeyBoard.callback_data = str(destinationBox)
        elif self.bot_graph.bot_nodes[box].message_handler and self.bot_graph.bot_nodes[destinationBox].query_handler:
            # if the from box is a message handler and the destination is a query handler
            self.bot_graph.bot_nodes[box].message_handler.callback.next_state = self.bot_graph.bot_nodes[
                destinationBox].query_handler.callback  # return value of the message query
            # check if edge already exits for the print graph update
            for edge in self.bot_graph.bot_edges:
                if edge.box == box:
                    self.bot_graph.bot_edges.remove(edge)
                    break
            # should be the key in the state dictionary
            # message_handler_button = self.bot_graph.bot_nodes[box].message_handler.callback.reply_buttons[from_button]  # get the
            # button of the message handler
            # message_handler_button.callback_data = str(destinationBox)  # set the callback data value of the dest box.
        else:
            raise Exception('Cannot add edge from a user variable getter to another user variable getter,'
                            'only to a regular box, because the box origin is dependent on user input.')
        if new_edge not in self.bot_graph.bot_edges:
            self.bot_graph.bot_edges.add(new_edge)
        else:
            raise Exception('Cannot add the same edge twice')

            # of if wer are from message handler to message handler

    def add_box(self, box_msg, box_type, api_obj=None):
        query_handler = None
        if self.state_key not in self.states:
            self.states[self.state_key] = []
        if BOX_TYPE_API == box_type:
            query_handler = CallbackQueryHandler(
                callableBox.CallableAPI(msg=box_msg, obj=api_obj, box_number=self.pattern),
                pattern='^' + str(self.pattern) + '$')
        if BOX_TYPE_QUESTION == box_type:
            query_handler = CallbackQueryHandler(
                callableBox.CallableQuestion(box_msg, api_obj, next_state=self.message_handler_key,
                                             box_number=self.pattern),
                pattern='^' + str(self.pattern) + '$')
        if BOX_TYPE_TEXT == box_type:
            query_handler = CallbackQueryHandler(callableBox.CallablePrint(msg=box_msg, box_number=self.pattern),
                                                 pattern='^' + str(self.pattern) + '$')
        if BOX_TYPE_INTERNAL_VARIABLE == box_type:
            query_handler = CallbackQueryHandler(
                callableBox.CallableInternalAPI(msg=box_msg, obj=api_obj, box_number=self.pattern),
                pattern='^' + str(self.pattern) + '$')

        self.states[self.state_key].append(query_handler)
        self.bot_graph.bot_nodes[self.pattern] = bot_node(self.pattern, box_msg, query_handler=query_handler,
                                                          state_value=self.state_key,
                                                          box_type=box_type)
        self.pattern += 1
        return self.pattern

    def add_message_handler_state(self, obj=None, return_callback=None, add_as_box=False):
        box_state_key = self.message_handler_key
        message_handler = MessageHandler(filters=Filters.text, callback=callableBox.CallableFollowUp(
            obj=obj,
            next_state=return_callback
        ))
        self.states[self.message_handler_key] = [message_handler]
        if add_as_box:
            message_handler.callback.box_number = self.pattern
            message_handler.callback.is_box = True
            var_name = self.states[self.message_handler_key][0].callback.obj['variable_name']
            self.bot_graph.bot_nodes[self.pattern] = bot_node(self.pattern, f'user input of variable "{var_name}"',
                                                              message_handler=message_handler,
                                                              state_value=self.message_handler_key)
            self.pattern += 1
            box_state_key = self.pattern

        self.message_handler_key = str(int(self.message_handler_key) + 1)
        return box_state_key

    def delete_state(self, box_num):
        if not self.is_valid_box(box_num):
            return False
        box_num -= 1
        callback = self.bot_graph.bot_nodes[box_num].callback
        if self.bot_graph.bot_nodes[box_num].query_handler:
            self.states[self.state_key] = [query_handler for query_handler in self.states[self.state_key]
                                           if self.filter_callbacks(query_handler.callback, callback)]
        else:
            for state, message_handler in self.states.items():
                if state != self.state_key and message_handler[0].callback == callback:
                    del self.states[state]
                    break
        # delete from bot_graph
        del self.bot_graph.bot_nodes[box_num]
        self.bot_graph.bot_edges = set(
            filter(lambda x: (x.box != box_num) and (x.destination != box_num), self.bot_graph.bot_edges))
        return True

    def filter_callbacks(self, callback, other_callback):
        return callback != other_callback

    def add_box_button(self, box_number, button_text):
        box_number -= 1
        callback = self.bot_graph.bot_nodes[box_number].callback
        callback.add_button(
            InlineKeyboardButton(button_text)
        )
        node = self.bot_graph.bot_nodes[box_number]
        node.button_list.append(button_text)
        return len(callback.reply_buttons)

    def find_return_callback(self, box_number):
        box_number -= 1
        return self.bot_graph.bot_nodes[box_number].callback

    def add_starting_point_from_message(self, message):
        for key, node in self.bot_graph.bot_nodes.items():
            if node.msg == message:
                self.entry_point = CommandHandler('start', node.callback)
                break

    def add_starting_point(self, box_number):
        callback = self.find_return_callback(int(box_number))
        # callback.add_button(
        #     InlineKeyboardButton("Start you bot here!", callback_data=str(0))
        # )
        self.entry_point = CommandHandler('start', callback)

    def is_valid_box(self, box_number):
        box_number -= 1
        if box_number in self.bot_graph.bot_nodes:
            return True
        else:
            return False

    def show_bot(self, file_name='111'):
        return self.bot_graph.render_graph(self.bot_graph.bot_nodes.values(), self.bot_graph.bot_edges, file_name)

    def attach_timer_to_box(self, box_number, interval):
        box_number -= 1
        box_callback = self.bot_graph.bot_nodes[box_number].callback
        box_callback.set_timer = callableBox.TimerAction(box_callback, False, params={'interval': interval})

    def add_client_variable_state(self, question, variable_name):
        self.client_variables.add(variable_name)
        question_box_number = self.add_box(box_msg=question,
                                           box_type=BOX_TYPE_QUESTION,
                                           api_obj=None)
        question_box_callback = self.find_return_callback(question_box_number)
        self.add_message_handler_state(obj={'variable_name': variable_name}, add_as_box=True)

    # def get_callabck_init(self, state_value):
    # # def get_all_boxes(self):
    # #     callbackqueryArray = self.states[self.state_key]
    # #     for msg_query in self.states.values():
