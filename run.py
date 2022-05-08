
import UI
import process
from copyreg import pickle
import torch
import wget
import os

import yaml
config = yaml.load(open('config.yaml'), Loader=yaml.FullLoader)

class BertClassfication(torch.nn.Module):
    def __init__(self):
        super(BertClassfication,self).__init__()
        self.fc = torch.nn.Linear(768,200)     
        
    def forward(self,x):           
        batch_tokenized = self.tokenizer.batch_encode_plus(x, add_special_tokens=True,
                                max_length=512,truncation=True, padding="max_length")    
        input_ids = torch.tensor(batch_tokenized['input_ids']).to(device_)
        attention_mask = torch.tensor(batch_tokenized['attention_mask']).to(device_)
        hiden_outputs = self.model(input_ids,attention_mask=attention_mask)
        outputs = hiden_outputs[0][:,0,:]   
        output = self.fc(outputs)
        return output

if __name__ == '__main__':
    model_path = config['predict_model']['model_path']
    device_ = torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')
    model_bert = torch.load(f = model_path, map_location=torch.device(device_))
    print('Loaded the predict model.')
    
    handler = process.ChatBotGraph()
    UI.UI_main(handler, model_bert)