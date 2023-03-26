from emora_stdm import DialogueFlow
import spacy
import time
import requests
import json
import sqlite3

import re
from emora_stdm import Macro, Ngrams
from typing import Dict, Any, List


# MACROS
class MacroGetTime(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        current_time = time.strftime("%H:%M")
        return current_time

