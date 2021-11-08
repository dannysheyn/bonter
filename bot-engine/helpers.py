import collections
from collections import defaultdict
from pymongo import MongoClient
from telegram import Update, Message, CallbackQuery

from telegram.ext import CallbackContext

import userGeneratedBot


def get_user_name(update):
    if isinstance(update, CallbackQuery):
        if update.from_user.username:
            return update.from_user.username
        else:
            return update.from_user.first_name
    else:
        if update.effective_user.username:
            return update.effective_user.username
        elif update.effective_user.first_name:
            return update.effective_user.first_name
        else:
            return update.message.chat.id


def add_chat(client: MongoClient, update: Update, context: CallbackContext):
    """
    Creates a new chat document, if it wasn't yet created with this bot.
    And adds a message to the messages array
    """
    db = client.bonter
    chat_id = update.message.chat.id
    bot_token = context.bot.token
    user_name = get_user_name(update)
    chat_id = str(chat_id)
    if db.chats.count_documents({"bot_token": bot_token}, limit=1) == 0:
        chat = {
            "bot_token": bot_token,
            "bot_name": context.bot.username,
            "userName": user_name,
            "messages": {chat_id: []}
        }
        db.chats.insert_one(chat)

    if db.chats.find({"messages": chat_id}, limit=1) == 0:
        db.chats.update({'bot_token': bot_token}, {'$set': {'messages': {chat_id: []}}})
    add_message(db, update.message, bot_token, chat_id, user_name)


def add_message(db, telegram_message: Message, bot_token, chat_id, user_name):
    # Do we also want to record what the bot has answered ?
    if telegram_message.from_user.is_bot:
        to_user = telegram_message.chat.username
    else:
        to_user = telegram_message.bot.username
    message = {
        "date": telegram_message.date,
        "from": user_name,
        "to": to_user,
        "text": telegram_message.text
    }
    db.chats.update({'bot_token': bot_token}, {'$push': {f'messages.{chat_id}': message}})


def add_user(client, update: Update):
    db = client.bonter
    if db.users.count_documents({"userId": update.effective_user.id}, limit=1) == 0:
        user = {
            "fullName": update.effective_user.full_name,
            "userId": update.effective_user.id,
            "bots": []
        }
        db.users.insert_one(user)


def add_bot(client: MongoClient, update: Update, user_generated_bot: userGeneratedBot):
    db = client.bonter
    db.users.update({'userId': update.effective_user.id}, {'$push': {'bots': create_bot_dict(user_generated_bot)}})


def update_bot(client: MongoClient, update: Update, user_generated_bot: userGeneratedBot):
    db = client.bonter
    user = db.users.find_one({"userId": update.effective_user.id})
    index = 0
    for bot in user["bots"]:
        if bot["api_key"] == user_generated_bot.api_key:
            break
        index += 1
    db.users.update(
        {'userId': update.effective_user.id, "bots.api_key": user_generated_bot.api_key},
        {"$set": {'bots.$': create_bot_dict(user_generated_bot)}})


def get_bot(client, api_key: str, user_id: str):
    db = client.bonter
    # criteria for api_key to choose specific bot
    user = db.users.find_one({"userId": user_id})
    for bot in user["bots"]:
        if bot["api_key"] == api_key:
            return bot
    return -1


def get_chats(client, bot_token):
    db = client.bonter
    bot_name = None
    bot_document = db.chats.find_one({"bot_token": bot_token})
    if bot_document:
        bot_name = bot_document["bot_name"]
    return bot_document["messages"], bot_name


def decode_states(states):
    state_string = ''
    raw_states = defaultdict(list)
    for key, state in states.items():
        if key == 1:
            # add type of callable
            for query_handler in state:
                callback_timer = query_handler.callback.set_timer
                query_handler.callback.set_timer = None
                if isinstance(query_handler.callback.next_state, collections.Callable):
                    next_state_callback = query_handler.callback.next_state
                    query_handler.callback.next_state = {'box_number': next_state_callback.box_number}
                    raw_states["query_handlers"].append(my_dict(query_handler.callback))
                    query_handler.callback.next_state = next_state_callback
                else:
                    raw_states["query_handlers"].append(my_dict(query_handler.callback))
                if callback_timer is not None:
                    raw_states["query_handlers"][-1]["timer_action"] = \
                        {'params': callback_timer.params}
                    query_handler.callback.set_timer = callback_timer
                if hasattr(query_handler.callback, 'obj'):
                    raw_states["query_handlers"][-1]['obj_type'] = type(query_handler.callback.obj).__name__
                raw_states["query_handlers"][-1]["callback_type"] = type(query_handler.callback).__name__

        else:
            callback_timer = state[0].callback.set_timer
            next_state_callback_timer = None
            if isinstance(state[0].callback.next_state, collections.Callable):
                next_state_callback_timer = state[0].callback.next_state
                state[0].callback.next_state = {'box_number': next_state_callback_timer.box_number}
            raw_states["message_handlers"].append(
                my_dict(state[0].callback))  # Because MessageHandler is in the form of [MessageHandler]
            raw_states["message_handlers"][-1]["callback_type"] = type(state[0].callback).__name__
            if hasattr(state[0].callback, 'obj'):
                raw_states["message_handlers"][-1]['obj_type'] = type(state[0].callback.obj).__name__
            if isinstance(next_state_callback_timer, collections.Callable):
                state[0].callback.next_state = next_state_callback_timer

    return raw_states


def create_bot_dict(user_generated_bot: userGeneratedBot):
    # TODO: When adding a bot add a field that states an objects type
    # For it not to be only for API objects
    api_endpoints = []
    for api in user_generated_bot.apis:
        api_endpoints.append(my_dict(api))
    bot_data = {
        "api_key": user_generated_bot.api_key,
        # "message_handler_key": user_generated_bot.message_handler_key,
        "entry_point_message": user_generated_bot.entry_point.callback.msg,
        "states": decode_states(user_generated_bot.states),
        # "pattern": user_generated_bot.pattern,
        "api_endpoints": api_endpoints,
        "bot_pic": decode_bot_pic(my_dict(user_generated_bot.bot_graph))
    }
    return bot_data


def decode_bot_pic(bot_pic):
    raw_bot_pic = defaultdict(list)
    timer = None
    next_callback = None
    for key, value in bot_pic["bot_nodes"].items():
        timer = value.callback.set_timer
        value.callback.set_timer = None
        if value.callback.set_timer is not None:
            value.callback.set_timer = {'params': timer.params}
        if isinstance(value.callback.next_state, collections.Callable):
            next_callback = value.callback.next_state
            value.callback.next_state = {'box_number': next_callback.box_number}
        raw_bot_pic["bot_nodes"].append(my_dict(value))
        value.callback.set_timer = timer
        if isinstance(value.callback.next_state, dict):
            value.callback.next_state = next_callback
    for value in bot_pic["bot_edges"]:
        raw_bot_pic["bot_edges"].append(my_dict(value))

    return raw_bot_pic


def my_dict(obj):
    if not hasattr(obj, "__dict__"):
        return obj
    result = {}
    for key, val in obj.__dict__.items():
        if key.startswith("_"):
            continue
        element = []
        if isinstance(val, list):
            for item in val:
                element.append(my_dict(item))
        else:
            element = my_dict(val)
        result[key] = element
    return result


#
# {
#     messages: {
#         chat_id: [],
#         chat_id: [],
#     }
# }