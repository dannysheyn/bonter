# for key, state in list(user_generated_bot.states.items()):
#     for s in state:
#         print(f'key of this callback: {key}')
#         print(f'callback will say: {s.callback.msg}')
#         print(f'callback will return: {s.callback.next_state}')
#         print(f'buttons are:')
#         for buttons in s.callback.replay_buttons:
#             for button in buttons:
#                 print(f'text:{button["text"]} will return: {button["callback_data"]}')
#         print('----------------------------------------------------------')
# query.message.reply_text(text=user_generated_bot.print_conversation())

# def ask_command(self, update: Update, context: CallbackContext):
#     query = update.callback_query
#     query.answer()
#     query.edit_message_text('Currently the bot knows this commands')
#     counter = 1
#     message = ""
#     for command in self.generated_bots[update.effective_user.id].commands:
#         message += f"{counter}. {command}\n"
#         counter += 1
#
#     query.message.reply_text(text=message)
#     query.message.reply_text('Please type a new command that the bot will respond to (will be shown as a button)')
#     return ADD_COMMAND
#
# def add_command(self, update: Update, context: CallbackContext):
#     command = update.message.text
#     self.generated_bots[update.effective_user.id].commands.append(command)
#     update.message.reply_text('What will the bot answer to this command?')
#     return ADD_RESPONSE
#
# def add_response(self, update: Update, context: CallbackContext):
#     response = update.message.text
#     user_generated_bot = self.generated_bots[update.effective_user.id]
#     last_command = user_generated_bot.commands[-1]
#     last_key = user_generated_bot.state_keys
#     # last_command = products..
#     # respose = iphone3.., ..,
#     # user_generated_bot.states[last_key] = [
#     #     MessageHandler(filters=Filters.text, callback=Button('', (last_key + 1), [last_command]))]  # button handler
#     # user_generated_bot.state_keys += 1
#     # last_key = user_generated_bot.state_keys
#     # user_generated_bot.states[last_key] = [
#     #     MessageHandler(filters=Filters.text, callback=Answer(response, last_key))]  # answer handler
#     keyboard_callback = CallbackQueryHandler(CallablePrint(response, last_key),
#                                              pattern='^' + str(user_generated_bot.button_key) + '$')
#     if last_key not in user_generated_bot.states:
#         user_generated_bot.states[last_key] = []
#     user_generated_bot.states[last_key].append(keyboard_callback)
#     user_generated_bot.states[last_key][-1].callback.add_button(
#         [InlineKeyboardButton(text=last_command, callback_data=str(user_generated_bot.button_key))]
#     )
#     # if self.follow_up == False:
#     #     user_generated_bot.entry_points[0].callback.add_button(
#     #         [InlineKeyboardButton(text=last_command, callback_data=str(user_generated_bot.button_key))]
#     #     )
#     #     user_generated_bot.button_key += 1
#     #     self.follow_up = True
#     menu_text = 'what do you want to do next?\n' \
#                 'please choose one of the following:'
#     menu_buttons = [[InlineKeyboardButton(text='Add new command', callback_data=str(ASK_COMMAND))],
#                     [InlineKeyboardButton(text='Add follow up question to this command',
#                                           callback_data=str(ADD_FOLLOW_UP))],
#                     [InlineKeyboardButton(text='Add edge between a button and a box', callback_data=str(END))],
#                     [InlineKeyboardButton(text='End building bot', callback_data=str(END))],
#                     ]
#     menu_keyboard = InlineKeyboardMarkup(menu_buttons)
#     update.message.reply_text(text=menu_text, reply_markup=menu_keyboard)
#     return SELECTION

# def start_user_bot(self, user_generated_bot):
#     user_generated_bot.dispatcher.add_handler(user_generated_bot.conv_handler)
#     user_generated_bot.updater.start_polling()
#     user_generated_bot.updater.idle()
#
#     def add_follow_up(self, update: Update, context: CallbackContext):
#         query = update.callback_query
#         query.answer()
#         user_generated_bot = self.generated_bots[update.effective_user.id]
#         last_key = user_generated_bot.state_keys
#         user_generated_bot.state_keys += 1
#         user_generated_bot.states[last_key][-1].callback.next_state = user_generated_bot.state_keys
#         query.message.reply_text(
#             'Please enter a command that the bot will respond to (will be shown as a button)\n (this is a nested '
#             'command)')
#         self.follow_up = True
#         return ADD_COMMAND