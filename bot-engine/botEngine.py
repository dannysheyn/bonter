import json
from collections import namedtuple

from helpers import *
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
    Handler, CallbackQueryHandler,
)
import requests
from datetime import datetime
from api import API
from callback import *
import re
import pymongo
from showBot import *
import showBot
import threading
import os

# TODO: Flights, RSS,Group chats + bots,Group Notification, Basic Api integrations with calender, gmail and more., Polls, Order bot? ,data to Graps , predefined demos
# TODO: 1) fix the code.
# TODO: 2) MOVE to regular Buttons
# TODO NEXT TIME: add queryHandler to our bot can be hardcoded. checks and optimizations,
#  and looking into how to upgrade the fetures in the bot engine ( at least add command to a command) i.e nested commands.
# TODO: maybe api action?
# TODO: defult end bot,


# Save database of users (identify user by api key probably or userid) , get all the bots of the users, edit bots.
# maybe add another layer of menu before.
# build db, module of th db, ,new menu , new menu features
#
# Save parameters and then use them for later use(pooling of parameters that we can get from api responses maybe,
# and the use them afterwards). variable as in user input.
# question -> param type -> regex? -> condition?
# ${products} = get all products...
# here are the products: ${products}
# callable question
#
# Adding timed action to button instead of box.
#    Then if you have 2 buttons to the same box they will have different behavior.
#
# Leting the client decide which query params are pre defined and which are up to the user. (add features to query
# params)
#
#
# Send logs of user activity to our server and save the logs, to be able to present to the client.
#
# Start the conversation without /start
#
# Add init box that can initiate variables and other stuff
#
# make timer box\button visible to the user
#
#
# Plan: mannage one state with multipyl callbackquery handlers
#

from userGeneratedBot import UserGeneratedBot, BOX_TYPE_QUESTION, CallableFollowUp, CallablePrint, CallableAPI, \
    CallableQuestion

CALLABLE_QUESTION = "CallableQuestion"
CALLABLE_PRINT = "CallablePrint"
CALLABLE_FOLLOWUP = "CallableFollowUp"
CALLABLE_API = "CallableAPI"

