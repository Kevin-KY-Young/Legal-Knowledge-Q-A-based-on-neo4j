

def question_classify(sentence, ltp):
	sentence_raw = sentence

	seg, hidden = ltp.seg([sentence])
	srl = ltp.srl(hidden, keep_empty=False)

	law_sublaw_v = ['有','包含', '含有', '包括', '属于']
	sublaw_action_v = ['是', '犯', '有', '判', '判处', '认定', '认为', '触犯', '违反']
	sublaw_punishment_v = ['有', '判','判处', '判罚', '判刑']

	di_all={}
	for tur in srl[0]:
		v=seg[0][tur[0]]
		di={}
		for turi in tur[1]:
			s=''
			for i in range(turi[1],turi[2]+1):
				s+=seg[0][i]
			di[turi[0]]=s
		di_all[v]=di

	class_li=[]
	sentence_li=[]

	for key in di_all.keys():
		if key in law_sublaw_v:
			if 'A1' in di_all[key].keys():
				if '罪' in di_all[key]['A1']:
					if len(di_all)>1:
						sentence=sentence.replace(key, '')
						for sub_key in di_all[key].keys():
							sentence=sentence.replace(di_all[key][sub_key], '')
					class_li.append('law_sublaw')
					if not sentence :
						sentence = sentence_raw
					sentence_li.append(sentence)


		if key in sublaw_punishment_v:
			if 'A1' in di_all[key].keys():
				if '刑' in di_all[key]['A1']:
					if len(di_all)>1:
						sentence=sentence.replace(key ,'')
						for sub_key in di_all[key].keys():
							sentence=sentence.replace(di_all[key][sub_key],'')
					class_li.append('sublaw_punishment')
					if not sentence :
						sentence = sentence_raw
					sentence_li.append(sentence)

		if key in sublaw_action_v:
			if 'A1' in di_all[key].keys():
				if len(di_all)>1:
					sentence=sentence.replace(key, '')
					for sub_key in di_all[key].keys():
						sentence=sentence.replace(di_all[key][sub_key],'')
				class_li.append('sublaw_action')
				if not sentence :
					sentence = sentence_raw
				sentence_li.append(sentence)
	if not sentence_li:
		sentence = sentence_raw
		sentence_li.append(sentence)
	return class_li, sentence_li


if __name__ == '__main__':
	li1, li2 = question_classify('放火罪属于什么罪')
	print(li1)
	print(li2)




