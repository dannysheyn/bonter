from telegram import Update
from telegram.ext import CallbackContext

import requests
import re
import json

# Notes:
# callable api that gets an api object
# user enters query params independently
# how does the client choose how to show to user an array?
from botEngine import GET_QUERY_PARAMS, GET_AUTHORIZATION
import curlify


class API:
    def __init__(self, uri=None, query_params=None, headers=None, expressions=None):
        if query_params is None:
            query_params = {}
        if headers is None:
            headers = {}
        self.uri = uri  # ${user_id:32412}&limit=5  | ?id=e42535
        self.query_params = query_params  # will change based on end user
        self.headers = headers
        self.expressions = expressions  # expressions for json parsing of key-value according to syntax ([flights][dest])
        self.key_expression = {}
        self.message_to_user = None
        # We want to map keys to their expressions,
        # So we can then show the client ${key},
        # To easily create a text to the end user
        # Expressions give us the path to the value
        # For now we assume key is the last key in the expression

    def parse_query_params(self, query_params):
        key_values = query_params.split(',')

        for key_value in key_values:
            key, value = key_value.split('=')
            self.query_params[key] = value

    def get_api_response(self):
        headers = {
            'x-rapidapi-host': "hotels4.p.rapidapi.com",
            'x-rapidapi-key': "28ef563eb3msh228e99b9a719be9p1e0652jsn69b0cd67ed65"
        }
        uri = self.sub_url_with_defualt_params(uri=self.uri)
        response = requests.get(uri, params=self.query_params, headers=self.headers)
        # for debgu
        print(curlify.to_curl(response.request))
        return response

    def sub_url_with_defualt_params(self, uri) -> str:
        query_variables = re.findall(r'\$\{.+?\}', uri)
        if query_variables:  # if in the url there are variables in the form of ${var}
            uri = self.sub_variables_with_defualt_values(query_variables, uri)
        return uri

    def sub_variables_with_defualt_values(self, query_variables, url) -> str:
        defual_params = list(map(lambda match: match.split(':')[1][:-1], query_variables))
        for param in defual_params:
            url = re.sub('\$\{.+?}', param, url, 1)
        return url

    def handle_response(self, response):
        text = "Now we need to get the query parameters that this endpoint expects to get\n" \
               "Please write key value pairs separated by & (For example: destination=israel&origin=Germany)\n" \
               "The request will be made according to the values the end user will input\n" \
               "If there are no query parameters type None"
        if response.status_code == 200:
            text = f'Nice!\n{text}'
        elif response.status_code == 403 or response.status_code == 401:
            text = "The endpoint requires authorization.\n" \
                   "Please provide us with valid authorization headers as a key value pairs, in future step.\n" + text
            # "for example: api_key=<apikey>, host=<host>.\n" \
            # "Please separate the key and the value with '=' sign.\n" \
            # "Different headers separate with ',' "
        else:
            text = f"We got a status code of {response.status_code}, we will continue the process but, please note that" \
                   f"the api could be corrupted.\n" + text
        return text

    def validate_keys(self, save_response=False, use_uri_to_check=False):
        prev_key_times = {}
        response_json = self.get_api_response()
        response_json_original = json.loads(response_json.text)
        for index, expression in enumerate(self.expressions):  # ["title"], ["body"]
            expression = expression.replace('"', '')
            elements = re.findall(r"\[([A-Za-z0-9_]+)\]", expression)
            response = response_json_original
            prev_key = None
            # TODO: Improve Error handling
            for element in elements:
                try:
                    element = self.validate_key_elements(element, expression, prev_key, response, save_response)
                    response = response[element]
                except (IndexError, KeyError) as e:
                    if save_response:
                        response = ''
                        break
                    else:
                        print(e)
                        raise e
            prev_key = elements[-1]
            if save_response:
                if prev_key in prev_key_times:
                    self.key_expression[
                        prev_key + f'{prev_key_times[prev_key]}'] = expression, response  # [0][text][2][time] , '10:00'
                    prev_key_times[prev_key] += 1
                else:
                    prev_key_times[prev_key] = 1
                    self.key_expression[prev_key] = (expression, response)  # [0][text][2][time] , '10:00'
            else:
                if prev_key in prev_key_times:
                    self.key_expression[prev_key + f'{prev_key_times[prev_key]}'] = expression
                    prev_key_times[prev_key] += 1
                else:
                    prev_key_times[prev_key] = 1
                    self.key_expression[prev_key] = expression

    def validate_key_elements(self, element, expression, prev_key, response, save_response):
        if not element.isnumeric() and element not in response:
            if prev_key is not None:
                raise KeyError(f"In the expression {expression} the key {element} does not exist in the "
                               f"context of '{prev_key}'")
            else:
                raise KeyError(f"In the expression {expression} the key {element} does not exist in this "
                               f"context")
        if element.isnumeric():
            element = int(element)
            if isinstance(response, list) and not (0 <= int(element) < len(response)):
                if not save_response:
                    raise IndexError(
                        f"In the expression {expression} the index {element} does not exist in the list")
            if isinstance(response, dict):
                if not save_response:
                    raise KeyError(f"In the expression {expression} The key {element} is not a valid key in "
                                   f"this dictionary context")
        return element

    def key_expression_map(self):
        mapping = ""
        for key, expression in self.key_expression.items():
            mapping += f"{key} = {expression}\n"
        return mapping

    def parse_message_to_user(self):  # hello user the flight from ${dest:[0][text][2][time]} to ${origin:} is
        self.validate_keys(True)
        variables = re.findall(r"\$\{([A-Za-z0-9_]+)\}", self.message_to_user)
        for variable in variables:
            if variable in self.key_expression:
                replacement = self.key_expression[variable][1]
                if isinstance(replacement, dict):
                    replacement = json.dumps(replacement)
                self.message_to_user = re.sub(r"\$\{([A-Za-z0-9_]+)\}", replacement, self.message_to_user, 1)

    def update_uri(self, uri, user_data):
        match = r'\$\{.+?}'
        if 'user_data' in user_data:
            question_dict = user_data['user_data']
            if question_dict != {}:
                variables = re.findall(match, uri)
                for var in variables:
                    elem = self.get_var_name(var)
                    if elem in question_dict:
                        uri = re.sub(match, question_dict[elem], uri, 1)

        if not re.findall(match, uri):
            return uri
        return self.sub_url_with_defualt_params(uri)

    # '${dest_id:1506246}' | '${dest_id}' -> 'dest_id'
    def get_var_name(self, var):
        if ':' in var:
            index = var.find(':')
            return var.split(':')[0][2:]
        else:
            return var[2:-1]
# str -> subb all user_data -> sub all key expression
