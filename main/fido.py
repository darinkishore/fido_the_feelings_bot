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
            '`It\'s nice to meet you,`#GET_CALL_NAME`! What\'s the main problem you\'re facing right now?`': {
                '#GET_PROBLEM_RESPONSE': {
                    '#FILLER_RESPONSE': {
                    }
                }
            }
        }
    }
}

# pretreatment, early in treatment, late in treatment

pretreatment = {
    'state': 'user_understanding_of_prob',
    '#FILLER_RESPONSE `Tell me more about it.`': {
        '#GET_PROBLEM_RESPONSE': {
            'state': 'attempted_solutions',
            '#TOUGH_RESPONSE `How have you tried to solve the problem so far, and how did it work?`': {
                '#GET_PROBLEM_RESPONSE': {
                    'state': 'when_problem_not_present',
                    '#FILLER_RESPONSE `When the problem isn’t present (or isn’t bad), what is going on differently?`': {
                        '#GET_PROBLEM_RESPONSE': {
                            'state': 'summarize_reiterate_problem',
                            '`Thank you for sharing. `#GET_SUMMARY` Just want to make sure I understand.`': {
                                '[{yes, yeah, correct, right, yuh, yep, yeap, yup}]': 'early_in_treatment_base',

                                '[{no, nope, not really, not at all, nah, incorrect, not correct, not right}]': {
                                    '`No worries! Can you please tell me what I didn\'t get right, and what I should have understood?`': {
                                        '#GET_PROBLEM_RESPONSE': {}
                                    }
                                },
                                'error': {
                                    '`Sorry, I didn\'t get that. Can you please tell me what I didn\'t get right, and what I should have understood?`': {
                                        '#GET_PROBLEM_RESPONSE': {}
                                    }
                                }
                            }

                        }
                    }
                },
            }
        }
    },
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
    'state': 'early_in_treatment_base',
    # See what the main issue is in terms of how the user has tried to tackle the problem
    '`Great! Let\'s move on to the next step. What are some blockers or challenges that you anticipate in addressing this issue?`': {
        '#GET_EARLY_RESPONSE': {
            'state': 'how_problem_influences_user_vice_versa',
            # See how the problem influences the user and how the user influences the problem
            '#TOUGH_RESPONSE`When and how does the problem influence you; and when do you influence it?`': {
                '#GET_EARLY_RESPONSE': {
                    'state': 'get_user_ideas_on_what_will_help',
                    # See what the user's idea or theory about what will help is in terms of tackling these issues
                    '#FILLER_RESPONSE`What\'s your ideas or theories about what will help?`': {
                        '#GET_EARLY_RESPONSE': {
                            'state': 'early_in_treatment_summary',
                            '`Ok` #GET_SUGGESTION `I need to make sure before we move on.`': {
                                '[{yes, yeah, correct, right, yuh, yep, yeap, yup}]': {
                                    '`Great! Let\'s move on to the next step.`': 'post_treatment_base'
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
                    }
                }
            },
        }
    }
}

# I feel like that this is okay to leave here, in general it should be a good response for most issues that the user is facing.

# for tough responses, respond in the dialog flow and then let gpt handle states, but make sure the response is tailored to the user.
# maybe a macro #GET_GPT_AWKNOWLEDGEMENT that, when mixed with #GET_FILLER_TEXT, will make sure we're not docked points for just straight copying gpt responses.


# evaluation
post_treatment = {
    'state': 'post_treatment_base',
    '`Do you feel that today\'s session has made a positive impact on your situation?`': {
        '[{yes, yeah, correct, right, yuh, yep, yeap, yup}]': {
            '`Great! Let\'s move on to the next step.`': 'post_treatment_secondary'
        },
        '[{no, nope, not really, not at all, nah, incorrect, not correct, not right}]': {
            '`Can you explain why the session didn\'t positively impact your situation?`': {
                '#GET_PROBLEM_RESPONSE': {},
            }
        },
        'error': {
            '`Sorry, I didn\'t get that. Can you please tell me what I didn\'t get right, and what I should have understood?`': {
                '#GET_PROBLEM_RESPONSE': {},
            }
        }
    },

    'state': 'post_treatment_secondary',
    '`Can you identify any specific methods or steps that you found particularly beneficial?`': {
        '#GET_PROBLEM_RESPONSE': 'post_treatment_tertiary'
    },

    'state': 'post_treatment_tertiary',
    '`How would you describe the effectiveness of this session?`': {
        '#GET_PROBLEM_RESPONSE': 'post_treatment_quaternary'
    },

    'state': 'post_treatment_quaternary',
    '`what are some areas that you felt like I fell short in?`': {
        '#GET_PROBLEM_RESPONSE': 'post_treatment_quinary'
        # maybe add a macro to store this specific response in a list of responses or a sqllite database
    },

}

# we gotta solo implement preparation/action stages, which is where the actual "therapizing" happens


df = DialogueFlow('start', end_state='end')
df.local_transitions(introduction)
df.local_transitions(pretreatment)
df.local_transitions(early_in_treatment)
df.add_macros(macros)

if __name__ == '__main__':
    df.run(debugging=True)
