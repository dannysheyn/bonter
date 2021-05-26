from telegram import Update
from telegram.ext import CallbackContext
import re


def set_user_variable(self, update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    text = 'Here you can set up a user variable, a user variable is an input from the user who will be going to use ' \
           'the bot, that you can reference during you bot building.\n' \
           'You can reference your variable anywhere using the variable like this: {$var_name} '
    query.message.reply_text(text=text)
    return None


sent = 'hi this {$my_var3} is my try, hello {$my_var1} {$my_var2}'
pattern = re.compile(r'[{$a-zA-Z0-9]+}')
matches = pattern.finditer(sent)

for match in matches:
    print(match)