class BotEngine:
    def __init__(self, bot_name=None, api_key=None, conv_handler=None, mongo_client=None):
        self.mongo_client = mongo_client
        self.bot_name = bot_name
        self.api_key = api_key
        self.conv_handler = conv_handler
        self.updater = Updater(api_key, use_context=True)
        # self.generated_bots = {}  # {'artem' : UserGeneratedBot() , 'daniel': UserGeneratedBot() }
        self.current_user_bot = None
        self.invalid_param = None
        self.follow_up = False
        self.is_editing = False

    def add_handler_entry_points(self, command_handler: Handler):
        self.conv_handler._entry_points.append(command_handler)

    def add_handler_states(self, user_defined_handler: Handler, handler_id: object):
        self.conv_handler._states[handler_id].append()

    def add_handler_fallbacks(self, user_defined_handler: Handler):
        self.conv_handler.fallbacks.append(user_defined_handler)

    def make_new_bot(self):
        created_bot = UserGeneratedBot()



    def create_callback(self, handler, message_handler_key):
        if handler["callback_type"] != CALLABLE_PRINT:
            obj = API(uri=handler["obj"], query_params=handler["obj"]["query_params"], expressions=handler["obj"]["expressions"])
            obj.message_to_user = handler["obj"]["message_to_user"]
            obj.key_expression = handler["obj"]["key_expression"]

        if handler["callback_type"] == CALLABLE_QUESTION:
                callback = CallableQuestion(obj, handler["msg"], next_state=message_handler_key)

        elif handler["callback_type"] == CALLABLE_API:
            callback = CallableAPI(msg=handler["msg"], obj=obj)

        elif handler["callback_type"] == CALLABLE_PRINT:
            callback = CallablePrint(msg=handler["msg"])

        elif handler["callback_type"] == CALLABLE_FOLLOWUP:
            callback = CallableFollowUp(obj=obj, next_state= handler["next_state"])

        callback.reply_buttons = handler["reply_buttons"]
        return callback

    def retrieve_states(self, raw_states):
        states = {1: []}
        pattern = 0
        message_handler_key = '1'
        for handler_type, handlers in raw_states.items():
            if handler_type == "query_handlers":
                for handler in handlers:
                    callback = self.create_callback(handler, message_handler_key)
                    states[1].append(CallbackQueryHandler(callback=callback, pattern='^' + str(pattern) + '$'))
                    pattern += 1

            elif handler_type == "message_handlers":
                for handler in handlers:
                    callback = self.create_callback(handler, message_handler_key)
                    states[message_handler_key] = [MessageHandler(callback=callback, filters=Filters.text)]
                    message_handler_key = str(int(message_handler_key) + 1)
        return states, pattern, message_handler_key

    def retrieve_api_endpoints(self, raw_api_endpoints):
        apis = []
        for api in raw_api_endpoints:
            api_obj = API(uri=api["uri"], query_params=api["query_params"], expressions=api["expressions"])
            api_obj.message_to_user = api["message_to_user"]
            api_obj.key_expression = api["key_expression"]
            apis.append(api_obj)
        return apis

    def retrieve_bot_pic(self, raw_bot_pic):
        bot_pic = botToPicture()
        # add buttons and such
        for node in raw_bot_pic["bot_nodes"]:
            bot_pic.bot_nodes[node["box"]] = bot_node(node["box"], node["msg"])
            bot_pic.bot_nodes[node["box"]].button_list += node["button_list"]

        for edge in raw_bot_pic["bot_edges"]:
            bot_pic.bot_edges.add(bot_edge(edge["box"], edge["button"], edge["destination"]))

        return bot_pic

    def build_bot(self, raw_bot):
        bot = UserGeneratedBot(api_key=raw_bot["api_key"])
        bot.states, bot.pattern, message_handler_key = self.retrieve_states(raw_bot["states"])
        bot.add_starting_point(raw_bot["entry_point_message"])
        bot.apis = self.retrieve_api_endpoints(raw_bot["api_endpoints"])
        #bot.message_handler_key = message_handler_key
        bot.bot_pic = self.retrieve_bot_pic(raw_bot["bot_pic"])
        bot.updater = Updater(token=bot.api_key, use_context=True)
        bot.dispatcher = bot.updater.dispatcher
        bot.conv_handler = ConversationHandler(
            entry_points=bot.entry_points,
            states=bot.states,
            fallbacks=[CommandHandler('cancel', bot.entry_points[0])],
        )
        bot.dispatcher.add_handler(bot.conv_handler)
        return bot

    def start(self, update: Update, context: CallbackContext) -> int:
        query = update.callback_query
        query.answer()
        self.current_user_bot = UserGeneratedBot()
        query.message.reply_text('Please enter the api key')
        return GET_API_KEY

    def get_api_key(self, update: Update, context: CallbackContext):
        api_key = update.message.text
        self.current_user_bot.api_key = api_key
        bot_username = self.get_bot_username(api_key)
        if bot_username != "":
            self.current_user_bot.bot_username = bot_username
            update.message.reply_text('Please enter you bots first words to the end user')
            return ADD_START
        else:
            update.message.reply_text('You have entered a wrong api key, please enter a valid one.')
            return GET_API_KEY

    def invalid_state_manegment(self, update: Update, context: CallbackContext):
        if self.invalid_param == 'API':
            update.message.reply_text('You have entered a wrong api key, please enter a valid one.')
            return GET_API_KEY

    def main_menu(self, update: Update, context: CallbackContext):
        query = Callback.check_query(update, context)
        add_user(self.mongo_client, update)
        text = 'Please choose one of the following actions'
        keyboard = \
            [
                [InlineKeyboardButton("Edit bot", callback_data=str(CHOOSE_BOT))],
                [InlineKeyboardButton("Create new bot", callback_data=str(CREATE_BOT))],
                [InlineKeyboardButton("View bots", callback_data=str(VIEW_BOT))],
                [InlineKeyboardButton("Help", callback_data=str(HELP))],
            ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.message.reply_text(text=text, reply_markup=reply_markup)
        return MAIN_MENU

    def choose_bot_to_edit(self, update: Update, context: CallbackContext):
        # Search bot int user bots using bot api key
        # set curr_bot to the found bot
        query = Callback.check_query(update, context)
        text = 'Please enter the API key of the bot that you want to edit'
        query.message.reply_text(text=text)
        return GET_BOT

    def get_bot(self, update: Update, context: CallbackContext):
        api_key = update.message.text
        bot_username = self.get_bot_username(api_key)
        if bot_username != "":
            raw_bot = get_bot(self.mongo_client, api_key, update.effective_user.id)
            if raw_bot != -1:
                bot = self.build_bot(raw_bot)
                self.current_user_bot = bot
                self.current_user_bot.bot_username = bot_username
            else:
                update.message.reply_text("We couldn't find a bot with this API key in your account\n"
                                          "Please try again")
                return GET_BOT
        else:
            update.message.reply_text('You have entered a wrong api key, please enter a valid one.')
            return GET_BOT
        self.is_editing = True
        return self.edit_bot(update, context)

    def view_bot(self):
        pass

    def edit_bot(self, update, context: CallbackContext):
        text = 'Please choose one of the following actions'
        keyboard = \
            [
                [InlineKeyboardButton("Add box", callback_data=str(CHOOSE_BOX))],
                [InlineKeyboardButton("Add edge", callback_data=str(ADD_EDGE))],
                [InlineKeyboardButton("Add box button", callback_data=str(ADD_BOX_BUTTON))],
                [InlineKeyboardButton("Add timed action", callback_data=str(TIMER_ACTION))],
                [InlineKeyboardButton("Print bot", callback_data=str(PRINT_BOT))],
                [InlineKeyboardButton("End building bot", callback_data=str(END))],
                [InlineKeyboardButton("Help", callback_data=str(HELP))],
            ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(text=text, reply_markup=reply_markup)
        return EDIT_BOT

    def define_bot_start(self, update: Update, context: CallbackContext):
        first_words = update.message.text
        user_generated_bot = self.current_user_bot
        user_generated_bot.add_starting_point(first_words)

        # self.current_user_bot.state_keys += 1
        update.message.reply_text('Please enter a conversation box using this notation:\n' + \
                                  'Each conversation box will have main text and buttons \n' + \
                                  '1)─────────────────────────┐\n' + \
                                  '│ Main text:               │\n' + \
                                  '│─────────────────────────│\n' + \
                                  '│1.1)Button1 │ 1.2)Button2 │\n' + \
                                  '└─────────────────────────┘\n' + \
                                  'you can connect boxes with the add edge command and the folowing notation: 1.1->2\n' + \
                                  'will connect box button 1.1 to box 2.\n' + \
                                  'The Start will be automatically linked to box #1, or you can skip the staring box.')

        return self.edit_bot(update, context)

    # save necessrray info of userGenerated bot to db in order to recreate it
    def init_user_bot(self, update: Update, context: CallbackContext):
        query = update.callback_query
        query.answer()
        if get_bot(self.mongo_client, self.current_user_bot.api_key, update.effective_user.id) != -1\
                and not self.is_editing:
            text = f"You already have a bot with this api key in your account\n" \
                   f"If you want to edit your bot, you can choose 'Edit Bot' in the menu"
        else:
            user_generated_bot = self.current_user_bot
            user_generated_bot.updater = Updater(user_generated_bot.api_key, use_context=True)
            user_generated_bot.dispatcher = user_generated_bot.updater.dispatcher
            user_generated_bot.conv_handler = ConversationHandler(
                entry_points=user_generated_bot.entry_points,
                states=user_generated_bot.states,
                fallbacks=[CommandHandler('cancel', self.current_user_bot.entry_points[0])],
            )

            # menu_buttons = [[InlineKeyboardButton(text='Create a new Bot', callback_data=str(GET_API_KEY))]]
            # menu_keyboard = InlineKeyboardMarkup(menu_buttons)

            user_generated_bot.dispatcher.add_handler(user_generated_bot.conv_handler)
            if self.is_editing:
                update_bot(self.mongo_client, update, user_generated_bot)
            else:
                add_bot(self.mongo_client, update, user_generated_bot)
            text = f"Your bot is now initialized! click the link to interact with your bot!\n" \
                   f"http://telegram.me/{user_generated_bot.bot_username}"

            user_generated_bot.updater.start_polling()

            # user_generated_bot.updater.idle()
            # new_bot = threading.Thread(target=self.start_user_bot, args=(user_generated_bot,))
            # new_bot.start()

        query.message.reply_text(text=text)
        return self.main_menu(update, context)  # Todo: change

    def get_bot_username(self, api_key):
        """
        Returns the username of the bot if the request is valid
        else empty string
        """
        check_url = f'https://api.telegram.org/bot{api_key}/getMe'
        response = requests.get(check_url)
        if response.status_code == 200:
            return response.json()['result']['username']
        else:
            return ""

    def add_edge(self, update: Update, context: CallbackContext):
        query = update.callback_query
        query.answer()
        text = 'Please enter the edge you would like to add: \n I.E: 1.2->2 (from box #1 button #2 will direct you ' \
               'to box #2)'
        query.message.reply_text(text=text)
        return ADD_EDGE2

    def add_edge2(self, update: Update, context: CallbackContext):
        response = update.message.text  # response =  1.2->2
        text = ''
        try:
            from_edge, to_edge = re.split('->', response)
            user_generated_bot = self.current_user_bot
            from_edge = from_edge.split('.')
            from_edge = [int(i) for i in from_edge]
            to_edge = int(to_edge)
            user_generated_bot.add_edge(from_edge, to_edge)
            text = 'Edge added successfully!'
        except ValueError:
            text = 'too much parameters were given, please try again'
        except:
            text = 'Wrong parameters were given, please try again'
        update.message.reply_text(text=text)
        return self.edit_bot(update, context)

    def choose_box(self, update: Update, context: CallbackContext):
        query = update.callback_query
        query.answer()
        text = 'Please Choose one of the following box purpose \n' \
               'Text box: Choose the text you want show to the user.\n' \
               'Api box: Choose an API you want show to the user.\n'
        keyboard = \
            [
                [InlineKeyboardButton("Add text box", callback_data=str(ADD_TEXT_BOX))],
                [InlineKeyboardButton("Add API fetch box", callback_data=str(ADD_API_BOX))],
            ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.message.edit_text(text=text, reply_markup=reply_markup)
        return BOX_DECISION

    def add_text_box(self, update: Update, context: CallbackContext):
        query = update.callback_query
        query.answer()
        text = 'Please enter the box msg'
        query.message.reply_text(text=text)
        return ADD_TEXT_BOX2

    def add_text_box2(self, update: Update, context: CallbackContext):
        text = ''
        box_msg = update.message.text
        user_generated_bot = self.current_user_bot
        try:
            box_number = user_generated_bot.add_box(box_msg, 'text')
            text = f'The box you created has the number of {box_number}'
        except:
            text = 'Invalid box number was given. please try again'
        update.message.reply_text(text=text)
        return self.edit_bot(update, context)

    def add_box_button(self, update: Update, context: CallbackContext):
        query = update.callback_query
        query.answer()
        text = 'Please enter the number of box'
        query.message.reply_text(text=text)
        return ADD_BOX_BUTTON2

    def add_box_button2(self, update: Update, context: CallbackContext):
        text = ''
        box_number = update.message.text
        try:
            box_number = int(box_number)
            user_generated_bot = self.current_user_bot
            box_is_valid = user_generated_bot.is_valid_box(box_number)
            if box_is_valid:
                text = 'Please enter the text that will be shown on the button'
                user_generated_bot.build_button['box'] = box_number
            else:
                text = 'Number box given is in use, please give another number or delete the number box given.'
        except Exception as e:
            print(e)
            text = 'Invalid box number was given. please try again'
            update.message.reply_text(text=text)
            return self.edit_bot(update, context)
        update.message.reply_text(text=text)
        return ADD_BOX_BUTTON3

    def add_box_button3(self, update: Update, context: CallbackContext):  # text on button
        user_generated_bot = self.current_user_bot
        box_number = user_generated_bot.build_button['box']
        button_text = update.message.text
        button_number_created = user_generated_bot.add_box_button(box_number, button_text)
        text = f'Button #{button_number_created} Added successfully to box #{box_number}'
        update.message.reply_text(text=text)
        return self.edit_bot(update, context)

    def print_bot(self, update: Update, context: CallbackContext):
        query = update.callback_query
        query.answer()
        user_generated_bot = self.current_user_bot
        file_path = user_generated_bot.show_bot(str(update.effective_user.id))
        print(file_path)
        query.message.reply_photo(photo=open(file_path, 'rb'), caption='Here is your bot!')
        return self.edit_bot(query, context)

    def start_api_flow(self, update: Update, context: CallbackContext):
        query = update.callback_query
        query.answer()
        text = "We will now ask you some basic questions regarding " \
               "your API endpoint\n\n" \
               "What is the base endpoint of the API you want to integrate"
        query.message.reply_text(text=text)
        return GET_BASE_API

    def get_base_api(self, update: Update, context: CallbackContext):
        base_url = update.message.text
        user_generated_bot = self.current_user_bot
        user_generated_bot.apis.append(API())
        user_generated_bot.apis[-1].uri = base_url
        request = user_generated_bot.apis[-1].get_api_response()
        if request.status_code == 200:
            text = "Nice!\n" \
                   "Now we need to get the query parameters that this endpoint expects to get\n" \
                   "Please write key value pairs separated by & (For example: destination=israel&origin=Germany)\n" \
                   "The request will be made according to the values the end user will input\n" \
                   "If there are no query parameters type None"
            # Should we infer the button text from the endpoint or ask the user
            # For not lets infer the first endpoint
            update.message.reply_text(text=text)
            return GET_QUERY_PARAMS

        else:
            text = f"We got a {request.status_code} response code from this uri" \
                   "Please make sure you passed the right uri and try again\n"
            update.message.reply_text(text=text)
            return self.get_base_api(update, context)

    # def get_endpoint(self, update: Update, context: CallbackContext):
    #     endpoint = update.message.text
    #     if not endpoint.startswith('/'):
    #         endpoint = '/' + endpoint
    #     user_generated_bot = self.current_user_bot
    #     if user_generated_bot.apis[-1].uri.endswith('/'):
    #         user_generated_bot.apis[-1].uri += endpoint.lstrip('/')
    #     else:
    #         user_generated_bot.apis[-1].uri += endpoint
    #
    #
    #     update.message.reply_text(text=text)
    #     return GET_QUERY_PARAMS

    def trim_long_response(self, response):
        start = f'{response[1:100]}'
        mid = '.\n.\n.\n.\n.\n.\n.\n'
        end = f'{response[-100:-2]}'
        return f'{start}{mid}{end}'

    def get_query_params(self, update: Update, context: CallbackContext):
        # First validate that it matches the desired pattern
        # key:value, key:value ...
        user_generated_bot = self.current_user_bot
        if update.message.text != 'None':
            query_params = [key_value.strip() for key_value in update.message.text.split('&')]
            for query_param in query_params:
                key, value = query_param.split("=", 1)
                user_generated_bot.apis[-1].query_params[key] = value

        request = user_generated_bot.apis[-1].get_api_response()
        # Validate it's a Json response, currently we will support only Json
        if request.status_code == 200:
            pretty_response = json.loads(request.text)
            user_generated_bot.apis[-1].response = pretty_response
            pretty_response = json.dumps(pretty_response, indent=2)
            if len(pretty_response) > 4000:
                pretty_response = self.trim_long_response(json.dumps(pretty_response, indent=2))
            text = "We just made a request with the parameters that you provided " \
                   "and got the following response\n\n" \
                   f"{pretty_response}"
            text_get_key = "What keys would you like to show the user from this response?\n" \
                           "Write Json expressions which evaluate to your keys separated by commas, for example: [origin], " \
                           "[destination][flight_num], etc...\n " \
                           "If the key are inside an array you need to index it, for example: [0][origin], " \
                           "[destination][1]\n" \
                           "You can use nesting for dictionaries as well, for example: [data][name], [0][data][time]\n" \
                           "You can also type in expressions which are arrays and we will get all the keys there\n" \
 \
                # In general expression maps to the value of the key
            update.message.reply_text(text=text)
            update.message.reply_text(text=text_get_key)
            return GET_KEY_FROM_RESPONSE
        else:
            text = f"We got a {request.status_code} response code from this uri with those parameters" \
                   "Please make sure you passed the right parameters and try again\n"
            update.message.reply_text(text=text)
            return GET_QUERY_PARAMS

    def get_keys_to_retrieve(self, update: Update, context: CallbackContext):
        expressions = [expression.strip() for expression in update.message.text.split(',')]
        user_generated_bot = self.current_user_bot
        user_generated_bot.apis[-1].expressions = expressions

        try:
            user_generated_bot.apis[-1].validate_keys()
        except Exception as e:
            error_message = "We couldn't validate one of your expressions\n" \
                            f"Original error is: \n {e}\n" \
                            f"Please try to write those expressions again according to the rules"
            update.message.reply_text(text=error_message)
            return GET_KEY_FROM_RESPONSE

        key_expression_mapping = user_generated_bot.apis[-1].key_expression_map()
        ref_keys_text = "Your keys have been validated and we have saved them\n" \
                        "Here is the key-expression mapping (In this format {Key} = {Expression}):\n" \
                        f"{key_expression_mapping}"
        next_stage_text = "How would you like to present the data to the user?\n" \
                          "notice that you can reference a key like this ${key},\n " \
                          "And we will get the value out of the expression that matches the key at run time\n" \
                          "For example: Your flight leaves at ${time} from ${destination} to ${origin}"

        update.message.reply_text(text=ref_keys_text)
        update.message.reply_text(text=next_stage_text)
        return GET_MESSAGE_TO_USER

    def get_message_to_user(self, update: Update, context: CallbackContext):
        user_generated_bot = self.current_user_bot
        # TODO: Validate that this is a valid message
        user_generated_bot.apis[-1].message_to_user = update.message.text
        text = f'The API Endpoint was created successfully\n ' \
               f'The box you created has the number of: '
        if not user_generated_bot.apis[-1].query_params:
            box_number = user_generated_bot.add_box(box_msg='api call', box_type='api',
                                                    api_obj=user_generated_bot.apis[-1])
            text += str(box_number)
        else:
            question = "Please provide us with the following query parameters values: \n"
            box_number = user_generated_bot.add_box(box_msg=question, box_type=BOX_TYPE_QUESTION
                                                    , api_obj=user_generated_bot.apis[-1])

            api_box_number = user_generated_bot.add_box(box_msg='Make api call', box_type='api',
                                                        api_obj=user_generated_bot.apis[-1])
            box_button_num = user_generated_bot.add_box_button(box_number, 'Get user query params')
            user_generated_bot.add_edge((box_number, box_button_num), api_box_number)
            api_box_callback = user_generated_bot.find_return_callabck(api_box_number)
            user_generated_bot.add_message_handler_state(obj=user_generated_bot.apis[-1], return_callback=api_box_callback)
            text += str(box_number)
            text += f'\nand {api_box_number}# for the api box'
        # if not valid message recursively come back to this function
        # else we finish the process and create new callbackquery handler
        update.message.reply_text(text=text)
        return self.edit_bot(update, context)

    def get_authorization_header(self, update: Update, context: CallbackContext):
        pass

    def timer_action(self, update: Update, context: CallbackContext):
        user_generated_bot = self.current_user_bot
        query = update.callback_query
        query.answer()
        text = 'The timer will be activated from when the moment the user will reach that timer-action-box.\n' \
               'Here is your bot, please choose the box to give it the time-action ability.'
        file_path = user_generated_bot.show_bot(file_name=str(update.effective_user.id))
        query.message.reply_photo(photo=open(file_path, 'rb'), caption=text)
        return TIMER_ACTION2

    def timer_action2(self, update: Update, context: CallbackContext):
        user_generated_bot = self.current_user_bot
        user_box_selected = int(update.message.text)
        valid_box = user_generated_bot.is_valid_box(user_box_selected)
        if valid_box:
            user_generated_bot.user_variables['box-timer'] = valid_box
            update.message.reply_text(text='Please enter the interval and finish time for this polling\n'
                                           'Interval in seconds\n'
                                           'Example: 10')
            return TIMER_ACTION3
        else:
            update.message.reply_text(text='Wrong box was given please try again')
            return TIMER_ACTION2

    def timer_action3(self, update: Update, context: CallbackContext):
        user_generated_bot = self.current_user_bot
        inetrval_endtime = update.message.text
        try:
            # inetrval_endtime = inetrval_endtime.split(',')
            # inetrval_endtime = [i.strip() for i in inetrval_endtime]
            # endtime = datetime.strptime(inetrval_endtime[1], '%d/%m/%Y')
            interval = int(inetrval_endtime)
            user_generated_bot.attach_timer_to_box(user_generated_bot.user_variables['box-timer'],
                                                   interval)
            update.message.reply_text(text='Timer attached successfully!')
        except Exception as s:
            print(s)
        return self.edit_bot(update, context)


# 3
# times to run, start , interval, finish , action/box. outcome?
#

ADD_START = 1
ADD_QUESTION = 2
GET_API_KEY = 3
END = 8
EDIT_BOT = 10
VIEW_BOT = 36
GET_BOT = 36
CREATE_BOT = 37
CHOOSE_BOT = 38
START_AGAIN = 11
ADD_EDGE = 13
ADD_EDGE2 = 14
ADD_TEXT_BOX = 15
ADD_TEXT_BOX2 = 16
ADD_BOX_BUTTON = 18
PRINT_BOT = 19
HELP = 20
MAIN_MENU = 21
ADD_BOX_BUTTON2 = 22
ADD_BOX_BUTTON3 = 23
GET_KEY_FROM_RESPONSE = 24
GET_MESSAGE_TO_USER = 25
GET_QUERY_PARAMS = 26
GET_ENDPOINT = 27
GET_BASE_API = 28
START_API_FLOW = 29
CHOOSE_BOX = 30
BOX_DECISION = 31
ADD_API_BOX = 32
TIMER_ACTION2 = 33
TIMER_ACTION3 = 34
TIMER_ACTION = 35


def main():
    import os
    os.environ["PATH"] += os.pathsep + 'C:/Program Files/Graphviz/bin'
    client = pymongo.MongoClient(
        "mongodb+srv://ArtemK:Art7302it%21@cluster0.xfxqr.mongodb.net/Bonter?retryWrites=true&w=majority")
    mainbot = BotEngine(bot_name='engineBot', api_key="1743828272:AAF_0DG0-bjmp5nb6TvjcaYXU08EHvTchQQ",
                        conv_handler=None, mongo_client=client)
    dispatcher = mainbot.updater.dispatcher
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', mainbot.main_menu)],
        states={
            MAIN_MENU: [
                CallbackQueryHandler(mainbot.choose_bot_to_edit, pattern='^' + str(CHOOSE_BOT) + '$'),
                CallbackQueryHandler(mainbot.view_bot, pattern='^' + str(VIEW_BOT) + '$'),
                CallbackQueryHandler(mainbot.start, pattern='^' + str(CREATE_BOT) + '$'),
            ],
            GET_BOT: [MessageHandler(Filters.text, mainbot.get_bot)],
            GET_API_KEY: [MessageHandler(Filters.text, mainbot.get_api_key)],
            ADD_START: [MessageHandler(Filters.text, mainbot.define_bot_start)],
            EDIT_BOT: [
                CallbackQueryHandler(mainbot.choose_box, pattern='^' + str(CHOOSE_BOX) + '$'),
                CallbackQueryHandler(mainbot.add_box_button, pattern='^' + str(ADD_BOX_BUTTON) + '$'),
                CallbackQueryHandler(mainbot.add_edge, pattern='^' + str(ADD_EDGE) + '$'),
                CallbackQueryHandler(mainbot.print_bot, pattern='^' + str(PRINT_BOT) + '$'),
                CallbackQueryHandler(mainbot.init_user_bot, pattern='^' + str(END) + '$'),
                CallbackQueryHandler(mainbot.timer_action, pattern='^' + str(TIMER_ACTION) + '$'),
            ],
            BOX_DECISION: [
                CallbackQueryHandler(mainbot.add_text_box, pattern='^' + str(ADD_TEXT_BOX) + '$'),
                CallbackQueryHandler(mainbot.start_api_flow, pattern='^' + str(ADD_API_BOX) + '$'),
            ],
            GET_BASE_API: [MessageHandler(Filters.text, mainbot.get_base_api)],
            # GET_ENDPOINT: [MessageHandler(Filters.text, mainbot.get_endpoint)],
            GET_QUERY_PARAMS: [MessageHandler(Filters.text, mainbot.get_query_params)],
            GET_KEY_FROM_RESPONSE: [MessageHandler(Filters.text, mainbot.get_keys_to_retrieve)],
            GET_MESSAGE_TO_USER: [MessageHandler(Filters.text, mainbot.get_message_to_user)],
            ADD_TEXT_BOX2: [MessageHandler(Filters.text, mainbot.add_text_box2)],
            ADD_EDGE2: [MessageHandler(Filters.text, mainbot.add_edge2)],
            ADD_BOX_BUTTON2: [MessageHandler(Filters.text, mainbot.add_box_button2)],
            ADD_BOX_BUTTON3: [MessageHandler(Filters.text, mainbot.add_box_button3)],
            TIMER_ACTION2: [MessageHandler(Filters.text, mainbot.timer_action2)],
            TIMER_ACTION3: [MessageHandler(Filters.text, mainbot.timer_action3)],
        },
        fallbacks=[CommandHandler('cancel', mainbot.start)],
    )
    dispatcher.add_handler(conv_handler)
    mainbot.updater.start_polling()
    # mainbot.updater.idle()


if __name__ == '__main__':
    main()

# Daniel : 1489264800:AAEgoIvqwoN3K1UZL6ghTY5ixZvUcl6qI_E
# Artem : 1743828272:AAF_0DG0-bjmp5nb6TvjcaYXU08EHvTchQQ

# public apis: https://github.com/public-apis/public-apis
# https://api.coincap.io/v2/assets  bitcoin api

# stam bot : 1729539488:AAFxZf8IItBf8dcrNUIW2albguVpHUvm5TU
