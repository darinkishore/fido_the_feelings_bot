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


# scope refinement: fido will help you solve an emotional problem.

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


early_available_states = ['user_emotional_state',  'user_support_system',
                           'user_finds_anticipated_challenges', 'how_problem_influences_user_vice_versa',
                          'get_user_ideas_on_what_will_help', 'early_in_treatment_summary']

early_vars = ['EMOTIONAL_STATE',  'SUPPORT_SYSTEM',
               'FINDS_ANTICIPATED_CHALLENGES', 'HOW_PROBLEM_INFLUENCES_USER_VICE_VERSA',
              'USER_IDEAS_ON_WHAT_WILL_HELP', 'GOALS_FROM_THERAPY']


def generate_prompt_early(vars: Dict[str, Any]):
    prompt_parts = []
    for var in early_vars:
        if var not in vars:
            prompt_parts.append(f'"{var}": "example_value_for_{var.lower()}"')

    prompt_parts.append(f'"NEXT_STATE": {"{" + ", ".join(f"{state}" for state in early_available_states) + "}"}')

    prompt = f'Please provide the missing information and choose the next logically best state from the given options. You may ONLY choose from the given options. Do not output ANY STATE NOT LISTED.' \
             f'If early_in_treatment_summary is the only option in the list, pick it no matter what. IF ALL INFORMATION IS NOT COLLECTED, UNDER NO CIRCUMSTANCES SHOULD YOU GO TO THE SUMMARY STATE.' \
             f'Respond in the one-line JSON format such as {{{", ".join(prompt_parts)}}}: '

    return prompt

def set_early_response(vars: Dict[str, Any], user: Dict[str, Any]):
    for state in early_vars:
        user_value = user.get(state.upper())
        if user_value != 'n/a':
            vars_value = vars.get(state.upper())
            if vars_value and vars_value != user_value:
                vars[state.upper()] = f"{vars_value}, {user_value}"
            else:
                vars[state.upper()] = user_value

    if 'NEXT_STATE' in user:
        if user['NEXT_STATE'] in early_available_states:
            if user['NEXT_STATE'] != 'early_in_treatment_summary':
                early_available_states.remove(user['NEXT_STATE'])
        vars['__target__'] = f"{user['NEXT_STATE']}"



available_states_pre = ['user_understanding_of_prob', 'attempted_solutions', 'when_problem_not_present',
                        'summarize_reiterate_problem']


def generate_prompt_pre(vars: Dict[str, Any]):
    prompt_parts = []
    if 'PROBLEM_SUMMARY' not in vars:
        prompt_parts.append('"PROBLEM_SUMMARY": "trouble at work"')
    if 'PROBLEM_DETAILS' not in vars:
        prompt_parts.append(
            '"PROBLEM_DETAILS": "Having trouble at work due to not being able to manage time, boss does not like them, eats too much"')
    if 'USER_SOLUTIONS' not in vars:
        prompt_parts.append(
            '"USER_SOLUTIONS": "tried to eat less, tried to delegate work, tried to manage time better, tried to communicate"')

    prompt_parts.append(f'"NEXT_STATE": {"{" + ", ".join(f"{state}" for state in available_states_pre) + "}"}')

    prompt = f'Please provide the missing information and choose only ONE next logically best state from the given options. You may ONLY choose from the given options. If no state seems best,' \
             f'summarize and reiterate the problem. IF ALL INFORMATION IS NOT COLLECTED, UNDER NO CIRCUMSTANCES SHOULD YOU GO TO THE SUMMARY STATE.' \
             f'Respond in the one-line JSON format such as {{{", ".join(prompt_parts)}}}: '

    return prompt


# Set problem response variables and the next state
def set_problem_response(vars: Dict[str, Any], user: Dict[str, Any]):
    user_problem_summary = user.get('PROBLEM_SUMMARY')
    if user_problem_summary != 'n/a':
        vars_problem_summary = vars.get('PROBLEM_SUMMARY')
        if vars_problem_summary and vars_problem_summary != user_problem_summary:
            vars['PROBLEM_SUMMARY'] = f"{vars_problem_summary}, {user_problem_summary}"
        else:
            vars['PROBLEM_SUMMARY'] = user_problem_summary

    user_problem_details = user.get('PROBLEM_DETAILS')
    if user_problem_details != 'n/a':
        vars_problem_details = vars.get('PROBLEM_DETAILS')
        if vars_problem_details and vars_problem_details != user_problem_details:
            vars['PROBLEM_DETAILS'] = f"{vars_problem_details}, {user_problem_details}"
        else:
            vars['PROBLEM_DETAILS'] = user_problem_details

    user_solutions = user.get('USER_SOLUTIONS')
    if user_solutions != 'n/a':
        vars_user_solutions = vars.get('USER_SOLUTIONS')
        if vars_user_solutions and vars_user_solutions != user_solutions:
            vars['USER_SOLUTIONS'] = f"{vars_user_solutions}, {user_solutions}"
        else:
            vars['USER_SOLUTIONS'] = user_solutions

    if 'NEXT_STATE' in user:
        if user['NEXT_STATE'] in available_states_pre:
            if user['NEXT_STATE'] != 'summarize_reiterate_problem':
                available_states_pre.remove(user['NEXT_STATE'])
        vars['__target__'] = f"{user['NEXT_STATE']}"


macros = {
    'GET_PROBLEM_RESPONSE': MacroGPTJSONNLG(
        generate_prompt_pre,
        {'PROBLEM_SUMMARY': 'issues at work',
         'PROBLEM_DETAILS': 'Having trouble at work due to not being able to manage time, boss does not like them, eats too much',
         'USER_SOLUTIONS': 'ate less, delegated work, managed time better',
         'NEXT_STATE': '...'},
        {'PROBLEM_SUMMARY': 'n/a', 'PROBLEM_DETAILS': 'n/a', 'USER_SOLUTIONS': 'n/a',
         'NEXT_STATE': '...'},
        set_problem_response
    ),
    'GET_EARLY_RESPONSE': MacroGPTJSONNLG(
        generate_prompt_early,
        {'EMOTIONAL_STATE': 'happy', 'SUPPORT_SYSTEM': 'family',
               'FINDS_ANTICIPATED_CHALLENGES': 'lack motivation', 'HOW_PROBLEM_INFLUENCES_USER_VICE_VERSA': 'ruining home life',
              'USER_IDEAS_ON_WHAT_WILL_HELP': 'dividing workload', 'GOALS_FROM_THERAPY': 'learn time management strategies, improve skills, feel better, overcome adversity',
         'NEXT_STATE': '...'},
        {'EMOTIONAL_STATE': 'n/a', 'SUPPORT_SYSTEM': 'n/a/',
               'FINDS_ANTICIPATED_CHALLENGES': 'n/a', 'HOW_PROBLEM_INFLUENCES_USER_VICE_VERSA': 'n/a',
              'USER_IDEAS_ON_WHAT_WILL_HELP': 'n/a', 'GOALS_FROM_THERAPY': 'n/a',
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