import random

from emora_stdm import DialogueFlow
import macros
import spacy
import time
import requests
import json
import sqlite3

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


transitions = {
    'state': 'start',
    '`Hello, how can I help you?`': {
        # TODO: to be filled.
    }
}




df = DialogueFlow('start', end_state='end')
df.load_transitions(transitions)

if __name__ == '__main__':
    df.run()