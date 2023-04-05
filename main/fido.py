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

import re
from emora_stdm import Macro, Ngrams
from typing import Dict, Any, List
from enum import Enum

PATH_API_KEY = '../resources/openai_api.txt'


def api_key(filepath=PATH_API_KEY) -> str:
    fin = open(filepath)
    return fin.readline().strip()


openai.api_key = api_key()

"""
TODO:
- Get/store hometown and how they feel about it (good/bad), see if they like the place - Eric
- Add roommate dialog branch -> Eric
- Add professor-relate didalog handling -> ezra
- Fix hobbies, add Friends dialog handling -> raphael
- add partner dialog handling -> Darin
- PLEASE get this done by Tuesday night. We need to have a working prototype by then.
"""


# User Management
def create_database():
    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    c.execute(
        """CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            hometown TEXT,
            likesHometown INTEGER,
            hobbies TEXT
        )"""
    )
    conn.commit()
    conn.close()


def add_user(name, hometown=None, likes_hometown=None, hobbies=None):
    conn = sqlite3.connect("data.db")
    c = conn.cursor()

    # Insert or update user
    c.execute(
        """INSERT OR IGNORE INTO users (name, hometown, likesHometown, Hobbies) VALUES (?, ?, ?, ?)""",
        (name, hometown, likes_hometown, hobbies),
    )
    conn.commit()

    # Get the user id for the inserted or existing user
    c.execute("""SELECT id FROM users WHERE name = ?""", (name,))
    user_id = c.fetchone()[0]

    conn.close()
    return user_id


def update_user(name, hometown=None, likes_hometown=None, hobbies=None):
    conn = sqlite3.connect("data.db")
    c = conn.cursor()

    if hometown is not None:
        c.execute("""UPDATE users SET hometown = ? WHERE name = ?""", (hometown, name))

    if likes_hometown is not None:
        c.execute("""UPDATE users SET likesHometown = ? WHERE name = ?""", (likes_hometown, name))

    if hobbies is not None:
        c.execute("""UPDATE users SET Hobbies = ? WHERE name = ?""", (hobbies, name))

    conn.commit()
    conn.close()


class User(Enum):
    call_name = 0
    hometown = 1
    likes_hometown = 2
    hometown_good = 3
    hobbies = 4


introduction = {
    'state': 'start',
    '`Hi! I\'m Fido. What\'s your name?`': {
        '#SET_CALL_NAME': {
            '`It\'s nice to meet you` #GET_CALL_NAME `. Do you want to hear a fun fact?`': {
                '[{yes, yeah, sure, ok, yea, why not}]': {
                    '#SET_FUN_FACT`Ok here\'s one:` #GET_FUN_FACT `Isn\'t that cool!`': 'hobbies'
                },
                '[{no, nope, nah, no thanks, not really, not now, not today}]': {
                    '`Ok, maybe next time!`': 'end'
                },
                'error': {
                    '`Fuck you and your family.`': 'end'
                },
            }
        }
    }
}

# precontemplation, contemplation, and preparation


# df to get/store hobbies
# assume this comes after fun fact

hobbies = {
    'state': 'hobbies',
    '`What are some of the hobbies that you enjoy?`': {
        '#GET_HOBBY_STATEMENT': {  # to access hobby statement, use $HOBBY_STATEMENT
            "`Have you tried similar hobbies to `$HOBBY`? I can suggest some if you\'d like.": {
                '[{yes, yeah, interested, suggested}]': {
                    '# SIMILAR_HOBBY `align with` $HOBBY `and your interests. Does this recommendation line up with your wants?`' : {
                    },
                        '[{yes, yeah, interested, suggested}]': {
                            'Perfect! I\'m glad that I was able to recommend you a new hobby that you\'d like to try': 'end'

                    }
                },
                '[{no, nope, nah, no thanks, not really, not now, not today}]':{
                    '`Ok, maybe next time!`': 'end'
                },
                'error': {
                    'Sorry, I didn\'t quite get that. Could you repeat that?': 'hobbies'
                },
            }
        }
    }
}

hometown = {
    'state': 'hometown',
    '`Where are you from originally?`': {
        '#GET_HOMETOWN_NAME': {
            '`Oh, I\'ve heard of that place. How has` $HOMETOWN `treated you?`': {
                '#GET_LIKES_HOMETOWN': {
                    '#IF($NO_HOMETOWN_PROBLEM = True)': {
                        '`That\'s great! Glad to hear you enjoy where you\'re from! Now, let\' talk about Emory`': 'professors'
                    },
                    '`I\'m sorry to hear that! I hope Emory\'s campus & community have treated you much better!`': 'professors'
                }
            }
        }
    }
}

professors = {
    'state': 'professors',
    '`Have you had any problems with professors recently? I know how annoying they can be.`': {
        '#GET_PROFESSOR_PROBLEM_ADVICE': {
            '#IF($NO_PROFESSOR_PROBLEM = True)': {
                '`Ok! Let me know if they ever give you any trouble. I know how tough they can be.`': 'end'
            },
            '`Wow I\'m sorry to hear that! Here\'s my advice:` $PROBLEM_STATEMENT `. Is that helpful?`': 'end'
        }

    }
}


def get_call_name(vars: Dict[str, Any]):
    ls = vars[User.call_name.name]
    return ls


def get_fun_fact(vars: Dict[str, Any]):
    return vars['FUN_FACT']


def get_hobby(vars: Dict[str, Any]):
    return vars['HOBBY']


def why_like_hobby(vars: Dict[str, Any]):
    return vars['WHY_LIKE_HOBBY']


def set_call_names(vars: Dict[str, Any], user: Dict[str, Any]):
    vars[User.call_name.name] = user[User.call_name.name]
    add_user(vars[User.call_name.name])


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
        hobby = random.choice(problem)
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
    similar_hobby = vars['SIMILAR_HOBBY']


macros = {
    'SET_CALL_NAME': MacroGPTJSON(
        'How does the speaker want to be called? Respond in the one-line JSON format such as {"call_names": ["Mike", "Michael"]}: ',
        {User.call_name.name: ["Mike", "Michael"]},
        {User.call_name.name: "n/a"},
        set_call_names
    ),
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
        {'Hobbies': ["workload", "communication"]},
        {'Hobbies': "n/a"},
        set_professor_problem,
    ),
    'GET_CALL_NAME': MacroNLG(get_call_name),
    'GET_FUN_FACT': MacroNLG(get_fun_fact),
    'GET_USER_HOBBY': MacroNLG(get_hobby),
    'GET_PROFESSOR_PROBLEM': MacroNLG(get_professor_problem)
}

df = DialogueFlow('start', end_state='end')
df.load_transitions(introduction)
df.load_transitions(hobbies)
df.add_macros(macros)

if __name__ == '__main__':
    create_database()
    add_user("John")
    update_user("John", "New York", 1, "hiking")
    df.run()
