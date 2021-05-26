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
from callback import *
import re
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
# 1) API , visualisation
# 2) aswer with .. (text,image, voice?)
# 3) impove chat flow, UI UX...
# 4) edit bot: remove edge, remove box, remove button
# 4) timer
# 5) Basic Api integrations with calender, gmail
# 6) deploy ,check if bot works with multiple users /clients ,
# 7) bot mangenment system?
# 7) data visualisation
# dinamic text , , poll? , group admin? , ,
# Haloka:
# 1) Adding a few commands
# 2) nested commands
# 3) command type
# 4) better UX/UI - improve botEngine convo and user freindly
# 5) DB
# press here to learn more

# Plan: mannage one state with multipyl callbackquery handlers
#
#

class CallablePrint:
    def __init__(self, msg, next_state=1):
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
        update.message.reply_text(text=self.msg)
        if self.reply_buttons:
            print(self.reply_buttons)
            keyboard = InlineKeyboardMarkup([self.reply_buttons])
            update.message.reply_text(text=self.msg, reply_markup=keyboard)
        return self.next_state


class CallableAPI:
    def __init__(self, uri, next_state):
        self.uri = uri
        self.next_state = next_state
        self.replay_buttons = []
        self.json_value = None

    def add_button(self, button):
        self.replay_buttons.append(button)

    def check_query(self, update: Update, context: CallbackContext):
        query = update.callback_query
        if query is not None:
            query.answer()
            return query
        else:
            return update

    def __call__(self, update: Update, context: CallbackContext):
        update = self.check_query(update, context)
        response = requests.get(self.uri)
        update.message.reply_text(text=self.msg)
        if self.replay_buttons:
            print(self.replay_buttons)
            keyboard = InlineKeyboardMarkup(self.replay_buttons)
            text = "What would you like to do next"
            update.message.reply_text(text=text, reply_markup=keyboard)
        return self.next_state


# class CallableAPI(CallablePrint):
#     def __init__(self, api_url, key, msg, next_state):
#         super(CallableAPI, self).__init__()


class UserGeneratedBot:
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
        self.commands = []
        self.button_key = 0
        self.build_button = {}
        self.edges = set()
        self.nodes = {}
        self.pattern = 0
        self.bot_pic = botToPicture()
        self.user_variables = {}

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
        new_edge = bot_edge(box, from_button, destinationBox - 1)
        if new_edge not in self.edges:
            self.edges.add(new_edge)
        else:
            raise Exception('Cannot add the same edge twice')
        box_callback = self.states[self.state_key][box].callback
        box_buttons = box_callback.reply_buttons
        inlinekeyBoard = box_buttons[from_button]
        inlinekeyBoard.callback_data = str(destinationBox - 1)

    def add_box(self, box_msg):
        if self.state_key not in self.states:
            self.states[self.state_key] = []
        self.states[self.state_key].append(
            CallbackQueryHandler(CallablePrint(msg=box_msg),
                                 pattern='^' + str(self.pattern) + '$')
        )
        self.nodes[self.pattern] = bot_node(self.pattern, box_msg)
        self.pattern += 1
        return self.pattern

    def add_box_button(self, box_number, button_text):
        callbackqueryArray = self.states[self.state_key]
        box_number -= 1
        node = self.nodes[box_number]
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
            if callback.pattern.pattern == pattern:
                return True
        return False

    def show_bot(self, file_name):
        return self.bot_pic.render_graph(self.nodes.values(), self.edges, file_name)


