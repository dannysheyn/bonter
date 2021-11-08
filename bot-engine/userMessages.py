QUERY_PARAMS_MESSAGE = "Nice!\n" \
                   "Now we need to get the query parameters that this endpoint expects to get\n" \
                   "Please write key value pairs separated by & (For example: destination=israel&origin=Germany)\n" \
                   "The request will be made according to the values the end user will input\n" \
                   "If there are no query parameters type None"

BOT_START = 'Please enter a conversation box using this notation:\n' + \
                                  'Each conversation box will have main text and buttons \n' + \
                                  '1)─────────────────────────┐\n' + \
                                  '│ Main text:               │\n' + \
                                  '│─────────────────────────│\n' + \
                                  '│1.1)Button1 │ 1.2)Button2 │\n' + \
                                  '└─────────────────────────┘\n' + \
                                  'you can connect boxes with the add edge command and the folowing notation: 1.1->2\n' + \
                                  'will connect box button 1.1 to box 2.\n' + \
                                  'The Start will be automatically linked to box #1, or you can skip the staring box.'
TEXT_GET_KEY = "What keys would you like to show the user from this response?\n" \
                           "Write Json expressions which evaluate to your keys separated by commas, for example: [origin], " \
                           "[destination][flight_num], etc...\n " \
                           "If the key are inside an array you need to index it, for example: [0][origin], " \
                           "[destination][1]\n" \
                           "You can use nesting for dictionaries as well, for example: [data][name], [0][data][time]\n" \
                           "You can also type in expressions which are arrays and we will get all the keys there\n"

HEADER_MESSAGE = "If there are any headers to the request please enter them in the following matter:\n" \
               "for example: api_key=<apikey>, host=<host>.\n" \
               "Please separate the key and the value with '=' sign.\n" \
               "Different headers separate with ',' " \
               "If there are no headers enter None"