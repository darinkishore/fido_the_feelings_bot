"""
Darin Kishore, dakisho
This code was my own Work. It was written without consulting
sources outside of those provided by the instructor.
"""

__author__ = "Darin Kishore"

from random import shuffle
from PyMovieDb import IMDB
import json

from emora_stdm import DialogueFlow
import spacy

import re
from emora_stdm import Macro, Ngrams
from typing import Dict, Any, List

# instructions for use: (PLEASE FOLLOW THIS OR IT WILL NOT WORK!)
# pip install emora_stdm
# pip install PyMovieDb
# pip install json
# pip install spacy
# run "python -m spacy download en_core_web_trf" in the current directory
# pip install markupsafe==2.0.1


# Create a chatbot that asks the user their name,
nlp = spacy.load("en_core_web_trf")

# ontology just defines category
# action - shawshank, godfather, etc..
#
# code executes left to right

# use regex to change the name so it's properly formatted.

transitions = {
    "state": "start",
    "`Hey. Gimme your name.`": {
        "#GET_NAME": {
            "`It's nice to meet you,`$NAME`. We\'re gonna talk about Babel today. Understood?`": {
                "[{yes, yeah, sure, definitely, absolutely, of course, yep, yea}]": {
                    'state': 'discussion'
                    "`Glad we\'re on the same page, chief. You like the movie?`"

                },
                "[{no favorite, have one, not have, have, dont know, not sure, not really, no, not really, nah}]": {
                    "`Not a problem. I can help you find one. What genre do you like?`": {
                        "$GENRE={action, adventure, animation, biography, comedy, crime, documentary, drama, dramatic, family, fantasy, film-noir, history, horror, music, musical, mystery, romance, sci-fi, sport, thriller, war, western}": {
                            "#TOP_TEN_MOVIES_NO_QUESTIONS`Here are my favorites! Come back when you've watched them all--maybe you'll have a favorite! `$TOP_TEN": "end"
                        },
                        "[{no idea, not sure, confused, not really}]": {
                            "#GET_RANDOM_GENRE#TOP_TEN_MOVIES_NO_QUESTIONS`That's okay! My favorite genre is $GENRE. I really recommend you"
                            "check out these movies. They're my top ten!`$TOP_TEN": "end"
                        },
                        "error": {
                            "`Go figure it out yourself!!!!! I'm not your mom!`": "end"
                        },
                    },
                },
                "error": {
                    "`I'm not sure I've seen that one. What's it about?`": {
                        "#UNX #GET_RANDOM_GENRE #TOP_TEN_MOVIES_NO_QUESTIONS": {
                            "`I'll have to check it out. I'm a big fan of`$GENRE`movies. Personal top ten--`$TOP_TEN`\n"
                            "Are you a fan of any of these?`": {
                                "[{not a fan, hate, dislike, bad, terrible, awful, horrible, terrible, negative, never liked, no, not really, nah}]": {
                                    "`No worries. You can always check out my top ten list. It's pretty good.`": "end"
                                },
                                "[{yes, yeah, sure, definitely, absolutely, of course, yep, yea}]": {
                                    "`Seems like we have a lot in common. Are you single?`": {
                                        "[{yes, yeah, sure, definitely, absolutely, of course, yep, yea, i guess}]": {
                                            "`I'm single too. Wanna go on a date?`": {
                                                "[{yes, yeah, sure, definitely, absolutely, of course, yep, yea, love to, love, yes please}]": {
                                                    "`Great! Let's go to the movies!`": "end"
                                                },
                                                "[{no, nope, nah, not really, not, not at all, hate, no thanks,}]": {
                                                    "`Oh. Well, I'm still single if you change your mind.`": "end"
                                                },
                                                "error": {
                                                    "`Let's just be friends then.`": "end"
                                                },
                                            }
                                        },
                                        "[{no, nope, nah, not really, not, not at all}]": {
                                            "`Oh. Well, I'm still single if you change your mind.`": "end"
                                        },
                                        "error": {
                                            "`THIS NEVER HAPPENED. I'M SORRY. ERROR>ERROR>ERROR>ERROR>...`": "end"
                                        },
                                    }
                                },
                                "error": {
                                    "`God. I'm so sorry. I'm just a bot. I don't know what to say. I'm sorry. I'm sorry. I'm sorry.`": "end"
                                },
                                "#UNX": {"`I get that. Peace!`": "end"},
                            }
                        }
                    }
                },
            }
        }
    },
}


