from botEngine import BotEngine
from callableBox import *
import userMessages
from EngineStates import *
from api import API
from userGeneratedBot import BOX_TYPE_INTERNAL_VARIABLE
from CurrentUser import CurrentUser

class InternalVariableFlow:
    @staticmethod
    def internal_variable_assignment_start_flow(update: Update, context: CallbackContext):
        '''
        goal: embedded a value into a variable
        '''
        query = update.callback_query
        query.answer()
        text = 'Please enter the name of the variable you want to embed with a value'
        query.message.reply_text(text=text)
        return GET_INTERNAL_VARIABLE

    @staticmethod
    def internal_variable_assignment_name(update: Update, context: CallbackContext):
        variable_name = update.message.text
        user_generated_bot = CurrentUser.get_current_user(update)
        if variable_name in user_generated_bot.internal_client_variables or variable_name in user_generated_bot.user_variables:
            update.message.reply_text(text='The variable name you gave is already in use, please try again.')
            return BotEngine.edit_bot(update, context)
        else:
            user_generated_bot.user_variables['internal_variable'] = variable_name
            update.message.reply_text(text='Please insert if you want to insert the value:\n'
                                           '1) Now\n'
                                           '2) API during run time.')

        return INTERNAL_VARIABLE_SOURCE

    @staticmethod
    def internal_variable_assignment_source(update: Update, context: CallbackContext):
        user_choice = update.message.text
        if user_choice == "1":
            update.message.reply_text(text='Please enter the value you want to insert to the variable')
            return INTERNAL_VARIABLE_INSTANT_VALUE
        elif user_choice == "2":
            update.message.reply_text(text='Please enter the api uri you want to use.\n'
                                           'Note: you can use the ${variable_name} in the uri given, BUT you will need to add'
                                           ' a default value in the following matter: ${variable_name:default_value} examples:\n'
                                           ' ${city:new york}, ${name:Alice}')
            return INTERNAL_VARIABLE_API_VALUE
        else:
            update.message.reply_text(text='Not 1 or 2 was given as an answer.\n Please try again')
            return BotEngine.edit_bot(update, context)

    @staticmethod
    def internal_variable_instant_value(update: Update, context: CallbackContext):
        query = update.callback_query
        query.answer()
        user_variable_value = update.message.text
        user_generated_bot = CurrentUser.get_current_user(update)
        internal_variable_name = user_generated_bot.user_variables['internal_variable']
        user_generated_bot.internal_client_variables[internal_variable_name] = user_variable_value
        update.message.reply_text(
            text=f'Value added to variable ${{{internal_variable_name}}} with the value: {internal_variable_name}.\n'
                 f'Now you can use the ${{{internal_variable_name}}} everywhere in your bot '
                 f'making.')
        return BotEngine.edit_bot(update, context)

    @staticmethod
    def internal_variable_api_value_start(update: Update, context: CallbackContext):
        url = update.message.text
        user_generated_bot = CurrentUser.get_current_user(update)
        user_generated_bot.apis.append(API(uri=url))
        update.message.reply_text(text=userMessages.HEADER_MESSAGE)
        return INTERNAL_VARIABLE_API_HEADERS

    @staticmethod
    def internal_variable_api_headers(update: Update, context: CallbackContext):
        authorization = update.message.text
        user_generated_bot = CurrentUser.get_current_user(update)
        api_obj = user_generated_bot.apis[-1]
        if authorization.find('=') == -1:
            text = 'No headers where given continuing to next stage...\n'
            update.message.reply_text(text=text)
        else:
            BotEngine.header_extractor(authorization, api_obj)
        text = 'Now we will show you the return value from the api call,' \
               ' and you will choose with value you want from the call'
        update.message.reply_text(text=text)
        query_variables = re.findall(r'\$\{.+?\}', api_obj.uri)
        if query_variables:  # if in the url there are variables in the form of ${var}
            api_obj.uri_to_check = BotEngine.sub_variables_with_defualt_values(query_variables, api_obj.uri)
        response = user_generated_bot.apis[-1].get_api_response()
        text = "We just made a request with the parameters that you provided " \
               "and got the following response\n\n"
        update.message.reply_text(text=text)
        if response.status_code == 200:
            pretty_response = json.loads(response.text)
            pretty_response = json.dumps(pretty_response, indent=2)
            user_generated_bot.apis[-1].response = pretty_response
            BotEngine.send_long_message(update=update, pretty_response=pretty_response)
            text_get_key = f'What key in the data would you like it to be inserted to the variable {user_generated_bot.user_variables["internal_variable"]}.' \
                           f'please enter the Json expressions which evaluate to your key for example:\n' \
                           f'[origin] or [destination][flight_num] and etc...\n ' \
                           'If the key are inside an array you need to index it, for example: [0][origin] or ' \
                           '[destination][1]\n ' \
                           'You can use nesting for dictionaries as well, for example: [data][name] or [0][data][' \
                           'time]\n '
            update.message.reply_text(text=text_get_key)
            return INTERNAL_VARIABLE_API_MAPPING
        else:
            text = 'Status code was not 200, please try to request the same values in postman and try again later'
            update.message.reply_text(text=text)
            return BotEngine.edit_bot(update, context)

    @staticmethod
    def internal_variable_api_mapping(update: Update, context: CallbackContext):
        expression = update.message.text  # I.E: [0][data][time]
        user_generated_bot = CurrentUser.get_current_user(update)
        user_generated_bot.apis[-1].expressions = [expression]
        internal_variable = user_generated_bot.user_variables["internal_variable"]
        try:
            user_generated_bot.apis[-1].validate_keys(save_response=False, use_uri_to_check=True)
            item = tuple(user_generated_bot.apis[-1].key_expression.items())
            key, value = item[0][0], item[0][1]
            user_generated_bot.apis[-1].key_expression[internal_variable] = value
            del user_generated_bot.apis[-1].key_expression[key]
        except Exception as e:
            error_message = "We couldn't validate one of your expressions\n" \
                            f"Original error is: \n {e}\n" \
                            f"Please try to write those expressions again according to the rules"
            update.message.reply_text(text=error_message)
            return INTERNAL_VARIABLE_API_MAPPING
        key_expression_mapping = user_generated_bot.apis[-1].key_expression_map()
        ref_keys_text = "Your keys have been validated and we have saved them\n" \
                        "Here is the key-expression mapping (In this format {Key} = {Expression}):\n" \
                        f"{key_expression_mapping}"
        update.message.reply_text(text=ref_keys_text)
        box_number = user_generated_bot.add_box(box_msg=f'Internal variable api: {key},'
                                                        f' Note: this box will be invisible to the user',
                                                box_type=BOX_TYPE_INTERNAL_VARIABLE,
                                                api_obj=user_generated_bot.apis[-1])
        # add to graph
        # support add edge to and from this box
        update.message.reply_text(
            text=f'You have successfully created an internal variable assignment, with the number '
                 f'of {box_number} '
                 f'Please remember that the box cannot print and every edge from it is in the '
                 f'following syntax:\n '
                 f'{box_number}.0->destination')
        return BotEngine.edit_bot(update, context)