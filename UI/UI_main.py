from .UI_bag import *
import os 
import random
from PyQt5.QtWidgets import QApplication,QMainWindow
import yaml
import warnings
import sys
import torch
warnings.filterwarnings('ignore')
question_type = ''
config = yaml.load(open('config.yaml'), Loader=yaml.FullLoader)

example_questions_qa = config['example_questions']['example_questions_qa']
example_questions_predict = config['example_questions']['example_questions_predict']
example_action_describe = config['example_questions']['example_action_describe']

def print_input_sentense(ui):
    x=ui.input_sentence.toPlainText()
    ui.input_sentence.clear()
    ui.qa_return.append('您输入的问题是：'+ x)

def set_function(ui, type):
    global question_type
    question_type = type
    ui.qa_return.append('您选择了：'+ type)
    if type == '法律知识问答':
        ui.example_button.clicked.connect(lambda: ui.input_sentence.setText(random.choice(example_questions_qa)))
    elif type == 'AI法官-刑期预测':
        ui.example_button.clicked.connect(lambda: ui.input_sentence.setText(random.choice(example_questions_predict)))
    elif type == '犯罪行为描述':
        ui.example_button.clicked.connect(lambda: ui.input_sentence.setText(random.choice(example_action_describe)))
 
def change_font_size(ui, deta):
    if config['UI_params']['min_font_size'] < config['UI_params']['font_size'] + deta < config['UI_params']['max_font_size']:
        config['UI_params']['font_size']+= deta
        ui.qa_return.setFontPointSize(config['UI_params']['font_size'])
        ui.input_sentence.setFontPointSize(config['UI_params']['font_size'])
        last_qa_return = ui.qa_return.toPlainText()
        ui.qa_return.setText(last_qa_return)
        last_input_sentence = ui.input_sentence.toPlainText()
        ui.input_sentence.setText(last_input_sentence)
        
def initinalize_UI(ui, handler, model):
    change_font_size(ui, 0)
    ui.submit_button.clicked.connect(lambda:QA(ui, handler, model))
    ui.clear_button.clicked.connect(ui.input_sentence.clear)
    ui.qa.clicked.connect(lambda: set_function(ui, '法律知识问答'))
    ui.predict_times.clicked.connect(lambda: set_function(ui, 'AI法官-刑期预测'))
    ui.action_describe.clicked.connect(lambda: set_function(ui, '犯罪行为描述'))
    ui.open_neo4j.clicked.connect(lambda: os.system(config['UI_params']['google_location'] +' '+'http://localhost:7474/browser/'))
    ui.font_smaller.clicked.connect(lambda: change_font_size(ui, -config['UI_params']['change_v']))
    ui.font_bigger.clicked.connect(lambda: change_font_size(ui, config['UI_params']['change_v']))

def QA(ui, handler, model):
    global question_type
    question = ui.input_sentence.toPlainText()
    if len(question) == 0:
        ui.qa_return.append('你还没有输入问题呢！')
        return 
    ui.qa_return.append('用户：' + question)
    ui.input_sentence.clear()
    if question_type == '法律知识问答':
        answer = handler.chat_main(question)
        if type(answer) == type([]):
            for i in answer:
                ui.qa_return.append('小冰：'+ i)
                ui.qa_return.append('')
        elif type(answer) == type(str()):
            ui.qa_return.append('小冰：'+answer)
            ui.qa_return.append('')
    elif question_type == 'AI法官-刑期预测':
        outputs = model([question])
        _,predict = torch.max(outputs, 1)
        answer = '在小冰看来，可能会判刑{}年'.format(int(predict[0]))
        ui.qa_return.append('小冰：'+ answer)
        ui.qa_return.append('')
    elif question_type == '犯罪行为描述':
        answer = handler.chat_main(question + ',请问他犯什么罪？')
        if type(answer) == type([]):
            for i in answer:
                ui.qa_return.append('小冰：'+ i)
                ui.qa_return.append('')
        elif type(answer) == type(str()):
            ui.qa_return.append('小冰：'+answer)
            ui.qa_return.append('')
    else:
        ui.qa_return.append('请先选择问题类型吧！')
        ui.qa_return.append('')

def UI_main( handler, model):
    question_type = ''
    app=QApplication(sys.argv)
    mainWindow=QMainWindow()
    mainWindow.show()
    ui=Ui_MainWindow() 
    ui.setupUi(mainWindow)
    mainWindow.show()
    initinalize_UI(ui, handler, model)
    sys.exit(app.exec_())

if __name__ == '__main__':
    pass