# #SET($MOVIE=shawshank redemption)
# after you do ontology, dont set it in transition where oyu get it -- stick it in front of I like movie too!

movie_genres = {
    "The Shawshank Redemption": "dramatic",
    "The Godfather": "crime",
    "The Dark Knight": "action",
    "The Godfather: Part II": "crime",
    "The Godfather: Part III": "crime",
    "Pulp Fiction": "crime",
    "Schindler's List": "dramatic",
    "Zootopia": "animated",
    "Raiders of the Lost Ark": "action",
    "Ex Machina": "sci-fi",
    "Blade Runner": "sci-fi",
    "Blade Runner 2049": "sci-fi",
}

movie_characters = {
    "The Shawshank Redemption": "Andy Dufresne",
    "The Godfather": "Michael Corleone",
    "The Dark Knight": "The Joker",
    "The Godfather: Part II": "Michael Corleone",
    "The Godfather: Part III": "Michael Corleone",
    "Pulp Fiction": "Jules Winnfield",
    "Schindler's List": "Oskar Schindler",
    "Zootopia": "Judy Hopps",
    "Raiders of the Lost Ark": "Indiana Jones",
    "Ex Machina": "Ava",
    "Blade Runner": "Rick Deckard",
    "Blade Runner 2049": "Officer K",
}


class MacroTopTenNoQuestions(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        if vars["GENRE"]:
            genre = vars["GENRE"]
        else:
            genre = ngrams.raw_text()
        imdb = IMDB()
        movies = ""
        res = json.loads(imdb.popular_movies(genre=genre, sort_by="num_votes,desc"))
        if not res:
            return False
        for i in range(10):
            if i == 5:
                movies = movies + "\n"
            elif i != 9:
                movies = movies + f"{res['results'][i]['name']}, "
            else:
                movies = movies + f" and {res['results'][i]['name']}."
        vars["TOP_TEN"] = movies
        return True

        # call imdb api to get top 10 movies of genre


class MacroGetTopTenMoviesOfGenre(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        genre = vars["GENRE"]
        imdb = IMDB()
        movies = ""
        res = json.loads(imdb.popular_movies(genre=genre, sort_by="num_votes,desc"))
        if not res:
            return False
        for i in range(10):
            movies = movies + f"{res['results'][i]['name']}? "
            if i == 5:
                movies = movies + "\n"
        vars["TOP_TEN"] = movies
        return True

        # call imdb api to get top 10 movies of genre


class MacroGetRandomGenre(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        choices = list(movie_genres.values())
        shuffle(choices)
        genre = choices[0]
        vars["GENRE"] = genre
        return True


class MacroGetCharacter(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        movie = vars["MOVIE"]
        character = movie_characters[movie]
        vars["CHARACTER"] = character
        return True


class MacroGetGenre(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        movie = vars["MOVIE"]
        genre = movie_genres[movie]
        vars["GENRE"] = genre
        return True


class MacroGetName(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        doc = nlp(ngrams.raw_text())
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                text = ent.text
                # regex to capitalize first letter of each word
                text = re.sub(r"\b[a-z]", lambda m: m.group(0).upper(), text)
                vars["NAME"] = text
                return True
        vars["NAME"] = "G"
        return True


macros = {
    "GET_NAME": MacroGetName(),
    "GET_GENRE": MacroGetGenre(),
    "GET_CHARACTER": MacroGetCharacter(),
    "GET_RANDOM_GENRE": MacroGetRandomGenre(),
    "TOP_TEN_MOVIES": MacroGetTopTenMoviesOfGenre(),
    "TOP_TEN_MOVIES_NO_QUESTIONS": MacroTopTenNoQuestions(),
}

# train by asking chatgpt for examplews of named entities with name

df = DialogueFlow("start", end_state="end")
df.load_transitions(transitions)
df.load_transitions(transitions_char)
df.knowledge_base().load_json_file("../../resources/ontology_quiz3.json")
df.add_macros(macros)

if __name__ == "__main__":
    df.run()
