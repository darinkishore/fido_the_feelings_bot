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
    '`How do you see or understand the situation?`': {
        '#GET_PROBLEM_RESPONSE': {
            '#FILLER_RESPONSE`details_abt_prob`': {
                'state': 'what_will_help',
                '`What do you think will help?`': {
                    '#GET_PROBLEM_RESPONSE': {
                        '#FILLER_RESPONSE`what_will_help`': {
                            'state': 'finding_solutions',
                            '`How have you tried to solve the problem so far, and how did it work?`': {
                                '#GET_PROBLEM_RESPONSE': {
                                    '#FILLER_RESPONSE`attempts_to_solve`': {
                                        'state': 'when_problem_not_present',
                                        '`When the problem isn’t present (or isn’t bad), what is going on differently?`': {
                                            '#GET_PROBLEM_RESPONSE': {
                                                '#FILLER_RESPONSE`when_prob_not_present`': {
                                                    'state': 'summarize_reiterate_problem',
                                                    '#GET_SUMMARY`It sounds like $SUMMARY. Is that right?`': {
                                                        '[{yes, yeah, correct, right, yuh, yep, yeap, yup}]': {
                                                            '`Great! Let\'s move on to the next step.`': 'early_in_treatment_base'
                                                        },
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
                    }
                },

            }
        },
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
    '`What are some blockers or challenges that you anticipate in addressing this issue?`': {
        '#GET_PROBLEM_RESPONSE': {
            '#TOUGH_RESPONSE': {},
            # I feel like that this is okay to leave here, in general it should be a good response for most issues that the user is facing.
        }
        # for tough responses, respond in the dialog flow and then let gpt handle states, but make sure the response is tailored to the user.
        # maybe a macro #GET_GPT_AWKNOWLEDGEMENT that, when mixed with #GET_FILLER_TEXT, will make sure we're not docked points for just straight copying gpt responses.
    },

    'state': 'early_in_treatment_influence',
    # See how the problem influences the user and how the user influences the problem
    '`When and how does the problem influence you; and when do you influence it?`': {
        '#GET_PROBLEM_RESPONSE': {
            '#FILLER_RESPONSE`early_in_treatment_influence': {
            }
        }
    },

    'state': 'early_in_treatment_idea',
    # See what the user's idea or theory about what will help is in terms of tackling these issues
    '`What\'s your ideas or theories about what wil help?`': {
        '#GET_PROBLEM_RESPONSE': {
            '#FILLER_RESPONSE`early_in_treatment_idea`': {
            }
        }
    },

    'state': 'early_in_treatment_small_steps',
    # See what small steps the user can take to address the issue so they can gain some confidence
    '`What are some small steps you can take to address this issue?`': {
        '#GET_PROBLEM_RESPONSE': {
            '#FILLER_RESPONSE`early_in_treatment_small_steps`': {
            }
        }
    },
    'state': 'pretreatment_summary',
    '`It sounds like $SUMMARY. With the information provided, do you feel confident in how to address your issue?`': {
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
df.add_macros(macros)

if __name__ == '__main__':
    df.run(debugging=False)
