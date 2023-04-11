# ========================================================================
# Copyright 2023 Emory University
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ========================================================================

__author__ = 'Jinho D. Choi'

import json
import re
import random
from json import JSONDecodeError
from typing import Dict, Any, List, Callable, Pattern
import random

import openai
from emora_stdm import Macro, Ngrams

import regexutils

OPENAI_API_KEY_PATH = 'resources/openai_api.txt'
CHATGPT_MODEL = 'gpt-3.5-turbo'


class MacroMakeFillerText(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        filler_text = ['Got it. That makes sense.',
                       "I understand where you're coming from.",
                       "That's a valid perspective.",
                       "I'm here to support you.",
                       "I'm listening",
                       "I hear you.",
                       "That's a complex issue.",
                       "I appreciate you sharing that with me.",
                       "I appreciate your honesty.",
                       "Thank you for trusting me with that.",
                       "It's understandable to feel that way.",
                       "That's a common issue.",
                       "It's important to be patient with yourself.",
                       "'Thanks for trusting me with your story."]
        return random.choice(filler_text)

class MacroMakeToughResponse(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        tough_response = ['I\'m sorry to hear that. I\'m here to support you.',
                            "I'm sorry you're going through that.",
                            "I'm sorry you're feeling that way.",
                            "I'm sorry you're having a hard time.",
                            "I'm sorry you're struggling with that.",
                            "It\'s really sad to know that. I want you to know that I'm by your side.",
                            "I'm sympathetic to your situation. You can count on me for support.",
                            "It's disheartening to hear that. I want to assure you that I'm here to help you!"]
        return random.choice(tough_response)

class MacroGPTJSON(Macro):
    def __init__(self, request: str, full_ex: Dict[str, Any], empty_ex: Dict[str, Any] = None,
                 set_variables: Callable[[Dict[str, Any], Dict[str, Any]], None] = None):
        """
        :param request: the task to be requested regarding the user input (e.g., How does the speaker want to be called?).
        :param full_ex: the example output where all values are filled (e.g., {"call_names": ["Mike", "Michael"]}).
        :param empty_ex: the example output where all collections are empty (e.g., {"call_names": []}).
        :param set_variables: it is a function that takes the STDM variable dictionary and the JSON output dictionary and sets necessary variables.
        """
        self.request = request
        self.full_ex = json.dumps(full_ex)
        self.empty_ex = '' if empty_ex is None else json.dumps(empty_ex)
        self.check = re.compile(regexutils.generate(full_ex))
        self.set_variables = set_variables

    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        examples = f'{self.full_ex} or {self.empty_ex} if unavailable' if self.empty_ex else self.full_ex
        prompt = f'{self.request} Respond in the JSON schema such as {examples}: {ngrams.text().strip()}'
        output = gpt_completion(prompt)
        if not output: return False

        try:
            d = json.loads(output)
        except JSONDecodeError:
            print(f'Invalid: {output}')
            return False

        if self.set_variables:
            self.set_variables(vars, d)
        else:
            vars.update(d)

        return True


class MacroNLG(Macro):
    def __init__(self, generate: Callable[[Dict[str, Any]], str]):
        self.generate = generate

    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        return self.generate(vars)


class MacroGPTJSONNLG(MacroGPTJSON, MacroNLG):
    def __init__(self, request: Callable, full_ex: Dict[str, Any], empty_ex: Dict[str, Any] = None,
                 set_variables: Callable[[Dict[str, Any], Dict[str, Any]], None] = None,
                 generate: Callable[[Dict[str, Any]], str] = None):
        MacroGPTJSON.__init__(self, request, full_ex, empty_ex, set_variables)
        MacroNLG.__init__(self, generate)

    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        request = self.request(vars) if callable(self.request) else self.request
        examples = f'{self.full_ex} or {self.empty_ex} if unavailable' if self.empty_ex else self.full_ex
        prompt = f'{request} Respond in the JSON schema such as {examples}: {ngrams.text().strip()}'
        output = gpt_completion(prompt)
        if not output: return False

        try:
            d = json.loads(output)
        except JSONDecodeError:
            print(f'Invalid: {output}')
            return False

        if self.set_variables:
            self.set_variables(vars, d)
        else:
            vars.update(d)

        return True


def gpt_completion(input: str, regex: Pattern = None) -> str:
    response = openai.ChatCompletion.create(
        model=CHATGPT_MODEL,
        messages=[
            {'role': 'system', 'content': 'You are a magic function behind a single-session-therapy chatbot. '
                                         'In any function responses you return, you must think from the perspective of a single session therapist'},
            {'role': 'user', 'content': input},
        ]
    )
    output = response['choices'][0]['message']['content'].strip()

    if regex is not None:
        m = regex.search(output)
        output = m.group().strip() if m else None

    return output
