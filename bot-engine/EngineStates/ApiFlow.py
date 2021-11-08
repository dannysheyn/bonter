import json

from telegram import Update
from telegram.ext import CallbackContext

from CurrentUser import CurrentUser
from botEngine import BotEngine
from callableBox import *
import userMessages
from EngineStates import *
from api import API
from userGeneratedBot import BOX_TYPE_INTERNAL_VARIABLE


class ApiFlow:
    @staticmethod
    def start_api_flow(update: Update, context: CallbackContext):
        query = update.callback_query
        query.answer()
        text = "We will now ask you some basic questions regarding " \
               "your API endpoint\n\n" \
               "What is the base endpoint of the API you want to integrate"
        query.message.reply_text(text=text)
        return GET_BASE_API

    @staticmethod
    def get_base_api(update: Update, context: CallbackContext):
        # put all default parameters in base uri
        base_url = update.message.text
        CurrentUser.get_current_user(update).apis.append(API(uri=base_url))
        text = "If there are any headers to the request please enter them in the following matter:\n" \
               "for example: api_key=<apikey>, host=<host>.\n" \
               "Please separate the key and the value with '=' sign.\n" \
               "Different headers separate with ',' " \
               "If there are no headers enter None"
        update.message.reply_text(text=text)
        return GET_AUTHORIZATION

    @staticmethod
    def get_authorization_header(update: Update, context: CallbackContext):
        authorization = update.message.text
        if authorization.find('=') == -1:
            text = 'No headers where given continuing to next stage...\n'
        else:
            auth_headers = [key_value.strip() for key_value in authorization.split(',')]
            for auth_header in auth_headers:
                header, value = auth_header.split("=", 1)
                CurrentUser.get_current_user(update).apis[-1].headers[header] = value.strip()
            text = 'Auth header were parsed successfully.\n'
        update.message.reply_text(text=text + 'Making a request to the provided endpoint...')
        return ApiFlow.parse_request(update, context)

    @staticmethod
    def parse_request(update: Update, context: CallbackContext):
        # This should be query params the user should enter
        # First validate that it matches the desired pattern
        # key:value, key:value ...
        request = CurrentUser.get_current_user(update).apis[-1].get_api_response()
        # Validate it's a Json response, currently we will support only Json
        if request.status_code == 200:
            pretty_response = json.loads(request.text)
            CurrentUser.get_current_user(update).apis[-1].response = pretty_response
            pretty_response = json.dumps(pretty_response, indent=2)
            text = "We just made a request with the parameters that you provided " \
                   "and got the following response\n\n"
            update.message.reply_text(text=text)
            BotEngine.send_long_message(update=update, pretty_response=pretty_response)
            text_get_key = userMessages.TEXT_GET_KEY
            # In general expression maps to the value of the key
            update.message.reply_text(text=text_get_key)
            return GET_KEY_FROM_RESPONSE
        else:
            api_obj = CurrentUser.get_current_user(update).apis[-1]
            if not re.findall(r'\$\{.+?\}', api_obj.uri):
                CurrentUser.get_current_user(update).user_variables['query_params_uri'] = True
                text = "Your api endpoint seems to be invalid, we will redirect you to the main menu so you could start" \
                       "the process from the beginning."
                del CurrentUser.get_current_user(update).apis[-1]
                update.message.reply_text(text=text)
                return BotEngine.edit_bot(update, context)
            else:
                text = "You have used user variables inside the url, we cannot query this api, please query the api and " \
                       "insert the parameters in the following format:\n"
                query_variables = re.findall(r'\$\{.+?}', api_obj.uri)
                api_obj.uri_to_check = BotEngine.sub_variables_with_defualt_values(query_variables, api_obj.uri)
                text_get_key = f'{text}{userMessages.TEXT_GET_KEY}'
                update.message.reply_text(text=text_get_key)
                return GET_KEY_FROM_RESPONSE

    @staticmethod
    def get_keys_to_retrieve(update: Update, context: CallbackContext):
        expressions = [expression.strip() for expression in update.message.text.split(',')]

        CurrentUser.get_current_user(update).apis[-1].expressions = expressions

        try:
            CurrentUser.get_current_user(update).apis[-1].validate_keys(save_response=False, use_uri_to_check=True)
        except Exception as e:
            error_message = "We couldn't validate one of your expressions\n" \
                            f"Original error is: \n {e}\n" \
                            f"Please try to write those expressions again according to the rules"
            update.message.reply_text(text=error_message)
            return GET_KEY_FROM_RESPONSE

        key_expression_mapping = CurrentUser.get_current_user(update).apis[-1].key_expression_map()
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

    # curr=[userid][currntbot = number ], curr_bot = [uid][curr]
    @staticmethod
    def get_message_to_user(update: Update, context: CallbackContext):
        CurrentUser.get_current_user(update).apis[-1].message_to_user = update.message.text
        text = f'The API Endpoint was created successfully\n ' \
               f'The box you created has the number of: '
        box_number = CurrentUser.get_current_user(update).add_box(box_msg='api call', box_type='api',
                                                   api_obj=CurrentUser.get_current_user(update).apis[-1])
        text += str(box_number)
        # if not valid message recursively come back to this function
        # else we finish the process and create new callbackquery handler
        update.message.reply_text(text=text)
        return BotEngine.edit_bot(update, context)
