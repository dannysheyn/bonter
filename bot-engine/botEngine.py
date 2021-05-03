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
import threading
import os

# TODO: Flights, RSS,Group chats + bots,Group Notification, Basic Api integrations with calender, gmail and more., Polls, Order bot? ,data to Graps , predefined demos
# TODO: 1) fix the code.
# TODO: 2) MOVE to regular Buttons
# TODO NEXT TIME: add queryHandler to our bot can be hardcoded. checks and optimizations,
#  and looking into how to upgrade the fetures in the bot engine ( at least add command to a command) i.e nested commands.
# TODO: maybe api action?
# TODO: defult end bot,

# Haloka:
# 1) Adding a few commands
# 2) nested commands
# 3) command type
# 4) better UX/UI - improve botEngine convo and user freindly
# 5) DB
#press here to learn more


class CallablePrint:
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
        if self.replay_buttons:
            print(self.replay_buttons)
            keyboard = ReplyKeyboardMarkup(self.replay_buttons)
            text = "What would you like to do next"
            update.message.reply_text(text=text, reply_markup=keyboard)
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
        self.state_keys = 0
        self.commands = []
        self.button_key = 0

    def add_new_command(self):
        if self.state_keys not in self.states:
            self.states[self.state_keys] = []
        self.state_keys += 1

    def add_button_command(self, state_key, callback, button_text, returned_button_key):
        callback.add_button([InlineKeyboardButton(button_text, callback_data=str(self.button_key))])
        self.states[state_key].append(
            CallbackQueryHandler(callback, pattern='^' + str(self.button_key) + '$')
        )

    # def print_conversation(self):
    #     conversetion = ''
    #     for entry_point in self.entry_points:
    #         conversetion += entry_point.callback.msg
    #         conversetion += '\n|\n'
    #         conversetion += 'V\n'
    #     for state in self.states.values():
    #         if isinstance(state, list):
    #             for callbackQueryHandler in state:
    #                 reply_buttons = callbackQueryHandler.callback.replay_buttons
    #                 for reply_button in reply_buttons:
    #                     for reply in reply_button:
    #                         conversetion += str.format('{0}\n', '_' * (len(reply.text) + 2))
    #                         conversetion += str.format('|{0}|\n', reply.text)
    #                         conversetion += str.format('{0}\n', ' ͞' * (len(reply.text) * 2))
    #                         conversetion += '\n|\n'
    #                         conversetion += 'V\n'
    #     return conversetion


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

    def define_bot_start(self, update: Update, context: CallbackContext):
        first_words = update.message.text
        return_key = self.generated_bots[update.effective_user.id].state_keys
        self.generated_bots[update.effective_user.id].entry_points = [
            CommandHandler('start', CallablePrint(first_words, return_key))
        ]
        # self.generated_bots[update.effective_user.id].state_keys += 1
        update.message.reply_text('Please enter a command that the bot will respond to (will be shown as a button)')
        return ADD_COMMAND

    def ask_command(self, update: Update, context: CallbackContext):
        query = update.callback_query
        query.answer()
        query.edit_message_text('Currently the bot knows this commands')
        counter = 1
        message = ""
        for command in self.generated_bots[update.effective_user.id].commands:
            message += f"{counter}. {command}\n"
            counter += 1

        query.message.reply_text(text=message)
        query.message.reply_text('Please type a new command that the bot will respond to (will be shown as a button)')
        return ADD_COMMAND

    def add_command(self, update: Update, context: CallbackContext):
        command = update.message.text
        self.generated_bots[update.effective_user.id].commands.append(command)
        update.message.reply_text('What will the bot answer to this command?')
        return ADD_RESPONSE

    def add_response(self, update: Update, context: CallbackContext):
        response = update.message.text
        user_generated_bot = self.generated_bots[update.effective_user.id]
        last_command = user_generated_bot.commands[-1]
        last_key = user_generated_bot.state_keys
        # last_command = products..
        # respose = iphone3.., ..,
        user_generated_bot.states[last_key] = [MessageHandler(filters=Filters.text, callback=Button('',(last_key + 1),[last_command]))]  #button handler
        user_generated_bot.state_keys += 1
        last_key = user_generated_bot.state_keys
        user_generated_bot.states[last_key] = [MessageHandler(filters=Filters.text, callback=Answer(response,last_key))] # answer handler
        # keyboard_callback = CallbackQueryHandler(CallablePrint(response, last_key),
        #                                          pattern='^' + str(user_generated_bot.button_key) + '$')
        # if last_key not in user_generated_bot.states:
        #     user_generated_bot.states[last_key] = []
        # user_generated_bot.states[last_key].append(keyboard_callback)
        # user_generated_bot.states[last_key][-1].callback.add_button(
        #     [InlineKeyboardButton(text=last_command, callback_data=str(user_generated_bot.button_key))]
        # )
        # if self.follow_up == False:
        #     user_generated_bot.entry_points[0].callback.add_button(
        #         [InlineKeyboardButton(text=last_command, callback_data=str(user_generated_bot.button_key))]
        #     )
        #     user_generated_bot.button_key += 1
        #     self.follow_up = True
        menu_text = 'what do you want to do next?\n' \
                    'please choose one of the following:'
        menu_buttons = [[InlineKeyboardButton(text='Add new command', callback_data=str(ASK_COMMAND))],
                        [InlineKeyboardButton(text='Add follow up question to this command',
                                              callback_data=str(ADD_FOLLOW_UP))],
                        [InlineKeyboardButton(text='End building bot', callback_data=str(END))]
                        ]
        menu_keyboard = InlineKeyboardMarkup(menu_buttons)
        update.message.reply_text(text=menu_text, reply_markup=menu_keyboard)
        return SELECTION

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
        #self.make_back_to_menu_button(user_generated_bot)
        query.message.reply_text(text=text, reply_markup=menu_keyboard)
        # for key, state in list(user_generated_bot.states.items()):
        #     for s in state:
        #         print(f'key of this callback: {key}')
        #         print(f'callback will say: {s.callback.msg}')
        #         print(f'callback will return: {s.callback.next_state}')
        #         print(f'buttons are:')
        #         for buttons in s.callback.replay_buttons:
        #             for button in buttons:
        #                 print(f'text:{button["text"]} will return: {button["callback_data"]}')
        #         print('----------------------------------------------------------')
        # query.message.reply_text(text=user_generated_bot.print_conversation())
        user_generated_bot.dispatcher.add_handler(user_generated_bot.conv_handler)
        print(user_generated_bot.states)
        user_generated_bot.updater.start_polling()
        # user_generated_bot.updater.idle()

        # new_bot = threading.Thread(target=self.start_user_bot, args=(user_generated_bot,))
        # new_bot.start()

        return START_AGAIN  # Todo: change

    def start_user_bot(self, user_generated_bot):
        user_generated_bot.dispatcher.add_handler(user_generated_bot.conv_handler)
        user_generated_bot.updater.start_polling()
        user_generated_bot.updater.idle()

    def is_valid_API_key(self, api_key, user_id):
        check_url = f'https://api.telegram.org/bot{api_key}/getMe'
        response = requests.get(check_url)
        if response.status_code == 200:
            self.generated_bots[user_id].bot_username = response.json()['result']['username']
            return True
        else:
            return False

    def start_over(self, update: Update, context: CallbackContext):
        query = update.callback_query
        query.answer()
        self.start(query, context)

    # def make_back_to_menu_button(self, user_generated_bot):
    #     button_key = user_generated_bot.button_key
    #     state_callback = CallbackQueryHandler(user_generated_bot.entry_points[0].callback,
    #                                           pattern='^' + str(button_key) + '$')
    #     button = [InlineKeyboardButton(text='Main Menu', callback_data=str(button_key))]
    #     user_generated_bot.button_key += 1
    #     bot_states = user_generated_bot.states
    #     for state in bot_states.values():
    #         for callbackquery in state:
    #             callbackquery.callback.replay_buttons.append(button)
    #     for state in bot_states.values():
    #         state.append(state_callback)

    def add_follow_up(self, update: Update, context: CallbackContext):
        query = update.callback_query
        query.answer()
        user_generated_bot = self.generated_bots[update.effective_user.id]
        last_key = user_generated_bot.state_keys
        user_generated_bot.state_keys += 1
        user_generated_bot.states[last_key][-1].callback.next_state = user_generated_bot.state_keys
        query.message.reply_text(
            'Please enter a command that the bot will respond to (will be shown as a button)\n (this is a nested command)')
        self.follow_up = True
        return ADD_COMMAND


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
                CallbackQueryHandler(mainbot.ask_command, pattern='^' + str(ASK_COMMAND) + '$'),
                CallbackQueryHandler(mainbot.add_follow_up, pattern='^' + str(ADD_FOLLOW_UP) + '$'),
                CallbackQueryHandler(mainbot.end_build_bot, pattern='^' + str(END) + '$')
            ],
            ADD_COMMAND: [MessageHandler(Filters.text, mainbot.add_command)],
            ADD_RESPONSE: [MessageHandler(Filters.text, mainbot.add_response)],
            START_AGAIN: [CallbackQueryHandler(mainbot.start_over, pattern='^' + str(START_AGAIN) + '$')],
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
