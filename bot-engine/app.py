from telegram.ext import ConversationHandler, CommandHandler, CallbackQueryHandler, MessageHandler, Filters

from .EngineStates.TimedAcationFlow import TimedActionFlow

from .EngineStates.ApiFlow import ApiFlow

from .EngineStates.UserVariablesFlow import UserVariableFlow

from .EngineStates.InternalVariableFlow import InternalVariableFlow
from botEngine import BotEngine
from EngineStates import *
API_KEY = "YOUR_KEY"

def main():
    import os
    os.environ["PATH"] += os.pathsep + 'C:/Program Files/Graphviz/bin'
    mainbot = BotEngine(bot_name='engineBot', api_key="API_KEY",
                        conv_handler=None)
    dispatcher = mainbot.updater.dispatcher
    global edit_bot
    edit_bot = mainbot.edit_bot
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', mainbot.main_menu)],
        states={
            MAIN_MENU: [
                CallbackQueryHandler(mainbot.choose_bot_to_edit, pattern='^' + str(CHOOSE_BOT) + '$'),
                CallbackQueryHandler(mainbot.start, pattern='^' + str(CREATE_BOT) + '$'),
                CallbackQueryHandler(mainbot.choose_bot_to_view_chats, pattern='^' + str(CHOOSE_BOT_CHATS) + '$'),
            ],
            VIEW_CHATS: [MessageHandler(Filters.text, mainbot.view_chats)],
            GET_BOT: [MessageHandler(Filters.text, mainbot.get_bot)],
            GET_API_KEY: [MessageHandler(Filters.text, mainbot.get_api_key)],
            EDIT_BOT: [
                CallbackQueryHandler(mainbot.choose_box, pattern='^' + str(CHOOSE_BOX) + '$'),
                CallbackQueryHandler(mainbot.choose_node_to_delete, pattern='^' + str(CHOOSE_NODE_TO_DELETE) + '$'),
                CallbackQueryHandler(mainbot.add_box_button, pattern='^' + str(ADD_BOX_BUTTON) + '$'),
                CallbackQueryHandler(mainbot.add_edge, pattern='^' + str(ADD_EDGE) + '$'),
                CallbackQueryHandler(mainbot.print_bot, pattern='^' + str(PRINT_BOT) + '$'),
                CallbackQueryHandler(mainbot.define_bot_start, pattern='^' + str(END) + '$'),
                CallbackQueryHandler(TimedActionFlow.timer_action, pattern='^' + str(TIMER_ACTION) + '$'),
            ],
            BOX_DECISION: [
                CallbackQueryHandler(mainbot.add_text_box, pattern='^' + str(ADD_TEXT_BOX) + '$'),
                CallbackQueryHandler(ApiFlow.start_api_flow, pattern='^' + str(ADD_API_BOX) + '$'),
                CallbackQueryHandler(UserVariableFlow.add_user_variable_box,
                                     pattern='^' + str(ADD_USER_VARIABLE) + '$'),
                CallbackQueryHandler(InternalVariableFlow.internal_variable_assignment_start_flow,
                                     pattern='^' + str(INTERNAL_VARIABLE_ASSIGNMENT_START_FLOW) + '$'),
            ],
            DELETE_NODE: [MessageHandler(Filters.text, mainbot.delete_node)],
            INIT_BOT: [MessageHandler(Filters.text, mainbot.init_user_bot)],
            GET_BASE_API: [MessageHandler(Filters.text, ApiFlow.get_base_api)],
            GET_AUTHORIZATION: [MessageHandler(Filters.text, ApiFlow.get_authorization_header)],
            GET_KEY_FROM_RESPONSE: [MessageHandler(Filters.text, ApiFlow.get_keys_to_retrieve)],
            GET_MESSAGE_TO_USER: [MessageHandler(Filters.text, ApiFlow.get_message_to_user)],
            ADD_TEXT_BOX2: [MessageHandler(Filters.text, mainbot.add_text_box2)],
            ADD_EDGE2: [MessageHandler(Filters.text, mainbot.add_edge2)],
            ADD_BOX_BUTTON2: [MessageHandler(Filters.text, mainbot.add_box_button2)],
            ADD_BOX_BUTTON3: [MessageHandler(Filters.text, mainbot.add_box_button3)],
            TIMER_ACTION2: [MessageHandler(Filters.text, TimedActionFlow.timer_action2)],
            TIMER_ACTION3: [MessageHandler(Filters.text, TimedActionFlow.timer_action3)],
            USER_VARIABLE2: [MessageHandler(Filters.text, UserVariableFlow.add_user_variable_box2)],
            USER_VARIABLE3: [MessageHandler(Filters.text, UserVariableFlow.add_user_variable_box3)],
            GET_INTERNAL_VARIABLE: [
                MessageHandler(Filters.text, InternalVariableFlow.internal_variable_assignment_name)],
            INTERNAL_VARIABLE_SOURCE: [
                MessageHandler(Filters.text, InternalVariableFlow.internal_variable_assignment_source)],
            INTERNAL_VARIABLE_INSTANT_VALUE: [
                MessageHandler(Filters.text, InternalVariableFlow.internal_variable_instant_value)],
            INTERNAL_VARIABLE_API_VALUE: [
                MessageHandler(Filters.text, InternalVariableFlow.internal_variable_api_value_start)],
            INTERNAL_VARIABLE_API_HEADERS: [
                MessageHandler(Filters.text, InternalVariableFlow.internal_variable_api_headers)],
            INTERNAL_VARIABLE_API_MAPPING: [
                MessageHandler(Filters.text, InternalVariableFlow.internal_variable_api_mapping)],

        },
        fallbacks=[CommandHandler('cancel', mainbot.start)],
    )
    dispatcher.add_handler(conv_handler)
    mainbot.updater.start_polling()
    # mainbot.updater.idle()


if __name__ == '__main__':
    main()
