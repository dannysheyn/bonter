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
import threading
import os


# TODO NEXT TIME: add queryHandler to our bot can be hardcoded. checks and optimizations,
#  and looking into how to upgrade the fetures in the bot engine ( at least add command to a command) i.e nested commands.
# TODO: maybe api action?

class CallablePrint:
    def __init__(self, msg, next_state):
        self.msg = msg
        self.next_state = next_state
        self.replay_buttons = []

    def add_button(self, button):
        self.replay_buttons.append(button)

    def __call__(self, update: Update, context: CallbackContext):
        update.message.reply_text(text=self.msg)
        if self.replay_buttons:
            print(self.replay_buttons)
            keyboard = InlineKeyboardMarkup(self.replay_buttons)
            update.message.reply_text(text="What would you like to do next", reply_markup=keyboard)
        return self.next_state


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


class BotEngine:
    def __init__(self, bot_name=None, bot_api_key=None, conv_handler=None):
        self.bot_name = bot_name
        self.bot_api_key = bot_api_key
        self.conv_handler = conv_handler
        self.updater = Updater(bot_api_key, use_context=True)
        self.generated_bots = {}  # {'artem' : UserGeneratedBot() , 'daniel': UserGeneratedBot() }
        self.invalid_param = None


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
            CommandHandler('start', CallablePrint(first_words, return_key))]
        # self.generated_bots[update.effective_user.id].state_keys += 1
        update.message.reply_text('Please enter a command that the bot will respond to (will be shown as a button)')
        return ADD_COMMAND

    def ask_command(self, update: Update, context: CallbackContext):
        query = update.callback_query
        query.answer()
        query.edit_message_text('Currently the bot knows this commands')
        counter = 0
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
        keyboard_callback = CallbackQueryHandler(CallablePrint(response, last_key), pattern='^' + str(user_generated_bot.button_key) + '$')
        if last_key not in user_generated_bot.states:
            user_generated_bot.states[last_key] = []
        user_generated_bot.states[last_key].append(keyboard_callback)
        self.generated_bots[update.effective_user.id].entry_points[0].callback.add_button(
            InlineKeyboardButton(text=last_command, callback_data=str(user_generated_bot.button_key))
        )
        user_generated_bot.button_key += 1
        menu_text = 'what do you want to do next?\n' \
                    'please choose one of the following:'
        menu_buttons = [[InlineKeyboardButton(text='Add new command', callback_data=str(ASK_COMMAND))],
                        [InlineKeyboardButton(text='End building bot', callback_data=str(END))]]
        menu_keyboard = InlineKeyboardMarkup(menu_buttons)
        update.message.reply_text(text=menu_text, reply_markup=menu_keyboard)
        return SELECTION

    def main_menu(self, update: Update, context: CallbackContext):
        query = update.callback_query
        query.annswer()

        #update.callback_query.answer()
        #update.callback_query.edit_message_text(text=menu_text, reply_markup=menu_keyboard)
        return MENU

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
        user_generated_bot.updater.start_polling()
        #user_generated_bot.updater.idle()

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

    def start_over(self, update:Update, context: CallbackContext):
        query = update.callback_query
        query.answer()
        self.start(query, context)


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

def main():
    mainbot = BotEngine(bot_name='engineBot', bot_api_key="1743828272:AAF_0DG0-bjmp5nb6TvjcaYXU08EHvTchQQ",
                        conv_handler=None)
    dispatcher = mainbot.updater.dispatcher
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', mainbot.start)],
        states={
            GET_API_KEY: [MessageHandler(Filters.text, mainbot.get_api_key)],
            ADD_START: [MessageHandler(Filters.text, mainbot.define_bot_start)],
            SELECTION: [
                CallbackQueryHandler(mainbot.ask_command, pattern='^' + str(ASK_COMMAND) + '$'),
                CallbackQueryHandler(mainbot.end_build_bot, pattern='^' + str(END) + '$')
                # ASK_COMMAND: [MessageHandler(Filters.text, mainbot.ask_command)],
                # END: [MessageHandler(Filters.text, mainbot.end_build_bot)]
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

# q: what would you like to know?
# a (if answer containd : phone): iphone, lg ...
# a (if answer containd : TV): samsung , lg, ..


''':key
make new bot:
{
new_bot = conversationHandler(entry_points=[],
 states={}
 fallbacks= []
)
new_bot.start()
}



create:
entry_points=[CommandHandler('start', mainbot.start)], # GET API KEY
states={
            BOT_NAME: [MessageHandler(Filters.text, mainbot.get_bot_name)],
            ADD_QUESTION: [MessageHandler(Filters.text, ADD_QUESTION)],
            # add_question: [MessageHandler(Filters.text, bio)],
        },

1) how to save each bot that we can remember
2)


please enter a command:
products
please enter a the response:
iphone3, samsungA5 ...
do you want to enter another command?
yes , no
if yes:
please enter a command:
if no:
init bot and send the costumer the link
'''

''':key
/start
hi im here to help you:
 ________
|_products__|__hours__|
|___|____|

'''

## added response, but without buttons,
# TODO: add buttons, add menu buttons, command nesting (calling a command within a command) lookinto microsoft bot builder
# [MessageHandler('start', CallablePrint(first_words,self.generated_bots[update.meffective_user.id].state_keys))]
# buttons = [
# [
#     InlineKeyboardButton(text=command, callback_data=),
#     InlineKeyboardButton(text=, callback_data=),
# ]

#
# please enter a command:
# products
# please enter a the response:
# iphone3, samsungA5 ...
# do you want to enter another command?
# yes , no
# if yes:
# please enter a command:
# if no:
# init bot and send the costumer the link

# def add_question(self, update: Update, context: CallbackContext):
#     key_words = []
#     update.message.reply_text('Please enter the options your bot give to the user')
#     question = update.message.from_user
#     max_len = 3
#     keyword = ''
#     response = ''
#     # save question and add to his bot
#     update.message.reply_text(f'Please enter the response to the question according to "{question}": keyword')
#     while keyword != 'q' or len(key_words) != max_len:
#         update.message.reply_text('The Key word:')  # products  product
#         keyword = update.message.from_user
#         update.message.reply_text('The response:')
#         response = update.message.from_user
#         key_words.append((keyword, response))
#     if len(key_words) == max_len:
#         print(f'max key words is {max_len}')
#     return ADD_QUESTION
