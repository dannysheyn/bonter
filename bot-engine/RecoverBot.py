from telegram import InlineKeyboardButton
from telegram.ext import Updater, ConversationHandler, CommandHandler, CallbackQueryHandler, MessageHandler, Filters

import userGeneratedBot
from api import API
from callableBox import TimerAction, CallableInternalAPI, CALLABLE_INTERNAL_API, CallableFollowUp, CALLABLE_FOLLOWUP, \
    CallablePrint, CALLABLE_PRINT, CallableAPI, CALLABLE_API, CallableQuestion, CALLABLE_QUESTION
from showBot import bot_edge, BotGraph, bot_node


class RecoverBot:
    @staticmethod
    def create_callback(handler, message_handler_key):
        obj = None
        callback = None
        if handler["callback_type"] != CALLABLE_PRINT and handler["obj"] is not None:
            if "obj_type" in handler:
                if handler["obj_type"] == 'API':
                    obj = API(uri=handler["obj"]["uri"], query_params=handler["obj"]["query_params"],
                              expressions=handler["obj"]["expressions"])
                    obj.message_to_user = handler["obj"]["message_to_user"]
                    obj.key_expression = handler["obj"]["key_expression"]
                    obj.headers = handler["obj"]["headers"]
                else:
                    obj = handler["obj"]
            else:  # dict
                obj = handler["obj"]
        if handler["callback_type"] == CALLABLE_QUESTION:
            callback = CallableQuestion(handler["msg"], obj, next_state=handler["next_state"])
        elif handler["callback_type"] == CALLABLE_API:
            callback = CallableAPI(msg=handler["msg"], obj=obj)

        elif handler["callback_type"] == CALLABLE_PRINT:
            callback = CallablePrint(msg=handler["msg"])

        elif handler["callback_type"] == CALLABLE_FOLLOWUP:
            callback = CallableFollowUp(obj=obj, next_state=handler["next_state"])
        elif handler["callback_type"] == CALLABLE_INTERNAL_API:
            callback = CallableInternalAPI(msg=handler["msg"], obj=obj, next_state=handler["next_state"])
        # callback.reply_buttons = handler["reply_buttons"]
        for button in handler["reply_buttons"]:  # add buttons
            callback.add_button(InlineKeyboardButton(text=button["text"], callback_data=button["callback_data"]))

        callback.box_number = handler["box_number"]

        # check if callback is a timed callback
        if "timer_action" in handler:  # callback is a timed action
            callback.set_timer = TimerAction(callback, False, handler["timer_action"]["params"])

        return callback

    @staticmethod
    def retrieve_states(raw_states):
        states = {1: []}
        callbacks_arr = []
        pattern = 0
        message_handler_key = '1'
        for handler_type, handlers in raw_states.items():
            if handler_type == "query_handlers":
                for handler in handlers:
                    callback = RecoverBot.create_callback(handler, message_handler_key)
                    callback_query_handler = CallbackQueryHandler(callback=callback,
                                                                  pattern='^' + str(callback.box_number) + '$')
                    states[1].append(callback_query_handler)
                    callbacks_arr.append(callback)
                    pattern += 1

            elif handler_type == "message_handlers":
                for handler in handlers:
                    callback = RecoverBot.create_callback(handler, message_handler_key)
                    callbacks_arr.append(callback)
                    states[message_handler_key] = [MessageHandler(callback=callback, filters=Filters.text)]
                    message_handler_key = str(int(message_handler_key) + 1)
                    if handler["is_box"]:
                        pattern += 1

        for callback in callbacks_arr:
            if isinstance(callback.next_state, dict):
                next_state_callback_number = callback.next_state['box_number']
                for destination_callback in callbacks_arr:
                    if next_state_callback_number == destination_callback.box_number:
                        callback.next_state = destination_callback

        return states, pattern, message_handler_key

    @staticmethod
    def retrieve_api_endpoints(raw_api_endpoints):
        apis = []
        for api in raw_api_endpoints:
            api_obj = API(uri=api["uri"], query_params=api["query_params"], expressions=api["expressions"])
            api_obj.message_to_user = api["message_to_user"]
            api_obj.key_expression = api["key_expression"]
            api_obj.headers = api["headers"]
            apis.append(api_obj)
        return apis

    @staticmethod
    def get_callback_init(state_dict, box_number):
        callbacksValueList = state_dict.items()
        for state, callbacks in callbacksValueList:
            for callback in callbacks:
                if callback.callback.box_number == box_number:
                    return callback, state, callback.callback.callback_type

    @staticmethod
    def determine_callback(callback):
        if type(callback) is CallbackQueryHandler:
            return callback, None
        else:
            return None, callback

    @staticmethod
    def retrieve_bot_pic(raw_bot_pic, states):
        bot_pic = BotGraph()
        for node in raw_bot_pic["bot_nodes"]:
            callabck, state, callback_type = RecoverBot.get_callback_init(states, node["box"])
            query_handler, message_handler = RecoverBot.determine_callback(callabck)
            bot_pic.bot_nodes[node["box"]] = bot_node(box=node["box"], msg=node["msg"],
                                                      query_handler=query_handler, message_handler=message_handler,
                                                      state_value=state,
                                                      box_type=callback_type)
            bot_pic.bot_nodes[node["box"]].button_list += node["button_list"]

        if "bot_edges" in raw_bot_pic:
            for edge in raw_bot_pic["bot_edges"]:
                bot_pic.bot_edges.add(bot_edge(edge["box"], edge["button"], edge["destination"]))

        return bot_pic

    @staticmethod
    def build_bot(raw_bot):
        bot = userGeneratedBot.UserGeneratedBot(api_key=raw_bot["api_key"])
        bot.states, bot.pattern, message_handler_key = RecoverBot.retrieve_states(raw_bot["states"])
        bot.apis = RecoverBot.retrieve_api_endpoints(raw_bot["api_endpoints"])
        bot.message_handler_key = message_handler_key
        bot.bot_graph = RecoverBot.retrieve_bot_pic(raw_bot["bot_pic"], bot.states)
        bot.updater = Updater(token=bot.api_key, use_context=True)
        bot.dispatcher = bot.updater.dispatcher
        bot.add_starting_point_from_message(raw_bot["entry_point_message"])
        bot.conv_handler = ConversationHandler(
            entry_points=[bot.entry_point],
            states=bot.states,
            fallbacks=[CommandHandler('cancel', bot.entry_point)],
        )
        bot.dispatcher.add_handler(bot.conv_handler)
        return bot
