import os
from py2neo import Graph
from regex import I
from .return_entities import return_entities
from .question_classifier_law import question_classify
from ltp import LTP
import yaml
config = yaml.load(open('config.yaml'), Loader=yaml.FullLoader)

class QuestionClassifier:
    def __init__(self):
        #--> 找到所有自己定义好的关键词表，包括各种方面的关键词
        cur_dir = '/'.join(os.path.abspath(__file__).split('/')[:-1])
        #　特征词路径
        self.laws_path = os.path.join(cur_dir, 'dict_law/laws.txt')
        self.sublaws_path = os.path.join(cur_dir, 'dict_law/sublaws.txt')
        self.actions_path = os.path.join(cur_dir, 'dict_law/actions.txt')
        self.punishments_path = os.path.join(cur_dir, 'dict_law/punishments.txt')
        
        # 加载特征词，去掉最后的\n
        self.laws_wds= [i.strip() for i in open(self.laws_path, encoding='utf-8') if i.strip()]
        self.sublaws_wds= [i.strip() for i in open(self.sublaws_path, encoding='utf-8') if i.strip()]
        self.actions_wds= [i.strip() for i in open(self.actions_path, encoding='utf-8') if i.strip()]
        self.punishments_wds= [i.strip() for i in open(self.punishments_path, encoding='utf-8') if i.strip()]
        # region_words比较特殊，他是前边所有的几个集合
        self.region_words = set(self.laws_wds + self.sublaws_wds + self.actions_wds + self.punishments_wds)
        # 我们的神经网络
        self.nn = return_entities
        self.senType = question_classify
        self.ltp = LTP()
        # 构建词典，["关键词"]:类别，注意这些关键词是要和neo4j对应的，而下边的疑问词只是作为问题类型判断的，两者的作用不一样，虽然都是关键词
        self.wdtype_dict = self.build_wdtype_dict()
        # 问句疑问词
        self.quesiton_type = []
        print('model init finished ......')
        return

    '''分类主函数'''
    def classify(self, question):
        # question是原始问题，不加修改的，原汁原味
        data = {}
        # yky的问句类型
        question_types_raw, question = self.senType(question, self.ltp)
        #mediccal_dict是question中所有的关键词以及对应的问题类型
        if question:
            medical_dict, lenOfLaw, lenOfSublaw = self.check_law(question[0])
        else:
            return []

        if not medical_dict:
            return {}
        #args即查询，也就是question中的关键词和对应问题类型字典集合
        data['args'] = medical_dict

        #收集问句当中所涉及到的实体类型
        types = [] #types即question问题中包含的所有关键词的类型，其实这个是和我们想要问的问题类型是一一对应的
        for type_ in medical_dict.values():
            types += type_ #注意这个加不是字符串的加，而是集合的加，即append
        
        # sublaw_punishenment sublaw_action law_sublaw三大类关系，要分成六大类关系
        # 统计law sublaw action punishment四个的数量
        # 如果law 和 sublaw存在的话，说明question里边存在罪的名字，是我们想要查的前两种问题
        question_types = []
        #第一种写的和下边不太一样，为了更好的检测出第一种问题，关键词太少
        if lenOfLaw or lenOfSublaw:
            # 某一个大罪下边包含什么小罪,如果有大类罪名就认为他要问第一种问题
            if lenOfLaw:
                question_types.append("law_sublaw")
            # 某一个小罪属于哪个大类，需要raw里边有law_sublaw，且lenOfSublaw大于0
            elif lenOfSublaw and 'law_sublaw' in question_types_raw:
                question_types.append("sublaw_law")
        if "sublaw_action" in question_types_raw:
            if lenOfSublaw > 0:
                question_types.append("sublaw_action")
            else:
                question_types.append("action_sublaw")
        
        if "sublaw_punishment" in question_types_raw:
            if lenOfSublaw > 0:
                question_types.append("sublaw_punishment")
            else:
                question_types.append("punishment_sublaw")

        # 将多个分类结果进行合并处理，组装成一个字典
        # data将会包含一个问句类型
        data['question_types'] = question_types

        return data

    '''构造词对应的类型'''
    def build_wdtype_dict(self):
        #将刚才的list关键词表转化为dict的形式
        wd_dict = dict()
        #遍历表中的每一个词
        for wd in self.region_words:
            #以词的名字作为索引值
            wd_dict[wd] = []
            #然后构建每个词对应的关键词类型，方便后续的问题分类
            #值得注意的是，每一个关键词可能会对应多个类别
            if wd in self.laws_wds:
                wd_dict[wd].append('laws')
            if wd in self.sublaws_wds:
                wd_dict[wd].append('sublaws')
            if wd in self.actions_wds:
                wd_dict[wd].append('actions')
            if wd in self.punishments_wds:
                wd_dict[wd].append('punishments')
        #返回
        return wd_dict

    '''问句过滤'''
    def check_law(self, question):
        #question是原始问题
        #region_wds是question中出现的关键词
        region_wds = []
        # 原来这里是通过ac自动机匹配关键词，我们改成了神经网络
        region_wds, lenOfLaw, lenOfSublaw, lenOfAction, lenOfPunishment  = self.nn(question)

        #如果关键词之间有包含关系，那我们找出这种重复的词
        
        stop_wds = []
        for wd1 in region_wds:
            for wd2 in region_wds:
                if wd1 in wd2 and wd1 != wd2:
                    stop_wds.append(wd1)
        #求region_wds和stop_wds的差，剔除冗余项
        final_wds = [i for i in region_wds if i not in stop_wds]
        #final_dict是将上述关键词映射到我们的关键词字典中，["关键词"]:类型
        final_dict = {i:self.wdtype_dict.get(i) for i in final_wds}

        return final_dict, lenOfLaw, lenOfSublaw

    '''基于特征词进行分类'''
    def check_words(self, wds, sent):
        #如果我们定义的问句关键词出现在了question当中，那么就默认我们将会回答这种问题
        for wd in wds:
            if wd in sent:
                return True
        return False

