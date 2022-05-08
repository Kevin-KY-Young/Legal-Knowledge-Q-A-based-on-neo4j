
from .word_similarity import WordSimilarity2010
from .return_entities import return_entities
from .chatbot_law import ChatBotGraph
from .question_classifier_law import question_classify

import yaml
config = yaml.load(open('config.yaml'), Loader=yaml.FullLoader)