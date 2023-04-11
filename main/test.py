from emora_stdm import DialogueFlow, Macro

df = DialogueFlow('start')

df.local_transitions({
    'state': 'start',
    "`Hello.`": {
        'state': 'nlu_step',
        "#DYNAJUMP(fuck_off)": {
            'state': 'state_you_wont_go_to'
        }
    }
})

df.local_transitions({
    'state': 'jump_target',
    "`We have successfully jumped.`": {
        'state': 'landing',
        'error': {
            'state': 'nlu_after_landing',
            "#DYNAJUMP(start) `Jump in NLG too.`": {
                'state': 'another_state_you_dont_see',
                'error': 'x'
            }
        }
    }
})

df.local_transitions({
    'state': 'fuck_off',
    "`We have successfully jumped.`": {
        'state': 'landing',
        'error': {
            'state': 'nlu_after_landing',
            "#DYNAJUMP(start) `Jump in NLG too.`": {
                'state': 'another_state_you_dont_see',
                'error': 'x'
            }
        }
    }
})


class DynaJump(Macro):
    def run(self, ngrams, vars, args):
        vars['__target__'] = args[0]
        return True


df.add_macros({'DYNAJUMP': DynaJump()})

if __name__ == '__main__':
    df.run(debugging=True)

