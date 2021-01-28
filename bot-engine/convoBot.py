
"""
First, a few callback functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.
Usage:
Example of a bot-user conversation using ConversationHandler.
Send /start to initiate the conversation.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""
#TODO: how fork the conversation, bot is made after conversation or on the go?, make the bot with all the user defined options, how to run the bot -- (run with new features?)
#TODO: api integration tool?
#TODO: wrapper class of all api's for all bots according to contex
import logging

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)


class BotObject:
    def __init__(self, bot_name=None, bot_api_key=None):
        self.bot_name = bot_name
        self.bot_api_key = bot_api_key



logger = logging.getLogger(__name__)

GET_API_KEY, ADD_NEW_REQUEST, PHOTO, LOCATION, BIO = range(4)


def start(update: Update, context: CallbackContext) -> int:
    update.message.reply_text('Please enter the api key')
    return GET_API_KEY

def get_api_key(update: Update, context: CallbackContext) -> int:
    api_key = update.message.text
    #TODO: save the api in a database? activate the bot?
    update.message.reply_text('Please enter the first suggested clickable keywords')
    return ADD_NEW_REQUEST

def new_user_defined_event_handler(update: Update, context: CallbackContext): #bot main menu
    reply_keyboard = [['Add new event handler', 'Add Poll', 'Add new API request/event', 'Help']]
    update.message.reply_text(
    'Choose the desired action',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
    )
    return


def gender(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    logger.info("Gender of %s: %s", user.first_name, update.message.text)
    update.message.reply_text(
        'I see! Please send me a photo of yourself, '
        'so I know what you look like, or send /skip if you don\'t want to.',
        reply_markup=ReplyKeyboardRemove(),
    )

    return PHOTO


def photo(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    photo_file = update.message.photo[-1].get_file()
    photo_file.download('user_photo.jpg')
    logger.info("Photo of %s: %s", user.first_name, 'user_photo.jpg')
    update.message.reply_text(
        'Gorgeous! Now, send me your location please, ' 'or send /skip if you don\'t want to.'
    )

    return LOCATION


def skip_photo(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    logger.info("User %s did not send a photo.", user.first_name)
    update.message.reply_text(
        'I bet you look great! Now, send me your location please, ' 'or send /skip.'
    )

    return LOCATION


def location(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    user_location = update.message.location
    logger.info(
        "Location of %s: %f / %f", user.first_name, user_location.latitude, user_location.longitude
    )
    update.message.reply_text(
        'Maybe I can visit you sometime! ' 'At last, tell me something about yourself.'
    )

    return BIO


def skip_location(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    logger.info("User %s did not send a location.", user.first_name)
    update.message.reply_text(
        'You seem a bit paranoid! ' 'At last, tell me something about yourself.'
    )

    return BIO


def bio(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    logger.info("Bio of %s: %s", user.first_name, update.message.text)
    update.message.reply_text('Thank you! I hope we can talk again some day.')

    return ConversationHandler.END


def cancel(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text(
        'Bye! I hope we can talk again some day.', reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


def main() -> None:
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater("1489264800:AAEgoIvqwoN3K1UZL6ghTY5ixZvUcl6qI_E", use_context=True)
    user_bot = BotObject()

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Add conversation handler with the states GENDER, PHOTO, LOCATION and BIO
    # TODO: check if api key is valid? best way?
    # TODO: Kinds of replays video, sticker etc
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            get_api_key: [MessageHandler(Filters.regex('^(Boy|Girl|Other)$'), gender)],
            PHOTO: [MessageHandler(Filters.photo, photo), CommandHandler('skip', skip_photo)],
            LOCATION: [
                MessageHandler(Filters.location, location),
                CommandHandler('skip', skip_location),
            ],
            BIO: [MessageHandler(Filters.text & ~Filters.command, bio)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    dispatcher.add_handler(conv_handler)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()


''':key
    
    '^(Boy|Girl|Other)$'
    def start(update: Update, context: CallbackContext) -> int:
    reply_keyboard = [['Product', 'Opening Times', 'Other']]

    update.message.reply_text(
    'Please enter the first suggested clickable keywords',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
    )
    return GENDER
'''