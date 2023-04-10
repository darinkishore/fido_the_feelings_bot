import random

from emora_stdm import DialogueFlow
import macros
import spacy
import time
import requests
import json
import os
import sqlite3
import openai
from re import Pattern
from utils import MacroGPTJSON, MacroNLG, MacroGPTJSONNLG, gpt_completion
from macros import macros

import re
from emora_stdm import Macro, Ngrams
from typing import Dict, Any, List
from enum import Enum

PATH_API_KEY = '../resources/openai_api.txt'


def api_key(filepath=PATH_API_KEY) -> str:
    fin = open(filepath)
    return fin.readline().strip()


openai.api_key = api_key()




introduction = {
    'state': 'start',
    '`Hi! I\'m Fido. What\'s your name?`': {
        '#SET_CALL_NAME': {
            '`It\'s nice to meet you,`#GET_CALL_NAME`! What\'s the main problem you\'re facing right now?`': 'pretreatment_base'
        }
    }
}

# precontemplation, contemplation, and preparation

pretreatment = {
    'state': 'pretreatment_base',
    # what's the problem -- why now have you called?
    '`#GET_PROBLEM_RESPONSE`': {
        '#GET_FILLER_ACKNOWLEDGEMENT`': {
            # random filler text response
        }
    },

    # how do you see or understand the situation?
    'state': 'get_details_about_prob',
    '`How do you see or understand the situation?`': {
        '#GET_PROBLEM_RESPONSE': {
            # random filler text response
        }
    },

    # What do you think will help?
    'state': 'what_will_help',
    '`What do you think will help?`': {
        '#GET_PROBLEM_RESPONSE': {
            # random filler text response
        }
    },

    # How have you tried to solve the problem so far -- how did it work?
    'state': 'attempts_to_solve',
    '`How have you tried to solve the problem so far, and how did it work?`': {
        '#GET_PROBLEM_RESPONSE': {
            # random filler text response
        }
    },

    # When the problem isn’t present (or isn’t bad), what is going on differently?
    'state': 'when_problem_not_present',
    '`When the problem isn’t present (or isn’t bad), what is going on differently?`': {
        '#GET_PROBLEM_RESPONSE': {
                # random filler text response
        }
    },

    'state': 'pretreatment_summary',
    '`It sounds like $SUMMARY. Is that right?`': {
        '[{yes, yeah, correct, right, yuh, yep, yeap, yup}]' : {
            '`Great! Let\'s move on to the next step.`': 'early_in_treatment_base'
        },
        '[{no, nope, not really, not at all, nah, incorrect, not correct, not right}]': {
            '`No worries! Can you please tell me what I didn\'t get right, and what I should have understood?`': {
                '#GET_PROBLEM_RESPONSE': {},
            }
        },
        'error': {
            '`Sorry, I didn\'t get that. Can you please tell me what I didn\'t get right, and what I should have understood?`': {
                '#GET_PROBLEM_RESPONSE': {},
            }
        }
    }
}

# IF ALL INFORMATION IS GATHERED, PRESENT A SUMMARY OF THE INFORMATION.
# THEN GO TO EARLY IN TREATMENT.

# action, maintenance, and termination

# questions to ask:
# when and how does the problem influence you; and when do you influence it
# what's your idea or theory about what wil help?
# what are some potential roadblocks or challenges that you anticipate in addressing this issue?
# what are some small steps you can take to address this issue?

early_in_treatment = {
    'state': 'early_in_treatment_base', # See what the main issue is in terms of how the user has tried to tackle the problem
    '`What are some blockers or challenges that you anticipate in addressing this issue?`': {
        '#GET_PROBLEM_RESPONSE': {
        }
    },

    'state': 'early_in_treatment_influence', # See how the problem influences the user and how the user influences the problem
    '`When and how does the problem influence you; and when do you influence it?`': {
        '#GET_PROBLEM_RESPONSE': {
        }
    },

    'state': 'early_in_treatment_idea', # See what the user's idea or theory about what will help is in terms of tackling these issues
    '`What\'s your ideas or theories about what wil help?`': {
        '#GET_PROBLEM_RESPONSE': {
        }
    },

    'state': 'early_in_treatment_small_steps', # See what small steps the user can take to address the issue so they can gain some confidence
    '`What are some small steps you can take to address this issue?`': {
        '#GET_PROBLEM_RESPONSE': {
        }
    }
}

macros['GET_PROBLEM_RESPONSE'] = MacroGPTJSONNLG(
        generate_prompt,
        {'PROBLEM_SUMMARY': 'Stress at work', 'PROBLEM_DETAILS': 'I have too many tasks to handle',
         'USER_SOLUTIONS': {'Delegation': False, 'Time management': True}, 'NEXT_STATE': 'user_understanding_of_prob'},
        {'PROBLEM_SUMMARY': 'n/a', 'PROBLEM_DETAILS': 'n/a', 'USER_SOLUTIONS': {}, 'NEXT_STATE': 'other'},
        set_problem_response
    )


df = DialogueFlow('start', end_state='end')
df.load_transitions(introduction)
df.load_transitions(pretreatment)
df.add_macros(macros)

if __name__ == '__main__':
    df.run()
