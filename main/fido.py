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

import re
from emora_stdm import Macro, Ngrams
from typing import Dict, Any, List

PATH_API_KEY = '../resources/openai_api.txt'


def api_key(filepath=PATH_API_KEY) -> str:
    fin = open(filepath)
    return fin.readline().strip()
openai.api_key = api_key()


"""
TODO:
- Get/store hometown and how they feel about it (good/bad), see if they like the place
- 
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

precontemplation = {
    'state': 'start',
    '`Hi! I\'m Fido. How are you feeling today?`': {
        '[{overwhelmed}]': {
            '`I\'m sorry to hear that. Can you tell me more about what\'s been making you feel overwhelmed?`': {
                '[{issues, boyfriend, distant}]': {
                    '`I see. That sounds like it could be difficult to deal with. Would you like to talk about it some more?`': {
                        '[{yes, please}]': {
                            '`Alright. It sounds like there might be some relationship issues going on. Is that correct?`': {
                                '[{yes}]': {
                                    '`Okay, thanks for confirming that. Before we move forward, I want to make sure that I understand the situation correctly. It sounds like you\'ve been feeling overwhelmed because your boyfriend has been distant and you\'re not sure why. Is that accurate?`': {
                                        '[{yes}]': {
                                            '`Thanks for letting me know. So, do you want advice on how to approach your boyfriend or do you just need someone to listen?`': {
                                                '[{advice}]': {
                                                    '`I would suggest trying to have an open and honest conversation with your boyfriend about your feelings and concerns. It\'s important to express your thoughts and give him a chance to share his perspective as well. Good luck!`': 'end'
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

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
#df.load_transitions(precontemplation)
df.load_transitions(introduction)
df.load_transitions(hobbies)
df.add_macros(macros)

if __name__ == '__main__':
    create_database()
    add_user("John")
    update_user("John", "New York", 1, "hiking")
    df.run()