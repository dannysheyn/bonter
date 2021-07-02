from collections import defaultdict

import pymongo
from pymongo import MongoClient
from telegram import Update
import json
import userGeneratedBot
import uuid


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


def decode_states(states):
    state_string = ''
    raw_states = defaultdict(list)
    for key, state in states.items():
        if key == 1:
            # add type of callable
            for query_handler in state:
                raw_states["query_handlers"].append(my_dict(query_handler.callback))
                if hasattr(query_handler.callback, 'obj'):
                    raw_states["query_handlers"][-1]['obj_type'] = type(query_handler.callback.obj).__name__
                raw_states["query_handlers"][-1]["callback_type"] = type(query_handler.callback).__name__
        else:
            raw_states["message_handlers"].append(
                my_dict(state[0].callback))  # Because MessageHandler is in the form of [MessageHandler]
            raw_states["message_handlers"][-1]["callback_type"] = type(state[0].callback).__name__
            if hasattr(state[0].callback, 'obj'):
                raw_states["query_handlers"][-1]['obj_type'] = type(state[0].callback.obj).__name__
    return raw_states


def create_bot_dict(user_generated_bot: userGeneratedBot):
    # TODO: When adding a bot add a field that states an objects type
    # For it not to be only for API objects
    api_endpoints = []
    for api in user_generated_bot.apis:
        api_endpoints.append(my_dict(api))
    bot_data = {
        "api_key": user_generated_bot.api_key,
        #"message_handler_key": user_generated_bot.message_handler_key,
        "entry_point_message": user_generated_bot.entry_points[0].callback.msg,
        "states": decode_states(user_generated_bot.states),
        #"pattern": user_generated_bot.pattern,
        "api_endpoints": api_endpoints,
        "bot_pic": decode_bot_pic(my_dict(user_generated_bot.bot_graph))

    }
    return bot_data

def decode_bot_pic(bot_pic):
    raw_bot_pic = defaultdict(list)
    for key, value in bot_pic["bot_nodes"].items():
        raw_bot_pic["bot_nodes"].append(my_dict(value))

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
