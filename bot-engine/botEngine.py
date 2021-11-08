import zipfile
from typing import Optional

import pymongo
from telegram.ext import (
    Updater,
    ConversationHandler,
    Handler, )

import userMessages
from RecoverBot import RecoverBot
from .EngineStates.TimedAcationFlow import TimedActionFlow
from .EngineStates.UserVariablesFlow import UserVariableFlow
from .EngineStates.ApiFlow import ApiFlow
from callableBox import *
from callback import *
from helpers import *
from userGeneratedBot import *
from .EngineStates.InternalVariableFlow import *
from CurrentUser import CurrentUser
mongo=os.getenv('mongo')

class BotEngine:
    mongo_client = pymongo.MongoClient(
mongo)

    #    current_user_bot = {}

    def __init__(self, bot_name=None, api_key=None, conv_handler=None, mongo_client=None):
        self.bot_name = bot_name
        self.api_key = api_key
        self.conv_handler = conv_handler
        self.updater = Updater(api_key, use_context=True)
        # self.generated_bots = {}  # {'artem' : UserGeneratedBot() , 'daniel': UserGeneratedBot() }
        self.current_user_bot = None
        self.invalid_param = None
        self.follow_up = False
        self.is_editing = False

    def start(self, update: Update, context: CallbackContext) -> int:
        query = update.callback_query
        query.answer()
        self.current_user_bot = CurrentUser.get_current_user(update)  # userGeneratedBot.UserGeneratedBot()
        query.message.reply_text('Please enter the api key')
        return GET_API_KEY

    def get_api_key(self, update: Update, context: CallbackContext):
        api_key = update.message.text
        self.current_user_bot.api_key = api_key
        if get_bot(self.mongo_client, self.current_user_bot.api_key, update.effective_user.id) != -1 \
                and not self.is_editing:
            text = f"You already have a bot with this api key in your account\n" \
                   f"If you want to edit your bot, you can choose 'Edit Bot' in the menu"
            update.message.reply_text(text=text)
            return self.main_menu(update, context)

        bot_username = self.get_bot_username(api_key)
        if bot_username != "":
            self.current_user_bot.bot_username = bot_username
            # update.message.reply_text('Please enter you bots first words to the end user')
            update.message.reply_text(userMessages.BOT_START)
            return self.edit_bot(update, context)
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
                [InlineKeyboardButton("View chats", callback_data=str(CHOOSE_BOT_CHATS))],
                [InlineKeyboardButton("Help", callback_data=str(HELP))],
            ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.message.reply_text(text=text, reply_markup=reply_markup)
        return MAIN_MENU

    def ask_api_key(self, update, context):
        query = Callback.check_query(update, context)
        text = 'Please enter the API key of the bot that you want to edit'
        query.message.reply_text(text=text)

    def choose_bot_to_edit(self, update: Update, context: CallbackContext):
        # Search bot in user bots using bot api key
        # set curr_bot to the found bot
        self.ask_api_key(update, context)
        return GET_BOT

    def get_bot(self, update: Update, context: CallbackContext):
        api_key = update.message.text
        bot_username = self.get_bot_username(api_key)
        if bot_username != "":
            raw_bot = get_bot(self.mongo_client, api_key, update.effective_user.id)
            if raw_bot != -1:
                bot = RecoverBot.build_bot(raw_bot)
                CurrentUser.set_current_user(update, bot)
                self.current_user_bot = CurrentUser.get_current_user(update)
                self.current_user_bot.bot_username = bot_username
            else:
                update.message.reply_text("We couldn't find a bot with this API key in your account\n"
                                          "Please try again")
                return self.main_menu(update, context)
        else:
            update.message.reply_text('You have entered a wrong api key, please enter a valid one.')
            return GET_BOT
        self.is_editing = True
        return self.edit_bot(update, context)

    def choose_bot_to_view_chats(self, update: Update, context: CallbackContext):
        query = Callback.check_query(update, context)
        text = 'Please enter the API key of the bot that you want to see his chats'
        query.message.reply_text(text=text)
        return VIEW_CHATS

    def view_chats(self, update: Update, context: CallbackContext):
        api_key = update.message.text
        chats, bot_name = get_chats(self.mongo_client, api_key)
        if bot_name is None:
            text = "No chats were found with this API Key.\n" \
                   "Please try another API key."
            update.message.reply_text(text=text)
        else:
            text = f"Here are all the chats with the bot {bot_name}\n\n"
            zip_file_name = f'ChatLogs_{update.effective_user.id}.zip'
            update.message.reply_text(text=text)
            with zipfile.ZipFile(zip_file_name, 'w') as myzip:
                for chat_id, chats in chats.items():
                    file_name = f"{chat_id}.txt"
                    with open(file_name, "w+") as log:
                        for message in chats:
                            log.write(f"{message['date']}\t\t{message['from']}\t\t{message['text']}\n")
                        log.seek(0)
                    myzip.write(file_name)
            context.bot.send_document(update.message.chat.id, document=open(zip_file_name, 'rb'))
            text = f"This are all the messages from the {bot_name} bot, which each text file is a different user\n"
            update.message.reply_text(text=text)
        return self.main_menu(update, context)

    @staticmethod
    def edit_bot(update, context: CallbackContext):
        text = 'Please choose one of the following actions'
        keyboard = \
            [
                [InlineKeyboardButton("Add box", callback_data=str(CHOOSE_BOX))],
                [InlineKeyboardButton("Add edge", callback_data=str(ADD_EDGE))],
                [InlineKeyboardButton("Add box button", callback_data=str(ADD_BOX_BUTTON))],
                [InlineKeyboardButton("Add timed action", callback_data=str(TIMER_ACTION))],
                [InlineKeyboardButton("Print bot", callback_data=str(PRINT_BOT))],
                [InlineKeyboardButton("End building bot", callback_data=str(END))],
                [InlineKeyboardButton("Delete Node", callback_data=str(CHOOSE_NODE_TO_DELETE))],
                [InlineKeyboardButton("Help", callback_data=str(HELP))]
            ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(text=text, reply_markup=reply_markup)
        return EDIT_BOT

    def choose_node_to_delete(self, update, context):
        query = Callback.check_query(update, context)
        query.message.reply_text("Please type in the box number which you want to delete")
        file_path = self.current_user_bot.show_bot(str(update.effective_user.id))
        try:
            query.message.reply_photo(photo=open(file_path, 'rb'), caption='Here is your bot!')
        except Exception as e:
            query.message.reply_text("Can't print bot photo as it is too big")
        return DELETE_NODE

    def delete_node(self, update, context):
        box_number = update.message.text
        if box_number.isnumeric():
            box_number = int(box_number)
            if not self.current_user_bot.delete_state(box_number):
                update.message.reply_text("Error!\nYou have entered a wrong box number, please try again")
            else:
                update.message.reply_text("The node was deleted successfully")
        else:
            update.message.reply_text("Error!\nThe box number should be an integer")

        return self.edit_bot(update, context)

    def define_bot_start(self, update, context):
        query = Callback.check_query(update, context)
        query.message.reply_text("Before initialing your bot, we will need you to choose the entry point for your bot"
                                 " please provide a box number that you want the bot to start at")

        file_path = self.current_user_bot.show_bot(str(update.effective_user.id))
        try:
            query.message.reply_photo(photo=open(file_path, 'rb'), caption='Here is your bot!')
        except Exception as e:
            query.message.reply_text("Can't print bot photo as it is too big")

        return INIT_BOT

    def init_user_bot(self, update: Update, context: CallbackContext):
        """
        save necessrray info of userGenerated bot to db in order to recreate it
        """
        start_box_number = update.message.text

        self.current_user_bot.add_starting_point(start_box_number)
        self.current_user_bot.updater = Updater(self.current_user_bot.api_key, use_context=True)
        self.current_user_bot.dispatcher = self.current_user_bot.updater.dispatcher
        self.current_user_bot.conv_handler = ConversationHandler(
            entry_points=[self.current_user_bot.entry_point],
            states=self.current_user_bot.states,
            fallbacks=[CommandHandler('cancel', self.current_user_bot.entry_point)],
        )

        self.current_user_bot.dispatcher.add_handler(self.current_user_bot.conv_handler)
        if self.is_editing:
            update_bot(self.mongo_client, update, self.current_user_bot)
        else:
            add_bot(self.mongo_client, update, self.current_user_bot)
        text = f"Your bot is now initialized! click the link to interact with your bot!\n" \
               f"http://telegram.me/{self.current_user_bot.bot_username}?start=start"

        if not self.current_user_bot.updater.running:
            self.current_user_bot.updater.start_polling()

        update.message.reply_text(text=text)
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
        try:
            from_edge, to_edge = re.split('->', response)

            from_edge = from_edge.split('.')
            from_edge = [int(i) for i in from_edge]
            to_edge = int(to_edge)
            self.current_user_bot.add_edge(from_edge, to_edge)
            text = 'Edge added successfully!'
        except ValueError:
            text = 'too much parameters were given, please try again'
        except Exception as e:
            print(e)
            text = 'Wrong parameters were given, please try again'
        update.message.reply_text(text=text)
        return self.edit_bot(update, context)

    def choose_box(self, update: Update, context: CallbackContext):
        query = update.callback_query
        query.answer()
        text = 'Please Choose one of the following box purpose \n' \
               'Text box: Choose the text you want show to the user.\n' \
               'Api box: Choose an API you want show to the user.\n' \
               'Internal variable assignment: Have a variable assign by and api or a constant value.\n'

        keyboard = \
            [
                [InlineKeyboardButton("Add text box", callback_data=str(ADD_TEXT_BOX))],
                [InlineKeyboardButton("Add API fetch box", callback_data=str(ADD_API_BOX))],
                [InlineKeyboardButton("Add User given variable", callback_data=str(ADD_USER_VARIABLE))],
                [InlineKeyboardButton("Add Internal variable assignment box",
                                      callback_data=str(INTERNAL_VARIABLE_ASSIGNMENT_START_FLOW))],
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
        try:
            box_number = self.current_user_bot.add_box(box_msg, 'text')
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

            box_is_valid = self.current_user_bot.is_valid_box(box_number)
            if box_is_valid:
                text = 'Please enter the text that will be shown on the button'
                self.current_user_bot.build_button['box'] = box_number
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
        box_number = self.current_user_bot.build_button['box']
        button_text = update.message.text
        button_number_created = self.current_user_bot.add_box_button(box_number, button_text)
        text = f'Button #{button_number_created} Added successfully to box #{box_number}'
        update.message.reply_text(text=text)
        return self.edit_bot(update, context)

    def print_bot(self, update: Update, context: CallbackContext):
        query = update.callback_query
        query.answer()
        file_path = self.current_user_bot.show_bot(str(update.effective_user.id))
        query.message.reply_photo(photo=open(file_path, 'rb'), caption='Here is your bot!')
        return self.edit_bot(query, context)

    @staticmethod
    def send_long_message(update, pretty_response):
        if len(pretty_response) > 4096:
            for x in range(0, len(pretty_response), 4096):
                update.message.reply_text(text=pretty_response[x:x + 4096])
        else:
            update.message.reply_text(text=pretty_response)

    @staticmethod
    def sub_variables_with_defualt_values(query_variables, url) -> str:
        defual_params = list(map(lambda match: match.split(':')[1][:-1], query_variables))
        new_uri = url
        for param in defual_params:
            new_uri = re.sub('\$\{.+?}', param, url)
        return new_uri

    @staticmethod
    def header_extractor(headers: str, api_to_insert):
        auth_headers = [key_value.strip() for key_value in headers.split(',')]
        for auth_header in auth_headers:
            header, value = auth_header.split("=", 1)
            api_to_insert.headers[header] = value.strip()


    @staticmethod
    def uri_has_variables(uri):
        match = r'\$\{([A-Za-z0-9_]+)\}'
        if re.match(match, uri):
            return True
        else:
            return False




# Daniel : 1489264800:AAEgoIvqwoN3K1UZL6ghTY5ixZvUcl6qI_E
# Artem : 1743828272:AAF_0DG0-bjmp5nb6TvjcaYXU08EHvTchQQ

# public apis: https://github.com/public-apis/public-apis
# https://api.coincap.io/v2/assets  bitcoin api

# stam bot : 1729539488:AAFxZf8IItBf8dcrNUIW2albguVpHUvm5TU
# danie pymongo: ("mongodb+srv://Shaanan:F4a6aAcqzpCVM4Dy@cluster0.xfxqr.mongodb.net/Bonter?retryWrites=true&w=majority")
# artem pymongo: "mongodb+srv://ArtemK:Art7302it%21@cluster0.xfxqr.mongodb.net/Bonter?retryWrites=true&w=majority"
'''





'''
