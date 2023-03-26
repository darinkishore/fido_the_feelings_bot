from emora_stdm import DialogueFlow

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