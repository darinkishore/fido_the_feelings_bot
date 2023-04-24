from emora_stdm import DialogueFlow
import spacy
import time
import requests
import json
import sqlite3

import re
from emora_stdm import Macro, Ngrams
from typing import Dict, Any, List
from enum import Enum

from emora_stdm.state_transition_dialogue_manager import dialogue_flow

from utils_babel import MacroGPTJSON, MacroNLG, MacroGPTJSONNLG, gpt_completion, MacroMakeFillerText, MacroMakeToughResponse, \
    MacroMakeSummary, MacroMakeSuggestions, babel_completion, babel_wrap_up




class User(Enum):
    call_name = 'call_name'
    hometown = 1
    likes_hometown = 2
    hometown_good = 3
    hobbies = 4
    friends = 5
    PROBLEM_SUMMARY = 6
    PROBLEM_DETAILS = 7
    USER_SOLUTIONS = 8


def get_call_name(vars: Dict[str, Any]):
    ls = vars[User.call_name.name]
    return ls


def set_call_names(vars: Dict[str, Any], user: Dict[str, Any]):
    vars[User.call_name.value] = user[User.call_name.value]

num_iterations = 0
conversation_context = []

class MacroBabelResponse(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        global conversation_context
        if vars['__selected_response__'] not in conversation_context:
            conversation_context.append(f'{vars["__selected_response__"]}\n')
        if vars['__user_utterance__'] not in conversation_context:
            conversation_context.append(f'{vars["__user_utterance__"]}')

        global num_iterations
        num_iterations += 1

        if num_iterations < 10:
            output = babel_completion(conversation_context)
        else:
            output = babel_wrap_up(conversation_context)
            vars['__target__'] = 'end'
        return output




macros = {
    'SET_CALL_NAME': MacroGPTJSON(
        'What does the speaker want to be called? Give only one name. Respond in the one-line JSON format such as {"call_names": ["Mike", "Michael"]}: ',
        {User.call_name.name: ["Mike", "Michael"]},
        {User.call_name.name: "n/a"},
        set_call_names
    ),

    'GET_CALL_NAME': MacroNLG(get_call_name),
    'BABEL_RESPONSE': MacroBabelResponse(),
}
