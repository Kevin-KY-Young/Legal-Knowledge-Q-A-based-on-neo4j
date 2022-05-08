import os
import json
from py2neo import Graph,Node
import yaml
config = yaml.load(open('config.yaml'), Loader=yaml.FullLoader)
encoding='utf-8'

class LawGraph:
	def __init__(self):
		cur_dir = '/'.join(os.path.abspath(__file__).split('/')[:-1])
		self.data_path = os.path.join(cur_dir, 'data/data.json')
		self.g = Graph(
            host=config['neo4j']['host'],
            http_port=config['neo4j']['http_port'],
            user=config['neo4j']['user'],
            password=config['neo4j']['password'])
		self.g.delete_all()

	'''读取文件'''
	def read_nodes(self):
		# 共4类节点

		laws = []
		sublaws = []		#describe:概念
		actions = []		#犯罪行为
		punishments = []		#犯罪处罚
		law_classes = []		#所属法典

		sublaw_infos = []		#子法律信息


		# 构建节点实体关系
		rels_sublaw = []		#罪名与子罪名之间的关系
		rels_whataction = []		#子罪名与犯罪行为之间的关系
		rels_whatpunishment = []		#子罪名与犯罪处罚之间的关系
		rels_belongto = []		#罪名与所属法律之间的关系



		count = 0
		for data in open(self.data_path,encoding='utf-8'):
			sublaw_dict = {}
			count += 1
			print(count)
			data_json = json.loads(data)
			sublaw = data_json['sublaw']
			sublaw_dict['sublaw'] = sublaw
			sublaws.append(sublaw)
			sublaw_dict['law'] = ''
			sublaw_dict['action'] = ''
			sublaw_dict['punishment'] = ''
			# sublaw_dict['lawclass'] = ''


			if 'law' in data_json:
				laws.append(data_json['law'])
				law = data_json['law']
				rels_sublaw.append([law, sublaw])
				sublaw_dict['law'] = data_json['law']

			if 'action' in data_json:
				actions += data_json['action']
				for action in data_json['action']:
					rels_whataction.append([sublaw, action])
				sublaw_dict['action'] = data_json['action']

			if 'punishment' in data_json:
				punishments += data_json['punishment']
				for punishment in data_json['punishment']:
					rels_whatpunishment.append([sublaw, punishment])
				sublaw_dict['punishment'] = data_json['punishment']

			if 'describe' in data_json:
				sublaw_dict['describe'] = data_json['describe']

			if 'lawclass' in data_json:
				law_classes.append(data_json['lawclass'])
				if 'law' in data_json:
					law = data_json['law']
					lawclass = data_json['lawclass']
					rels_belongto.append([law, lawclass])
						# sublaw_dict['law'] = data_json['law']


			# if 'desc' in data_json:
			# 	disease_dict['desc'] = data_json['desc']


			sublaw_infos.append(sublaw_dict)
		return set(laws), set(sublaws), set(actions), set(punishments), sublaw_infos, rels_sublaw, rels_whataction, rels_whatpunishment

	'''建立无属性节点'''
	def create_node(self, label, nodes):
		count = 0
		for node_name in nodes:
			node = Node(label, name=node_name)
			self.g.create(node)
			count += 1
			print(count, len(nodes))
		return

	'''创建知识图谱中心子罪名的节点（有属性节点）'''
	def create_center_nodes(self, sublaw_infos):
		count = 0
		for sublaw_dict in sublaw_infos:
			node = Node("Sublaw", name=sublaw_dict['sublaw'], describe=sublaw_dict['describe'], law=sublaw_dict['law'], action=sublaw_dict['action'], punishment=sublaw_dict['punishment'])
			self.g.create(node)
			count += 1
			print(count)
		return

	'''创建知识图谱实体节点类型schema'''
	def create_graphnodes(self):
		Laws, Sublaws, Actions, Punishments, sublaw_infos, rels_sublaw, rels_whataction, rels_whatpunishment = self.read_nodes()
		self.create_center_nodes(sublaw_infos)
		self.create_node('Law', Laws)
		print(len(Laws))
		# self.create_node('Sublaw', Sublaws)
		# print(len(Sublaws))
		self.create_node('Action', Actions)
		print(len(Actions))
		self.create_node('Punishment', Punishments)
		print(len(Punishments))

		return


	'''创建实体关系边'''
	def create_graphrels(self):
		# Drugs, Foods, Checks, Departments, Producers, Symptoms, Diseases, disease_infos, rels_check, rels_recommandeat, rels_noteat, rels_doeat, rels_department, rels_commonddrug, rels_drug_producer, rels_recommanddrug,rels_symptom, rels_acompany, rels_category = self.read_nodes()
		Laws, Sublaws, Actions, Punishments, sublaw_infos, rels_sublaw, rels_whataction, rels_whatpunishment = self.read_nodes()
		self.create_relationship('Law', 'Sublaw', rels_sublaw, 'subclass_law', '子罪名')
		self.create_relationship('Sublaw', 'Action', rels_whataction, 'law_action', '犯罪行为')
		self.create_relationship('Sublaw', 'Punishment', rels_whatpunishment, 'law_punishment', '犯罪处罚')
		
	'''创建实体关联边'''
	def create_relationship(self, start_node, end_node, edges, rel_type, rel_name):
		count = 0
		# 去重处理
		set_edges = []
		for edge in edges:
			set_edges.append('###'.join(edge))
		all = len(set(set_edges))
		for edge in set(set_edges):
			edge = edge.split('###')
			p = edge[0]
			q = edge[1]
			query = "match(p:%s),(q:%s) where p.name='%s'and q.name='%s' create (p)-[rel:%s{name:'%s'}]->(q)" % (
				start_node, end_node, p, q, rel_type, rel_name)
			try:
				self.g.run(query)
				count += 1
				print(rel_type, count, all)
			except Exception as e:
				print(e)
		return

	'''导出数据'''
	def export_data(self):
		# Drugs, Foods, Checks, Departments, Producers, Symptoms, Diseases, disease_infos, rels_check, rels_recommandeat, rels_noteat, rels_doeat, rels_department, rels_commonddrug, rels_drug_producer, rels_recommanddrug, rels_symptom, rels_acompany, rels_category = self.read_nodes()
		Laws, Sublaws, Actions, Punishments, sublaw_infos, rels_sublaw, rels_whataction, rels_whatpunishment = self.read_nodes()
		f_law = open('law.txt', 'w+')
		f_sublaw = open('sublaw.txt', 'w+')
		f_action = open('action.txt', 'w+')
		f_punishment = open('punishment.txt', 'w+')
		

		f_law.write('\n'.join(list(Laws)))
		f_sublaw.write('\n'.join(list(Sublaws)))
		f_action.write('\n'.join(list(Actions)))
		f_punishment.write('\n'.join(list(Punishments)))
		

		f_law.close()
		f_sublaw.close()
		f_action.close()
		f_punishment.close()
		

		return



if __name__ == '__main__':
	handler = LawGraph()
	handler.create_graphnodes()
	handler.create_graphrels()
	# handler.export_data()

#json格式:
#	sublaw:v1, law:v2, action:v3, punishment:v4, describe:v5
