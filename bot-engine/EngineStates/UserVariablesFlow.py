import json

from telegram import Update
from telegram.ext import CallbackContext

import userGeneratedBot
from CurrentUser import CurrentUser
from botEngine import BotEngine
from callableBox import *
import userMessages
from EngineStates import *
from api import API
from userGeneratedBot import BOX_TYPE_INTERNAL_VARIABLE


class UserVariableFlow:
    @staticmethod
    def add_user_variable_box(update: Update, context: CallbackContext):
        query = update.callback_query
        query.answer()
        text = 'Variables are values you get from the user from free text, you can reference them the following way:\n' \
               'Let''s say i obtained the name of the user and defined it to the variable name of ''user_name''.' \
               'You can now reference that variable the following way: (any where you input text to the bot)' \
               '''Hi ${user_name} nice to meet you!''' \
               'The end user will see the following string: ''Hi John nice to meet you!'''
        query.message.reply_text(text=text)

        query.message.reply_text(text='Please enter the question you will ask the user.'
                                      'Examples: ' \
                                      'Please enter your name:' \
                                      'How old are you?' \
                                      'What is your oder id?')
        return USER_VARIABLE2

    @staticmethod
    def add_user_variable_box2(update: Update, context: CallbackContext):
        client_variable = update.message.text

        CurrentUser.get_current_user(update).user_variables['question'] = client_variable
        #
        update.message.reply_text(text='Please enter the variable name that will store the user''s answer'
                                       'Example: The variable ''user_name'', ''user_age''')
        return USER_VARIABLE3

    @staticmethod
    def add_user_variable_box3(update: Update, context: CallbackContext):
        variable_name = update.message.text

        question = CurrentUser.get_current_user(update).user_variables['question']
        if variable_name in CurrentUser.get_current_user(update).client_variables:
            update.message.reply_text(text=f'The variable "{variable_name}" is already in use, try a different name')
            return USER_VARIABLE
        else:
            CurrentUser.get_current_user(update).client_variables.add(variable_name)
            # create the box flow of the question -> answer
            question_box_number = CurrentUser.get_current_user(update).add_box(box_msg=question,
                                                                               box_type=userGeneratedBot.BOX_TYPE_QUESTION)
            box_button_num = CurrentUser.get_current_user(update).add_box_button(question_box_number,
                                                                                 'Get user variable value')
            user_answer_box_number = CurrentUser.get_current_user(update).add_message_handler_state(
                obj={'variable_name': variable_name},
                add_as_box=True)
            CurrentUser.get_current_user(update).add_edge((question_box_number, box_button_num), user_answer_box_number)

        update.message.reply_text(text=f'Two boxes have been created:'
                                       f'first: box number {question_box_number} that asks: {question}\n'
                                       f'second: box number {user_answer_box_number} that gets the answer from the '
                                       f'user and inserts it into {variable_name}\n '
                                       f'that can be referenced by typing ${{{variable_name}}} anywhere in the bot\n'
                                       f'NOTE: You can only use this variable after the user submitted his response.')

        return BotEngine.edit_bot(update, context)
