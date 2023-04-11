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

from utils import MacroGPTJSON, MacroNLG, MacroGPTJSONNLG, gpt_completion, MacroMakeFillerText, MacroMakeToughResponse, \
    MacroMakeSummary


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


def set_summary(vars: Dict[str, Any], user: Dict[str, Any]):
    vars['SUMMARY'] = user['SUMMARY']


available_states = ['user_understanding_of_prob', 'what_will_help', 'finding_solutions', 'when_problem_not_present',
                    'summarize_reiterate_problem']


def generate_prompt(vars: Dict[str, Any]):
    prompt_parts = []
    if 'PROBLEM_SUMMARY' not in vars:
        prompt_parts.append('"PROBLEM_SUMMARY": "trouble at work"')
    if 'PROBLEM_DETAILS' not in vars:
        prompt_parts.append('"PROBLEM_DETAILS": "Having trouble at work due to not being able to manage time, boss does not like them, eats too much"')
    if 'USER_SOLUTIONS' not in vars:
        prompt_parts.append('"USER_SOLUTIONS": "ate less, delegated work, managed time better"')


    prompt_parts.append(f'"NEXT_STATE": {"{" + ", ".join(f"{state}" for state in available_states) + "}"}')

    prompt = f'Please provide the missing information and choose the next logically best state from the given options. You may ONLY choose from the given options. If no state seems best,' \
             f'summarize and reiterate the problem.' \
             f'Respond in the one-line JSON format such as {{{", ".join(prompt_parts)}}}: '

    return prompt


# Set problem response variables and the next state
def set_problem_response(vars: Dict[str, Any], user: Dict[str, Any]):
    if user['PROBLEM_SUMMARY'] != 'n/a':
        vars['PROBLEM_SUMMARY'] = user['PROBLEM_SUMMARY']
    if user['PROBLEM_DETAILS'] != 'n/a':
        vars['PROBLEM_DETAILS'] = user['PROBLEM_DETAILS']
    if user['USER_SOLUTIONS'] != 'n/a':
        vars['USER_SOLUTIONS'] = user['USER_SOLUTIONS']

    if 'NEXT_STATE' in user:
        if user['NEXT_STATE'] in available_states:
            available_states.remove(user['NEXT_STATE'])
        vars['__target__'] = f"{user['NEXT_STATE']}"


macros = {
    'GET_PROBLEM_RESPONSE': MacroGPTJSONNLG(
        generate_prompt,
        {'PROBLEM_SUMMARY': 'trouble at work', 'PROBLEM_DETAILS': 'Having trouble at work due to not being able to manage time, boss does not like them, eats too much',
         'USER_SOLUTIONS': 'ate less, delegated work, managed time better',
         'NEXT_STATE': 'summarize_reiterate_problem'},
        {'PROBLEM_SUMMARY': 'n/a', 'PROBLEM_DETAILS': 'n/a', 'USER_SOLUTIONS': 'n/a',
         'NEXT_STATE': 'summarize_reiterate_problem'},
        set_problem_response
    ),
    'SET_CALL_NAME': MacroGPTJSON(
        'What does the speaker want to be called? Give only one name. Respond in the one-line JSON format such as {"call_names": ["Mike", "Michael"]}: ',
        {User.call_name.name: ["Mike", "Michael"]},
        {User.call_name.name: "n/a"},
        set_call_names
    ),
    
    'GET_CALL_NAME': MacroNLG(get_call_name),
    'FILLER_RESPONSE': MacroMakeFillerText(),
    'TOUGH_RESPONSE': MacroMakeToughResponse(),
    'GET_SUMMARY': MacroMakeSummary(),
}

