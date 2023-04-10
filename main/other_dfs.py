hobbies = {
    'state': 'hobbies',
    '`What are some of the hobbies that you enjoy?`': {
        '#GET_HOBBY_STATEMENT': {  # to access hobby statement, use $HOBBY_STATEMENT
            "`Have you tried similar hobbies to `$HOBBY`? I can suggest some if you\'d like.": {
                '[{yes, yeah, interested, suggested}]': {
                    '# SIMILAR_HOBBY `align with` $HOBBY `and your interests. Does this recommendation line up with your wants?`': {
                    },
                    '[{yes, yeah, interested, suggested}]': {
                        'Perfect! I\'m glad that I was able to recommend you a new hobby that you\'d like to try': 'end'

                    }
                },
                '[{no, nope, nah, no thanks, not really, not now, not today}]': {
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
        'state': 'professor advice',
        '#GET_PROFESSOR_PROBLEM_ADVICE': {
            '#IF($NO_PROFESSOR_PROBLEM = True)': {
                '`Ok! Let me know if they ever give you any trouble. I know how tough they can be. Is there something else I can help with?`': 'end'
            },
            '`Wow I\'m sorry to hear that! Here\'s my advice:` $PROBLEM_STATEMENT `. Is that helpful?`': {
                '[{yes, yeah, thank, yep}]': {
                    '`Happy to help! Let me know if you need to talk more about it. I am always here to listen. Is there anything else you want to discuss?`': {
                        '[{yes, yeah, sure, yup, yep}]': {
                            '`Ok! What do you want to talk about?`': 'end'
                        },
                        'error': {
                            '`Alright! I\'ll be here if you need to talk again! Have a good day !`': 'end'
                        }
                    }
                },
                'error': {
                    '`Ok, I\'m sorry I wasn\'t more helpful. I can offer more advice. Would that be helpful?`': {
                        '[{yes, yeah, course, sure, yep}]': {
                            '`Great! Maybe give me some more details this time, I\'ll see if I can do better!`': 'professor advice'
                        },
                        'error': {
                            '`If something is really bothering you, try talking to a friend or administrator! I\'m sorry I couldn\'t help this time. Let me know if you need anything else!`': 'end'
                        }
                    }
                }
            }
        }

    }
}

partners = {
    'state': 'partners',
    '`How is your relationship with your partner?`': {
        '#GET_PARTNER_STATUS': {
            'good': {
                '`That\'s wonderful to hear! What do you think makes your relationship so strong?`': {
                    '#GET_STRONG_ATTRIBUTE': {
                        '`It\'s great that $STRONG_ATTRIBUTE plays a significant role in your relationship. Remember to keep nurturing your bond and supporting each other. Have a great day!`': 'end',
                    }
                }
            },
            'bad': {
                '`I\'m sorry to hear that your relationship is going through a tough time. Can you tell me more about the challenges you\'re facing?`': {
                    '#GET_CHALLENGE': {
                        '`It sounds like $CHALLENGE is causing some issues in your relationship. Here is some advice:` $PARTNER_ADVICE `I hope it helps, and remember, open communication and understanding are key to resolving conflicts. Take care!`': 'end',
                    }
                }
            },
            'complicated': {
                '`Relationships can be complicated sometimes. Can you tell me more about the aspects of your relationship that are causing confusion or mixed feelings?`': {
                    '#GET_CONFUSION': {
                        '`It seems like $CONFUSION is making things a bit unclear in your relationship. Here is a suggestion:` $PARTNER_ADVICE `Remember, communication and understanding are essential in addressing these complexities. Good luck!`': 'end',
                    }
                }
            },
        }
    }
}

# add more to the bad, empathise, and offer advice
friends = {
    'state': 'friends',
    '`How is your relationship with your friends?`': {
        '#GET_FRIENDS_STATUS': {  # to access friends status, use $FRIENDS_STATUS
            'good': {
                '`That\'s wonderful to hear! What do you makes your friendship string?`': {
                    '#GET_STRONG_ATTRIBUTE': {
                        '`It\'s great that $STRONG_ATTRIBUTE plays a significant role in your relationship. Remember to keep nurturing your bond and supporting each other. Have a great day!`': 'end',
                    }
                }
            },
            'bad': {
                '`I\'m sorry to hear that your relationship is going through a tough time. Can you tell me more about the challenges you\'re facing?`': {
                    '#GET_CHALLENGE': {
                        '`It sounds like $CHALLENGE is causing some issues in your relationship. Here is some advice:` $FRIENDS_ADVICE `I hope it helps, and remember, open communication and understanding are key to resolving conflicts. Take care!`': 'end',
                    }
                    # Add Empathizing here
                }
            },
            'complicated': {
                '`Relationships can be complicated sometimes. Can you tell me more about the aspects of your relationship that are causing confusion or mixed feelings?`': {
                    '#GET_CONFUSION': {
                        '`It seems like $CONFUSION is making things a bit unclear in your relationship. Here is a suggestion:` $FRIENDS_ADVICE `Remember, communication and understanding are essential in addressing these complexities. Good luck!`': 'end',
                    }
                }
                # Add Empathizing here
            },
        }
    }

}