class QuestionPaser:

    '''构建实体节点'''
    def build_entitydict(self, args):
        # entity_dict是将args逆变换一下，也就是变成["type"]:关键词
        entity_dict = {}
        # arg是关键词,types是类型，一个arg可能对应多个类型
        for arg, types in args.items():
            for type in types:
                if type not in entity_dict:
                    entity_dict[type] = [arg]
                else:
                    entity_dict[type].append(arg)
        return entity_dict

    '''解析主函数'''
    def parser_main(self, res_classify):
        # res_classify是一个 data，包含["arg"]和["question_types"]
        # args是关键词以及对应的类型
        args = res_classify['args']
        # entity_dict是一个["类型"]：关键词形式的字典
        entity_dict = self.build_entitydict(args)
        #question_types是一个问句类型列表
        question_types = res_classify['question_types']
        #导入上述信息后，我们要开始构建我们的sql
        sqls = []
        # 遍历每一种问句类型
        for question_type in question_types:
            # sql_包含着每一个sql对应的所有信息
            sql_ = {}
            # 这条sql信息的问句类型
            sql_['question_type'] = question_type
            sql = []
            # 一种问句类型只能对应一个sql句子，根据我们识别的问句类型，给出相应的关键词即可，不需要给所有的关键词
            # law_sublaw : law xxx罪包含什么罪
            if question_type == 'law_sublaw':
                sql = self.sql_transfer(question_type, entity_dict.get('laws'))
            # sublaw_law : sublaw xxx罪属于什么罪
            elif question_type == 'sublaw_law':
                sql = self.sql_transfer(question_type, entity_dict.get('sublaws'))
            # action_sublaw : action xxx行为会导致什么罪
            elif question_type == 'action_sublaw':
                sql = self.sql_transfer(question_type, entity_dict.get('actions'))
            # sublaw_action : sublaw xxx罪有什么行为
            elif question_type == 'sublaw_action':
                sql = self.sql_transfer(question_type, entity_dict.get('sublaws'))
            # punishment_sublaw : punishment 什么罪会有xxx处罚
            elif question_type == 'punishment_sublaw':
                sql = self.sql_transfer(question_type, entity_dict.get('punishments'))
            # sublaw_punishment : sublaw xxx罪会有什么处罚
            elif question_type == 'sublaw_punishment':
                sql = self.sql_transfer(question_type, entity_dict.get('sublaws'))
            
            if sql:
                # sql_中的["sql"]为具体cypher语句
                sql_['sql'] = sql
                sqls.append(sql_)

        return sqls

    '''针对不同的问题，分开进行处理'''
    def sql_transfer(self, question_type, entities):
        # question_type是这个句子的问题类型，entities是question句子中对应的这个问题类型所对应的所有关键词(每次问题对应的entities都在一个数据库，所以下边i会在不同位置出现)
        if not entities:
            return []

        # 查询语句
        sql = []

        # 原来的那种查询方法是针对一对一关系或者一对多关系的，没有多对一，一对多时sql会是一个列表（后边的for），所以原来for query可能是多个
        # law_sublaw : law xxx罪包含什么罪
        if question_type == 'law_sublaw':
            sql = ["MATCH (m:Law)-[r:subclass_law]->(n:Sublaw) where m.name = '{0}' return m.name, r.name, n.name".format(i) for i in entities]
        # sublaw_law : sublaw xxx罪属于什么罪
        elif question_type == 'sublaw_law':
            sql = ["MATCH (m:Law)-[r:subclass_law]->(n:Sublaw) where n.name = '{0}' return m.name, r.name, n.name".format(i) for i in entities]
        # action_sublaw : action xxx行为会导致什么罪
        elif question_type == 'action_sublaw':
            sql = self.multi2one(question_type, entities)
        # sublaw_action : sublaw xxx罪有什么行为
        elif question_type == 'sublaw_action':
            sql = ["MATCH (m:Sublaw) where m.name = '{0}' return m.name, m.describe".format(i) for i in entities]
        # punishment_sublaw : punishment 什么罪会有xxx处罚
        elif question_type == 'punishment_sublaw':
            sql = ["MATCH (m:Sublaw)-[r:law_punishment]->(n:Punishment) where n.name = '{0}' return m.name, r.name, n.name".format(i) for i in entities]
        # sublaw_punishment : sublaw xxx罪会有什么处罚
        elif question_type == 'sublaw_punishment':
            sql = ["MATCH (m:Sublaw) where m.name = '{0}' return m.name, m.punishment".format(i) for i in entities]
        
        #返回了一个sql
        return sql
    
    def multi2one(self, question_type, entities):
        if question_type == "action_sublaw":
            sql_list = []
            for i in entities:
                sql = "MATCH(a:Sublaw)-[b:law_action]->(c:Action) WHERE '{}' in a.action RETURN distinct a.name, a.describe, a.punishment".format(i)
                sql_list.append(sql)
        return sql_list
    
    
    def multi2one_old(self, question_type, entities):
        # ############################################
        # 这里现在写的是所有的都用上的，需要改进为最大匹配
        if question_type == "action_sublaw":
            sql = "MATCH(a:Sublaw)-[b:law_action]->(c:Action) WHERE True "
            for i in entities:
                sql +=  'AND ' + "'" + i +"'" + ' in a.action '
            sql += 'RETURN distinct a.name, a.describe, a.punishment'
        
        sql = [sql]

        return sql