"""
'SET_FUN_FACT': MacroGPTJSON(
    'write a fun fact in the one line JSON format: ',
    {'FUN_FACT': "The Eiffel Tower can grow up to six inches during the summer due to thermal expansion."},
    None,
    set_fun_fact
),


'GET_HOBBY_STATEMENT': MacroGPTJSONNLG(
    'What hobby is the speaker talking about? Respond in the one-line JSON format such as {"hobby": ["Basketball", "Soccer"]}: ',
    {'Hobbies': ["Basketball", "Soccer"]},
    {'Hobbies': "n/a"},
    set_user_hobby,
),
'#GET_HOMETOWN_NAME': MacroGPTJSONNLG(
    'What is the speakers hometown? Respond in the one-line JSON format such as {"HOMETOWN": ["Atlanta"]}: ',
    {'HOMETOWN': ["Detroit"]},
    {'HOMETOWN': "n/a"},
    set_user_hometown,
),
'#GET_LIKES_HOMETOWN': MacroGPTJSONNLG(
    'Does the speaker like their hometown? Respond in the one-line JSON format such as {"LIKES_HOMETOWN: ["YES"]}: ',
    {'LIKES_HOMETOWN': ["NO"]},
    None,
    set_user_likeshometown,
),
'GET_PROFESSOR_PROBLEM_ADVICE': MacroGPTJSONNLG(
    'What is the speakers problem? Respond in the one-line JSON format such as {"problem": ["workload", "communication"]}: ',
    {'Problems': ["workload", "communication"]},
    {'Problems': "n/a"},
    set_professor_problem,
),

'GET_FUN_FACT': MacroNLG(get_fun_fact),
'GET_USER_HOBBY': MacroNLG(get_hobby),
'GET_PROFESSOR_PROBLEM': MacroNLG(get_professor_problem),
'GET_PARTNER_STATUS': MacroGPTJSONNLG(
    'What is the speaker\'s relationship status with their partner? Respond in the one-line JSON format such as {"PARTNER_STATUS": "good"}: ',
    {'PARTNER_STATUS': "good"},
    {'PARTNER_STATUS': "n/a"},
    set_partner_status,
),
'GET_FRIEND_STATUS': MacroGPTJSONNLG(
    'What is the speaker\'s relationship status with their friend? Respond in the one-line JSON format such as {"FRIEND_STATUS": "good"}: ',
    {'FRIEND_STATUS': "good"},
    {'FRIEND_STATUS': "n/a"},
    set_friend_status,
),
'GET_STRONG_ATTRIBUTE': MacroGPTJSONNLG(
    'What is a strong attribute the speaker mentioned about their relationship? Respond in the one-line JSON format such as {"STRONG_ATTRIBUTE": "communication"}: ',
    {'STRONG_ATTRIBUTE': "communication"},
    {'STRONG_ATTRIBUTE': "n/a"},
    set_strong_attribute,
),
'GET_CHALLENGE': MacroGPTJSONNLG(
    'What is a challenge the speaker is facing in their relationship? Respond in the one-line JSON format such as {"CHALLENGE": "communication"}: ',
    {'CHALLENGE': "communication"},
    {'CHALLENGE': "n/a"},
    set_challenge,
),
'GET_CONFUSION': MacroGPTJSONNLG(
    'What is causing confusion or mixed feelings in the speaker\'s relationship? Respond in the one-line JSON format such as {"CONFUSION": "priorities"}: ',
    {'CONFUSION': "priorities"},
    {'CONFUSION': "n/a"},
    set_confusion,
),
'GET_FRIEND_CHALLENGE': MacroGPTJSONNLG(
    'What is a challenge the speaker is facing in their relationship with their friend? Respond in the one-line JSON format such as {"FRIEND_CHALLENGE": "communication"}: ',
    {'FRIEND_CHALLENGE': "communication"},
    {'FRIEND_CHALLENGE': "n/a"},
    set_friend_challenge,
),
'GET_FRIEND_CONFUSION': MacroGPTJSONNLG(
    'What is causing confusion or mixed feelings in the speaker\'s relationship with their friend? Respond in the one-line JSON format such as {"FRIEND_CONFUSION": "priorities"}: ',
    {'FRIEND_CONFUSION': "priorities"},
    {'FRIEND_CONFUSION': "n/a"},
    set_friend_confusion,
)
"""
