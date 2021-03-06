from telegram import Update
from telegram.ext import CallbackContext

import requests
import re
import json


# Notes:
# callable api that gets an api object
# user enters query params independently
# how does the client choose how to show to user an array?

class API:
    def __init__(self, uri=None, query_params={}, authorization=None, expressions=None):
        self.uri = uri
        self.query_params = query_params # will change based on end user
        self.authorization = authorization
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
        response = requests.get(self.uri, params=self.query_params, headers={"Authorization": self.authorization})
        return response

    def validate_keys(self, save_response=False):
        for expression in self.expressions: # ["title"], ["body"]
            expression = expression.replace('"', '')
            elements = re.findall(r"\[([A-Za-z0-9_]+)\]", expression)
            response_json = self.get_api_response()
            response = json.loads(response_json.text)
            prev_key = None
            # TODO: Improve Error handling
            for element in elements:
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
                        raise IndexError(f"In the expression {expression} the index {element} does not exist in the list")
                    if isinstance(response, dict):
                        raise KeyError(f"In the expression {expression} The key {element} is not a valid key in "
                                       f"this dictionary context")
                response = response[element]
                prev_key = element

            if save_response:
                self.key_expression[prev_key] = (expression, response) # [0][text][2][time] , '10:00'
            else:
                self.key_expression[prev_key] = expression

    def key_expression_map(self):
        mapping = ""
        for key, expression in self.key_expression.items():
            mapping += f"{key} = {expression}\n"
        return mapping

    def parse_message_to_user(self): # hello user the flight from ${dest:[0][text][2][time]} to ${origin:} is
        self.validate_keys(True)
        variables = re.findall(r"\$\{([A-Za-z0-9_]+)\}", self.message_to_user)
        for variable in variables:
            replacement = self.key_expression[variable][1]
            self.message_to_user = re.sub(r"\$\{([A-Za-z0-9_]+)\}", replacement, self.message_to_user, 1)
