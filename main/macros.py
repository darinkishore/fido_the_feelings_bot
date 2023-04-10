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

from utils import MacroGPTJSON, MacroNLG, MacroGPTJSONNLG, gpt_completion, MacroMakeFillerText

class User(Enum):
    call_name = 'call_name'
    hometown = 1
    likes_hometown = 2
    hometown_good = 3
    hobbies = 4
    friends = 5

def get_call_name(vars: Dict[str, Any]):
    ls = vars[User.call_name.name]
    return ls


def get_fun_fact(vars: Dict[str, Any]):
    return vars['FUN_FACT']


def get_hobby(vars: Dict[str, Any]):
    return vars['HOBBY']


def why_like_hobby(vars: Dict[str, Any]):
    return vars['WHY_LIKE_HOBBY']


def get_similar_hobby(vars: Dict[str, Any]):
    return vars['SIMILAR_HOBBY']


def set_call_names(vars: Dict[str, Any], user: Dict[str, Any]):
    vars[User.call_name.value] = user[User.call_name.value]


def set_fun_fact(vars: Dict[str, Any], user: Dict[str, Any]):
    vars['FUN_FACT'] = user['FUN_FACT']


def set_user_hobby(vars: Dict[str, Any], user: Dict[str, Any]):
    vars['HOBBY'] = user['HOBBY']
    generate_hobby_statement(vars)
    if vars['HOBBY'] == 'n/a':
        vars['NO_HOBBY'] = bool(True)


def set_user_hometown(vars: Dict[str, Any], user: Dict[str, Any]):
    vars['HOMETOWN'] = user['HOMETOWN']


def set_user_likeshometown(vars: Dict[str, Any], user: Dict[str, Any]):
    vars['LIKES_HOMETOWN'] = user['LIKES_HOMETOWN']
    if vars['LIKES_HOMETOWN'] == 'YES':
        vars['NO_HOMETOWN_PROBLEM'] = bool(True)
    else:
        vars['NO_HOMETOWN_PROBLEM'] = bool(False)


def set_professor_problem(vars: Dict[str, Any], user: Dict[str, Any]):
    vars['PROBLEM'] = user['PROBLEM']
    generate_problem_statement(vars)
    if vars['PROFESSOR_PROBLEM'] == 'n/a':
        vars['NO_PROFESSOR_PROBLEM'] = bool(True)


def get_professor_problem(vars: Dict[str, Any]):
    return vars['PROFESSOR_PROBLEM']


def generate_problem_statement(vars: Dict[str, Any]):
    # if vars[hobby] is a list, then randomly select one
    # else, just use vars[hobby]
    problem = vars['PROBLEM']

    if isinstance(problem, list):
        problem = random.choice(problem)
        vars['PROBLEM'] = problem

    prompt = f"Give advice about {problem}"
    output = gpt_completion(prompt)
    vars['PROBLEM_STATEMENT'] = output


def generate_hobby_statement(vars: Dict[str, Any]):
    # if vars[hobby] is a list, then randomly select one
    # else, just use vars[hobby]
    hobby = vars['HOBBY']

    if isinstance(hobby, list):
        hobby = random.choice(hobby)
        vars['HOBBY'] = hobby

    prompt = f"Give me a statement about why you like {hobby}"
    output = gpt_completion(prompt)
    vars['HOBBY_STATEMENT'] = output


def generate_similar_hobby(vars: Dict[str, Any]):
    # if vars[similar_hobby] is similar to vars[hobby], then suggest it to the user
    # similar to generate_hobby_statment, but adjust it to similar hobby needs
    similar_hobby = vars['SIMILAR_HOBBY']


def set_partner_status(vars: Dict[str, Any], user: Dict[str, Any]):
    vars['PARTNER_STATUS'] = user['PARTNER_STATUS']


def set_strong_attribute(vars: Dict[str, Any], user: Dict[str, Any]):
    vars['STRONG_ATTRIBUTE'] = user['STRONG_ATTRIBUTE']


def set_challenge(vars: Dict[str, Any], user: Dict[str, Any]):
    vars['CHALLENGE'] = user['CHALLENGE']
    generate_partner_advice(vars)


def set_confusion(vars: Dict[str, Any], user: Dict[str, Any]):
    vars['CONFUSION'] = user['CONFUSION']
    generate_partner_advice(vars)


def set_friend_status(vars: Dict[str, Any], user: Dict[str, Any]):
    vars['FRIEND_STATUS'] = user['FRIEND_STATUS']


def set_friend_challenge(vars: Dict[str, Any], user: Dict[str, Any]):
    vars['FRIEND_CHALLENGE'] = user['FRIEND_CHALLENGE']
    generate_friend_advice(vars)


def set_friend_confusion(vars: Dict[str, Any], user: Dict[str, Any]):
    vars['CONFUSION'] = user['CONFUSION']
    generate_friend_advice(vars)


def generate_prompt(vars: Dict[str, Any]):
    available_states = ['user_understanding_of_prob', 'what_will_help', 'attempts_to_solve', 'when_problem_not_present',
                        'end']

    prompt_parts = []
    if 'PROBLEM_SUMMARY' not in vars:
        prompt_parts.append('"PROBLEM_SUMMARY": "Stress at work"')
    if 'PROBLEM_DETAILS' not in vars:
        prompt_parts.append('"PROBLEM_DETAILS": "I have too many tasks to handle"')
    if 'USER_SOLUTIONS' not in vars:
        prompt_parts.append('"USER_SOLUTIONS": {"Delegation": false, "Time management": true}')

    prompt_parts.append(f'"NEXT_STATE": {available_states}')

    prompt = f'Please provide the missing information and choose the next logically best state from the given options in the one-line JSON format such as {{{", ".join(prompt_parts)}}}: '

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
        vars['__state__'] = user['NEXT_STATE']


macros = {
    'GET_PROBLEM_RESPONSE':MacroGPTJSONNLG(
        generate_prompt,
        {'PROBLEM_SUMMARY': 'Stress at work', 'PROBLEM_DETAILS': 'I have too many tasks to handle',
         'USER_SOLUTIONS': {'Delegation': False, 'Time management': True}, 'NEXT_STATE': 'user_understanding_of_prob'},
        {'PROBLEM_SUMMARY': 'n/a', 'PROBLEM_DETAILS': 'n/a', 'USER_SOLUTIONS': {}, 'NEXT_STATE': 'other'},
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