# -*- coding: utf-8 -*-
import requests 
import yaml
from .word_similarity import WordSimilarity2010

config = yaml.load(open('config.yaml'), Loader=yaml.FullLoader)
ws_tool = WordSimilarity2010()
host = config['baidu_api']['host']

def return_similarity_word(word, vocabulary, confidence=0.9):
    result_dict = {}
    for i in vocabulary:
        sim_a = ws_tool.similarity(word, i)
        if sim_a>=confidence:
            result_dict[i] = sim_a
    result_dict= dict(sorted(result_dict.items(),key=lambda x:x[1],reverse=True))
    return result_dict
def baiduapi_entities(sentence): 
    data = {'data':sentence}
    response = requests.get(url = host, params=data)
    answers = response.json()
    entities_set = set()
    for i in answers['entity_annotation']:
        entities_set.add(i['mention'])
    return entities_set

def return_entities(sentence):
    entities_dict = {'laws':set(),'sublaws':set(),'actions':set(),'punishments':set()}
    laws_list = [i.strip() for i in open(config['dict_txt']['law'],'r', encoding='utf8').readlines()]
    sublaws_list = [i.strip() for i in open(config['dict_txt']['sublaw'],'r', encoding='utf8').readlines()]
    actions_list = [i.strip() for i in open(config['dict_txt']['action'],'r', encoding='utf8').readlines()]
    punishes_list = [i.strip() for i in open(config['dict_txt']['punishments'],'r', encoding='utf8').readlines()]
    for i in laws_list:
        if i in sentence:
            entities_dict['laws'].add(i)
    for i in sublaws_list:
        if i in sentence:
            entities_dict['sublaws'].add(i)
    for i in punishes_list:
        if i in sentence:
            entities_dict['punishments'].add(i)
    
    if len(entities_dict['laws']) == 0 and len(entities_dict['sublaws']) == 0:
        entities_set = baiduapi_entities(sentence)
        for i in entities_set:
            re = list(return_similarity_word(i,actions_list, 0.90).keys())
            if re:
                entities_dict['actions'].add(re[0])
    # print(entities_dict)

    #将上述set改成list列表
    laws = list(entities_dict["laws"])
    sublaws = list(entities_dict["sublaws"])
    actions = list(entities_dict["actions"])
    punishments = list(entities_dict["punishments"])
    entities_dict = []
    entities_dict += laws + sublaws + actions + punishments
    return entities_dict, len(laws), len(sublaws), len(actions), len(punishments)

if __name__ == '__main__':
    print("Examples:")
    sentence = '张三逃税'
    x = return_entities(sentence)
    print(x)