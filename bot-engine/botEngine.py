from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update, InlineKeyboardButton
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
    Handler,
)


class CallablePrint:
    def __init__(self, msg, next_state):
        self.msg = msg
        self.next_state = next_state

    def __call__(self, update: Update, context: CallbackContext):
        update.message.reply_text(self.msg)
        return self.next_state


class UserGeneratedBot:
    def __init__(self, bot_name=None, bot_api_key=None, conv_handler=None):
        self.bot_name = bot_name
        self.bot_api_key = bot_api_key
        self.conv_handler = conv_handler
        self.updater = None  # Updater(bot_api_key, use_context=True)
        self.entry_points = []  # build on the go /start /hi
        self.states = {}  # build on the go
        self.fallbacks = []  # build on the go
        self.state_keys = 0
        self.last_command = None


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

    def is_valid_API_key(self, api_key):
        if api_key == 'hi':
            return False
        return True

    def get_api_key(self, update: Update, context: CallbackContext):
        api_key = update.message.text
        self.generated_bots[update.effective_user.id].bot_api_key = api_key
        if self.is_valid_API_key(api_key):
            update.message.reply_text('Please enter the bot name')
            return BOT_NAME
        else:
            pass
            update.message.reply_text('You have entered a wrong api key, please enter a valid one.')
            return GET_API_KEY

    def invalid_state_manegment(self, update: Update, context: CallbackContext):
        if self.invalid_param == 'API':
            update.message.reply_text('You have entered a wrong api key, please enter a valid one.')
            return GET_API_KEY

    def get_bot_name(self, update: Update, context: CallbackContext):
        self.generated_bots[update.effective_user.id].bot_name = update.message.text
        update.message.reply_text('Please enter the first word your bot will say to the user')
        return ADD_START

    #    update.message.reply_text('Please enter a command that the bot will respond to')

    def define_bot_start(self, update: Update, context: CallbackContext):
        first_words = update.message.text
        self.generated_bots[update.effective_user.id].entry_point = [CommandHandler('start', CallablePrint(first_words,
                                                                                                           self.generated_bots[
                                                                                                               update.effective_user.id].state_keys))]
        self.generated_bots[update.effective_user.id].state_keys += 1
        update.message.reply_text('Please enter a command that the bot will respond to (will be shown as a button)')
        return ADD_COMMAND


    def add_command(self, update: Update, context: CallbackContext):
        command = update.message.text
        self.generated_bots[update.effective_user.id].last_command = command
        update.message.reply_text('What will the bot will answer to this command?')
        return ADD_RESPONSE


    def add_response(self, update: Update, context: CallbackContext):
        response = update.message.text
        last_command = self.generated_bots[update.effective_user.id].last_command
        last_key = self.generated_bots[update.effective_user.id].state_keys
        self.generated_bots[update.effective_user.id].states[last_key] = [
            MessageHandler(Filters.text, CallablePrint(response, last_key))
        ]
        ## added response, but without buttons,
        # TODO: add buttons, add menu buttons, command nesting (calling a command within a command) lookinto microsoft bot builder
        #

        #[MessageHandler('start', CallablePrint(first_words,self.generated_bots[update.meffective_user.id].state_keys))]
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

    def add_question(self, update: Update, context: CallbackContext):
        key_words = []
        update.message.reply_text('Please enter the options your bot give to the user')
        question = update.message.from_user
        max_len = 3
        keyword = ''
        response = ''
        # save question and add to his bot
        update.message.reply_text(f'Please enter the response to the question according to "{question}": keyword')
        while keyword != 'q' or len(key_words) != max_len:
            update.message.reply_text('The Key word:')  # products  product
            keyword = update.message.from_user
            update.message.reply_text('The response:')
            response = update.message.from_user
            key_words.append((keyword, response))
        if len(key_words) == max_len:
            print(f'max key words is {max_len}')
        return ADD_QUESTION


BOT_NAME = 0
ADD_START = 1
ADD_QUESTION = 2
GET_API_KEY = 3
INVALID_STATE = 4
ADD_COMMAND = 5
ADD_RESPONSE = 6

def main():
    mainbot = BotEngine(bot_name='engineBot', bot_api_key="1489264800:AAEgoIvqwoN3K1UZL6ghTY5ixZvUcl6qI_E",
                        conv_handler=None)
    dispatcher = mainbot.updater.dispatcher
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', mainbot.start)],
        states={
            GET_API_KEY: [MessageHandler(Filters.text, mainbot.get_api_key)],
            BOT_NAME: [MessageHandler(Filters.text, mainbot.get_bot_name)],
            ADD_START: [MessageHandler(Filters.text, mainbot.define_bot_start)],  # first thing that the bot says,
            # and how to start the bot "/start":
            ADD_QUESTION: [MessageHandler(Filters.text, ADD_QUESTION)]
            # INVALID_TOKEN: [MessageHandler(Filters.text, ADD_QUESTION)],
        },
        fallbacks=[CommandHandler('cancel', mainbot.start)],
    )
    dispatcher.add_handler(conv_handler)
    mainbot.updater.start_polling()
    mainbot.updater.idle()


# ~##~@@ kvar ba

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