class AnswerSearcher:
    def __init__(self):
        self.g = Graph(
            host=config['neo4j']['host'],
            http_port=config['neo4j']['http_port'],
            user=config['neo4j']['user'],
            password=config['neo4j']['password'])
        self.num_limit = 20

    '''执行cypher查询，并返回相应结果'''
    def search_main(self, sqls):
        # sqls中有很多个元素，每个对应一个具体的查询
        # 构建final_answers
        final_answers = []
        for sql_ in sqls:
            question_type = sql_['question_type']
            queries = sql_['sql']
            answers = []
            
            for query in queries:
                ress = self.g.run(query).data()
                answers += ress

            # answers是对应查到的答案，下边将其标准化
            final_answer = self.answer_prettify(question_type, answers)
            if final_answer:
                final_answers.append(final_answer)
        #final_answers有很多个，是个列表
        return final_answers

    '''根据对应的qustion_type，调用相应的回复模板'''
    def answer_prettify(self, question_type, answers):
        final_answer = []
        if not answers:
            return ''

        if question_type == 'law_sublaw':
            desc = [i['n.name'] for i in answers]
            subject = answers[0]['m.name']
            final_answer = '{0}包括：{1}'.format(subject, '；'.join(list(set(desc))[:self.num_limit]))

        # sublaw_law : sublaw xxx罪属于什么罪
        elif question_type == 'sublaw_law':
            desc = [i['m.name'] for i in answers]
            subject = answers[0]['n.name']
            final_answer = '{0}属于：{1}'.format(subject, '；'.join(list(set(desc))[:self.num_limit]))

        # action_sublaw : action xxx行为会导致什么罪
        elif question_type == 'action_sublaw':
            desc = [i['a.name'] for i in answers]
            desc_dict = {}
            for i in desc:
                if i in desc_dict:
                    desc_dict[i] += 1
                else:
                    desc_dict[i] = 1
            best_answer = max(list(desc_dict.values()))
            desc_final = []
            for i in desc:
                if desc_dict[i] == best_answer:
                    desc_final.append(i)
            final_answer = '您说的这些行为将可能导致犯如下罪：{0}'.format('；'.join(list(set(desc_final))[:self.num_limit]))

        # sublaw_action : sublaw xxx罪有什么行为
        elif question_type == 'sublaw_action':
            desc = [i['m.describe'] for i in answers]
            subject = answers[0]['m.name']
            final_answer = '{0}的犯罪行为包括：{1}'.format(subject, desc[0][0])

        # punishment_sublaw : punishment 什么罪会有xxx处罚
        elif question_type == 'punishment_sublaw':
            desc = [i['m.name'] for i in answers]
            final_answer = '这些处罚对应的罪行可能有：{0}'.format('；'.join(list(set(desc))[:self.num_limit]))

        # sublaw_punishment : sublaw xxx罪会有什么处罚
        elif question_type == 'sublaw_punishment':
            desc = [i['m.punishment'] for i in answers]
            subject = answers[0]['m.name']
            final_answer = '{0}罪的可能处罚包括：{1}'.format(subject, desc[0])

        return final_answer

'''问答类'''
class ChatBotGraph:
    def __init__(self):
        #首先要将原文中的基于模板的匹配方法，改变为基于神经网络的匹配方法
        self.classifier = QuestionClassifier()
        self.parser = QuestionPaser()
        self.searcher = AnswerSearcher()

    def chat_main(self, sent):
        answer = config['return_answer']
        #--> 将所说问题转化为一个data，data["arg"]里边包含了question对应的关键词以及关键词类型，data["question_types"]是问句类型
        res_classify = self.classifier.classify(sent)

        if not res_classify:
            return answer
        # 有了问句类型以及关键词，下一步就是将其转化为cypher语言
        #--> res_sql是一个集合，因为一句话可能对应多个问题，对于每一个元素s, s["sql"]是对应语句，s["question_type"]是该句子对应的问句类型
        res_sql = self.parser.parser_main(res_classify)

        #--> 有了sql，下一步就是用cypher具体去查询
        final_answers = self.searcher.search_main(res_sql)
        if not final_answers:
            return answer
        else:
            return final_answers

if __name__ == '__main__':
    handler = ChatBotGraph()
    while 1:
        question = input('用户:')
        if question == "再见":
            break
        answer = handler.chat_main(question)
        print('小小勇:', answer)