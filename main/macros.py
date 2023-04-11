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
    MacroMakeSummary, MacroMakeSuggestions


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



def generate_prompt_early(vars: Dict[str, Any]):
    prompt_parts = []
    if 'PROBLEM_CHALLENGE' not in vars:
        prompt_parts.append('"PROBLEM_CHALLENGE": "having the courage, the consequences, its difficult"')
    if 'PROBLEM_INFLUENCE' not in vars:
        prompt_parts.append('"PROBLEM_INFLUENCE": "ruins my life, makes me angry, at night, all the time"')
    if 'PROBLEM_IDEA' not in vars:
        prompt_parts.append(
            '"PROBLEM_IDEA": "could eat better, could manage my time better, could communicate better, get help"')


    prompt_parts.append(f'"NEXT_STATE": {"{" + ", ".join(f"{state}" for state in early_available_states) + "}"}')

    prompt = f'Please provide the missing information and choose the next logically best state from the given options. You may ONLY choose from the given options. If no state seems best,' \
             f'provide a summary. IF ALL INFORMATION IS NOT COLLECTED, UNDER NO CIRCUMSTANCES SHOULD YOU GO TO THE SUMMARY STATE.' \
             f'Respond in the one-line JSON format such as {{{", ".join(prompt_parts)}}}: '

    return prompt

early_available_states = ['how_problem_influences_user_vice_versa', 'get_user_ideas_on_what_will_help',
                           'early_in_treatment_summary']

def set_early_response(vars: Dict[str, Any], user: Dict[str, Any]):
    if user['PROBLEM_CHALLENGE'] != 'n/a':
        vars['PROBLEM_CHALLENGE'] = f"{vars['PROBLEM_CHALLENGE']}, {user['PROBLEM_CHALLENGE']}" if vars['PROBLEM_CHALLENGE'] != user['PROBLEM_CHALLENGE'] else vars['PROBLEM_CHALLENGE']
    if user['PROBLEM_INFLUENCE'] != 'n/a':
        vars['PROBLEM_INFLUENCE'] = f"{vars['PROBLEM_INFLUENCE']}, {user['PROBLEM_INFLUENCE']}" if vars['PROBLEM_INFLUENCE'] != user['PROBLEM_INFLUENCE'] else vars['PROBLEM_INFLUENCE']
    if user['PROBLEM_IDEA'] != 'n/a':
        vars['PROBLEM_IDEA'] = f"{vars['PROBLEM_IDEA']}, {user['PROBLEM_IDEA']}" if vars['PROBLEM_IDEA'] != user['PROBLEM_IDEA'] else vars['PROBLEM_IDEA']


    if 'NEXT_STATE' in user:
        if user['NEXT_STATE'] in early_available_states:
            early_available_states.remove(user['NEXT_STATE'])
        vars['__target__'] = f"{user['NEXT_STATE']}"

available_states_pre = ['user_understanding_of_prob',  'attempted_solutions', 'when_problem_not_present',
                    'summarize_reiterate_problem']

def generate_prompt_pre(vars: Dict[str, Any]):
    prompt_parts = []
    if 'PROBLEM_SUMMARY' not in vars:
        prompt_parts.append('"PROBLEM_SUMMARY": "trouble at work"')
    if 'PROBLEM_DETAILS' not in vars:
        prompt_parts.append('"PROBLEM_DETAILS": "Having trouble at work due to not being able to manage time, boss does not like them, eats too much"')
    if 'USER_SOLUTIONS' not in vars:
        prompt_parts.append('"USER_SOLUTIONS": "tried to eat less, tried to delegate work, tried to manage time better"')


    prompt_parts.append(f'"NEXT_STATE": {"{" + ", ".join(f"{state}" for state in available_states_pre) + "}"}')

    prompt = f'Please provide the missing information and choose the next logically best state from the given options. You may ONLY choose from the given options. If no state seems best,' \
             f'summarize and reiterate the problem. IF ALL INFORMATION IS NOT COLLECTED, UNDER NO CIRCUMSTANCES SHOULD YOU GO TO THE SUMMARY STATE.' \
             f'Respond in the one-line JSON format such as {{{", ".join(prompt_parts)}}}: '

    return prompt


# Set problem response variables and the next state
def set_problem_response(vars: Dict[str, Any], user: Dict[str, Any]):
    if user['PROBLEM_SUMMARY'] != 'n/a':
        vars['PROBLEM_SUMMARY'] = f"{vars['PROBLEM_SUMMARY']}, {user['PROBLEM_SUMMARY']}" if vars['PROBLEM SUMMARY'] and vars['PROBLEM_SUMMARY'] != user['PROBLEM_SUMMARY'] else vars['PROBLEM_SUMMARY']
    if user['PROBLEM_DETAILS'] != 'n/a':
        vars['PROBLEM_DETAILS'] = f"{vars['PROBLEM_DETAILS']}, {user['PROBLEM_DETAILS']}" if vars['PROBLEM_DETAILS'] and vars['PROBLEM_DETAILS'] != user['PROBLEM_DETAILS'] else vars['PROBLEM_DETAILS']
    if user['USER_SOLUTIONS'] != 'n/a':
        vars['USER_SOLUTIONS'] = f"{vars['USER_SOLUTIONS']}, {user['USER_SOLUTIONS']}" if vars['USER_SOLUTIONS'] and vars['USER_SOLUTIONS]'] != user['USER_SOLUTIONS'] else vars['USER_SOLUTIONS']

    if 'NEXT_STATE' in user:
        if user['NEXT_STATE'] in available_states_pre:
            if user['NEXT_STATE'] != 'summarize_reiterate_problem':
                available_states_pre.remove(user['NEXT_STATE'])
        vars['__target__'] = f"{user['NEXT_STATE']}"


macros = {
    'GET_PROBLEM_RESPONSE': MacroGPTJSONNLG(
        generate_prompt_pre,
        {'PROBLEM_SUMMARY': 'issues at work', 'PROBLEM_DETAILS': 'Having trouble at work due to not being able to manage time, boss does not like them, eats too much',
         'USER_SOLUTIONS': 'ate less, delegated work, managed time better',
         'NEXT_STATE': '...'},
        {'PROBLEM_SUMMARY': 'n/a', 'PROBLEM_DETAILS': 'n/a', 'USER_SOLUTIONS': 'n/a',
         'NEXT_STATE': '...'},
        set_problem_response
    ),
'GET_EARLY_RESPONSE': MacroGPTJSONNLG(
        generate_prompt_early,
        {'PROBLEM CHALLENGE': 'its hard', 'PROBLEM_INFLUENCE': 'hard to study in school', 'PROBLEM_IDEA': 'could eat less',
         'NEXT_STATE': '...'},
        {'PROBLEM_CHALLENGE': 'n/a', 'PROBLEM_INFLUENCE': 'n/a', 'PROBLEM_IDEA': 'n/a',
         'NEXT_STATE': '...'},
        set_early_response
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
    'GET_SUGGESTION': MacroMakeSuggestions(),
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