class BotEngine:
    def __init__(self, bot_name=None, bot_api_key=None, conv_handler=None):
        self.bot_name = bot_name
        self.bot_api_key = bot_api_key
        self.conv_handler = conv_handler
        self.updater = Updater(bot_api_key, use_context=True)
        self.generated_bots = {}  # {'artem' : UserGeneratedBot() , 'daniel': UserGeneratedBot() }
        self.invalid_param = None
        self.follow_up = False

    def add_handler_entry_points(self, command_handler: Handler):
        self.conv_handler._entry_points.append(command_handler)

    def add_handler_states(self, user_defined_handler: Handler, handler_id: object):
        self.conv_handler._states[handler_id].append()

    def add_handler_fallbacks(self, user_defined_handler: Handler):
        self.conv_handler.fallbacks.append(user_defined_handler)

    def make_new_bot(self):
        created_bot = UserGeneratedBot()

    def start(self, update: Update, context: CallbackContext) -> int:
        self.generated_bots[update.effective_user.id] = UserGeneratedBot()
        update.message.reply_text('Please enter the api key')
        return GET_API_KEY

    def get_api_key(self, update: Update, context: CallbackContext):
        api_key = update.message.text
        self.generated_bots[update.effective_user.id].bot_api_key = api_key
        if self.is_valid_API_key(api_key, update.effective_user.id):
            update.message.reply_text('Please enter you bots first words to the end user')
            return ADD_START
        else:
            pass
            update.message.reply_text('You have entered a wrong api key, please enter a valid one.')
            return GET_API_KEY

    def invalid_state_manegment(self, update: Update, context: CallbackContext):
        if self.invalid_param == 'API':
            update.message.reply_text('You have entered a wrong api key, please enter a valid one.')
            return GET_API_KEY

    def main_menu(self, update, context: CallbackContext):
        text = 'Please choose one of the following actions'
        keyboard = \
            [

                [InlineKeyboardButton("Add box", callback_data=str(ADD_BOX))],
                [InlineKeyboardButton("Add edge", callback_data=str(ADD_EDGE))],
                [InlineKeyboardButton("Add box button", callback_data=str(ADD_BOX_BUTTON))],
                [InlineKeyboardButton("Print bot", callback_data=str(PRINT_BOT))],
                [InlineKeyboardButton("End building bot", callback_data=str(END))],
                [InlineKeyboardButton("Help", callback_data=str(HELP))],
            ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(text=text, reply_markup=reply_markup)
        return SELECTION

    def define_bot_start(self, update: Update, context: CallbackContext):
        first_words = update.message.text
        user_generated_bot = self.generated_bots[update.effective_user.id]
        user_generated_bot.add_starting_point(first_words)

        # self.generated_bots[update.effective_user.id].state_keys += 1
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

        return self.main_menu(update, context)

    def end_build_bot(self, update: Update, context: CallbackContext):
        query = update.callback_query
        query.answer()
        user_generated_bot = self.generated_bots[update.effective_user.id]
        user_generated_bot.updater = Updater(user_generated_bot.bot_api_key, use_context=True)
        user_generated_bot.dispatcher = user_generated_bot.updater.dispatcher
        user_generated_bot.conv_handler = ConversationHandler(
            entry_points=user_generated_bot.entry_points,
            states=user_generated_bot.states,
            fallbacks=[CommandHandler('cancel', self.generated_bots[update.effective_user.id].entry_points[0])],
        )
        text = f"Your bot is now initialized! click the link to interact with your bot!\n" \
               f"http://telegram.me/{user_generated_bot.bot_username}"
        menu_buttons = [[InlineKeyboardButton(text='Create a new Bot', callback_data=str(GET_API_KEY))]]
        menu_keyboard = InlineKeyboardMarkup(menu_buttons)
        query.message.reply_text(text=text, reply_markup=menu_keyboard)
        user_generated_bot.dispatcher.add_handler(user_generated_bot.conv_handler)
        print(user_generated_bot.states)
        user_generated_bot.updater.start_polling()
        # user_generated_bot.updater.idle()
        # new_bot = threading.Thread(target=self.start_user_bot, args=(user_generated_bot,))
        # new_bot.start()
        return START_AGAIN  # Todo: change

    def is_valid_API_key(self, api_key, user_id):
        check_url = f'https://api.telegram.org/bot{api_key}/getMe'
        response = requests.get(check_url)
        if response.status_code == 200:
            self.generated_bots[user_id].bot_username = response.json()['result']['username']
            return True
        else:
            return False

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
            user_generated_bot = self.generated_bots[update.effective_user.id]
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
        return self.main_menu(update, context)

    def add_follow_up(self, update: Update, context: CallbackContext):
        query = update.callback_query
        query.answer()
        user_generated_bot = self.generated_bots[update.effective_user.id]
        last_key = user_generated_bot.state_keys
        user_generated_bot.state_keys += 1
        user_generated_bot.states[last_key][-1].callback.next_state = user_generated_bot.state_keys
        query.message.reply_text(
            'Please enter a command that the bot will respond to (will be shown as a button)\n (this is a nested '
            'command)')
        self.follow_up = True
        return ADD_COMMAND

    def add_box(self, update: Update, context: CallbackContext):
        query = update.callback_query
        query.answer()
        text = 'Please enter the box msg'
        query.message.reply_text(text=text)
        return ADD_BOX2

    def add_box2(self, update: Update, context: CallbackContext):
        text = ''
        box_msg = update.message.text
        user_generated_bot = self.generated_bots[update.effective_user.id]
        try:
            box_number = user_generated_bot.add_box(box_msg)
            text = f'The box you created has the number of {box_number}'
        except:
            text = 'Invalid box number was given. please try again'
        update.message.reply_text(text=text)
        return self.main_menu(update, context)

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
            user_generated_bot = self.generated_bots[update.effective_user.id]
            box_is_valid = user_generated_bot.is_valid_box(box_number)
            if box_is_valid:
                text = 'Please enter the text that will be shown on the button'
                user_generated_bot.build_button['box'] = box_number
            else:
                text = 'Number box given is in use, please give another number or delete the number box given.'
        except Exception as e:
            print(e)
            text = 'Invalid box number was given. please try again'
            return self.main_menu(update, context)
        update.message.reply_text(text=text)
        return ADD_BOX_BUTTON3

    def add_box_button3(self, update: Update, context: CallbackContext):  # text on button
        user_generated_bot = self.generated_bots[update.effective_user.id]
        box_number = user_generated_bot.build_button['box']
        button_text = update.message.text
        button_number_created = user_generated_bot.add_box_button(box_number, button_text)
        text = f'Button #{button_number_created} Added successfully to box #{box_number}'
        update.message.reply_text(text=text)
        return self.main_menu(update, context)

    def print_bot(self, update: Update, context: CallbackContext):
        query = update.callback_query
        query.answer()
        user_generated_bot = self.generated_bots[update.effective_user.id]
        file_path = user_generated_bot.show_bot(str(update.effective_user.id))
        print(file_path)
        query.message.reply_photo(photo=open(file_path, 'rb'), caption='Here is your bot!')
        return self.main_menu(query, context)


ADD_START = 1
ADD_QUESTION = 2
GET_API_KEY = 3
INVALID_STATE = 4
ADD_COMMAND = 5
ADD_RESPONSE = 6
MENU = 7
END = 8
ASK_COMMAND = 9
SELECTION = 10
START_AGAIN = 11
ADD_FOLLOW_UP = 12
ADD_EDGE = 13
ADD_EDGE2 = 14
ADD_BOX = 15
ADD_BOX2 = 16
ADD_BOX3 = 17
ADD_BOX_BUTTON = 18
PRINT_BOT = 19
HELP = 20
MAIN_MENU = 21
ADD_BOX_BUTTON2 = 22
ADD_BOX_BUTTON3 = 23


def main():
    mainbot = BotEngine(bot_name='engineBot', bot_api_key="1489264800:AAEgoIvqwoN3K1UZL6ghTY5ixZvUcl6qI_E",
                        conv_handler=None)
    dispatcher = mainbot.updater.dispatcher
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', mainbot.start)],
        states={
            GET_API_KEY: [MessageHandler(Filters.text, mainbot.get_api_key)],
            ADD_START: [MessageHandler(Filters.text, mainbot.define_bot_start)],
            SELECTION: [
                CallbackQueryHandler(mainbot.add_box, pattern='^' + str(ADD_BOX) + '$'),
                CallbackQueryHandler(mainbot.add_box_button, pattern='^' + str(ADD_BOX_BUTTON) + '$'),
                CallbackQueryHandler(mainbot.add_follow_up, pattern='^' + str(ADD_FOLLOW_UP) + '$'),
                CallbackQueryHandler(mainbot.add_edge, pattern='^' + str(ADD_EDGE) + '$'),
                CallbackQueryHandler(mainbot.print_bot, pattern='^' + str(PRINT_BOT) + '$'),
                CallbackQueryHandler(mainbot.end_build_bot, pattern='^' + str(END) + '$'),
            ],
            ADD_BOX2: [MessageHandler(Filters.text, mainbot.add_box2)],
            ADD_EDGE2: [MessageHandler(Filters.text, mainbot.add_edge2)],
            ADD_BOX_BUTTON2: [MessageHandler(Filters.text, mainbot.add_box_button2)],
            ADD_BOX_BUTTON3: [MessageHandler(Filters.text, mainbot.add_box_button3)],
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
