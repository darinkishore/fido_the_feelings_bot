import random

from emora_stdm import DialogueFlow
import macros
import spacy
import time
import requests
import json
import os
import sqlite3
import utils

import re
from emora_stdm import Macro, Ngrams
from typing import Dict, Any, List

# User Management
def create_database():
    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    c.execute(
        """CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE, visits INT)"""
    )
    c.execute(
        """CREATE TABLE IF NOT EXISTS movie_recommendations (id INTEGER PRIMARY KEY, user_id INTEGER, movie TEXT, seen INTEGER, reccomended INTEGER, FOREIGN KEY(user_id) REFERENCES users(id))"""
    )
    c.execute(
        """CREATE TABLE IF NOT EXISTS song_recommendations (id INTEGER PRIMARY KEY, user_id INTEGER, song TEXT, artist TEXT, listened INTEGER, reccomended INTEGER, FOREIGN KEY(user_id) REFERENCES users(id))"""
    )
    # make a table that tracks if a user is happy or sad
    c.execute(
        """CREATE TABLE IF NOT EXISTS mood (id INTEGER PRIMARY KEY, user_id INTEGER, mood TEXT, FOREIGN KEY(user_id) REFERENCES users(id))"""
    )
    conn.commit()
    conn.close()

def add_user(name):
    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    # get ID of user

    c.execute("""INSERT OR IGNORE INTO users (name, visits) VALUES (?, ?)""", (name, 1))
    conn.commit()

    # Get the user id for the inserted or existing user
    c.execute("""SELECT id FROM users WHERE name = ?""", (name,))
    user_id = c.fetchone()[0]

    # Add initial movie and song recommendations for the user (modify the recommendations as needed)
    initial_movie_recommendations = [
        ("Forrest Gump", 0),
        ("Parasite", 0),
        ("The Joker", 0),
    ]
    initial_song_recommendations = [
        ("Long Time", "Playboi Carti", 0),
        ("6-Foot/7-Foot", "Lil Wayne", 0),
        ("The Box", "Roddy Ricch", 0),
    ]

    random.shuffle(initial_movie_recommendations)
    random.shuffle(initial_song_recommendations)

    # Insert movie recommendations
    for movie, seen in initial_movie_recommendations:
        c.execute(
            """INSERT OR IGNORE INTO movie_recommendations (user_id, movie, seen, reccomended) VALUES (?, ?, ?, ?)""",
            (user_id, movie, seen, seen),
        )

    # Insert song recommendations
    for song, artist, listened in initial_song_recommendations:
        c.execute(
            """INSERT OR IGNORE INTO song_recommendations (user_id, song, artist, listened, reccomended) VALUES (?, ?, ?, ?, ?)""",
            (user_id, song, artist, listened, listened),
        )

    conn.commit()
    conn.close()

def update_user_visits(name):
    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    c.execute("""UPDATE users SET visits = visits + 1 WHERE name = ?""", (name,))
    conn.commit()
    conn.close()

def is_returning_user(name):
    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    c.execute("""SELECT visits FROM users WHERE name = ?""", (name,))
    visits = c.fetchone()
    conn.close()
    return visits is not None



# precontemplation, contemplation, and preparation

# Goals: expand on the feeling stages.
# Add error states for precontempation. Dont give a fuck, etc...
# Add and implement a get advice macro.

# future:
# implement state to gather info about student's life right now. natural conversation.
#      Age, gender, classes?, work?, family?, friends?, etc...
# store the information about them

# figure out how to use GPT. get emotions from it.

# key:
# design an introductory conversation to get the user's name and age, and what they're doing in college.
# - can store it in the natek variable format ($NAME = ..)
# - make a get_name macro, use it to get name
# - make a get_age macro, use it to get age

# get emotion/sentiment macro (Good, bad, neutral) from the user's input.
# design conversation to understand the user's primary relationships/conflicts (ie: who they engage with in their lives.)
# start with conflicts. " have u been feeling like u rlly wanna fight anyone lately?"
# - ask about the following people: friends, family, significant other, professors, classmates, etc...
# store data in DB.

# store all that shit

precontemplation = {
    'state': 'start',
    '`Hello, I\'m Fido! How are you today?`': {
        '{good, great, fine, not bad}': {
            '`That\'s great to hear! Is there something specific you\'d like to talk about or just have a casual chat?`': 'casual_chat'
        },
        '{bad, not good, terrible, sad, unhappy}': {
            '`I\'m sorry to hear that. Would you like to talk about what\'s bothering you or just have a casual chat to take your mind off things?`': 'casual_chat'
        },
        'error': {
            '`No worries. If you ever want to talk or need someone to listen, I\'m here for you. Let\'s have a casual chat!`': 'casual_chat'
        }
    },
    'state': 'casual_chat',
    '`Alright! What would you like to chat about? We could talk about hobbies, movies, music, or something else you\'re interested in.`': {
        '{hobbies, interests, activities}': {
            '`What are some of your favorite hobbies or interests?`': 'casual_chat_response'
        },
        '{movies, films, cinema}': {
            '`What kind of movies do you enjoy? Any favorite genres or films?`': 'casual_chat_response'
        },
        '{music, songs, bands, artists}': {
            '`What type of music do you like? Any favorite artists or songs?`': 'casual_chat_response'
        },
        'error': {
            '`It\'s alright if you\'re not sure. If you ever want to chat or need someone to listen, feel free to reach out to me. Have a great day!`': 'end'
        }
    },
    'state': 'casual_chat_response',
    '`That sounds interesting! I always enjoy learning about new things. If you ever want to talk about your experiences or issues, feel free to reach out to me anytime. Have a great day!`': 'end'
}


macros = {
    'GPTJSON': utils.MacroGPTJSON(),
}

df = DialogueFlow('start', end_state='end')
df.load_transitions(precontemplation)
df.add_macros(macros)

if __name__ == '__main__':
    df.run()