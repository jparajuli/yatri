###-------First step-------run the app using flask and get the verificatio
### information from the server

import sys, json, traceback, random, re
import requests
from flask import Flask,request
#from nltk import data
from pymongo import MongoClient
from datetime import datetime, timedelta
#from chatterbot import ChatBot
#from chatterbot.trainers import ListTrainer


#tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')

Greetings=['hi', 'hello', 'hi there', 'hello there']
Greetings_answer=['Hi there!', 'Hello there!','Welcome']

app=Flask(__name__)
app.config['MONGO_DBNAME']='test_mongo'
app.config['MONGO_URI']='mongodb://jhanak:jhanak@ds119210.mlab.com:19210/test_mongo'
#DBNAME ='test_mongo'
#URI = 'mongodb://jhanak:jhanak@ds119210.mlab.com:19210/test_mongo'

mongo=MongoClient(app.config['MONGO_URI'])
db= mongo[app.config['MONGO_DBNAME']]
log=db.message_log

PAT='EAAVSI7hWsxQBAEQWbbmwoYvDRlaLxzd4ZAK99rovFS0VngIOb1IQWytMAnoTYSNjbtM288JnGiTmx5JcKCWSkrNQGtAOJm6HblIFLPULeZATuH6bIQMUAT4YM28ZBhtfJim54qvU0S7EbTbnOOZCJZCU8BbIynch2KPOtZAdsIJAZDZD'
VFT='myLibrary'


##"""When you add a new subscription, or modify an existing one,
##Facebook servers will make a GET request to your callback
##URL in order to verify the validity of the callback server.
##A query string will be appended to this URL with the following parameters:
##hub.mode - The string "subscribe" is passed in this parameter
##hub.challenge - A random string
##hub.verify_token - The verify_token value you specified when you
##created the subscription"""
@app.route('/', methods=['GET'])
def verify():
    if request.args.get('hub.verify_token','')==VFT:
        print ("Webhook verified!")
        return request.args.get('hub.challenge','')
    else:
        return "Wrong verification token!"

###------Second Step---------------Browser tells the server that it wants to
    ###post the new information-----

##{
##  "object":"page",
##  "entry":[
##    {
##      "id":"PAGE_ID",
##      "time":1458692752478,
##      "messaging":[
##        {
##          "sender":{
##            "id":"USER_ID"
##          },
##          "recipient":{
##            "id":"PAGE_ID"
##          },
##
##          ...
##        }
##      ]
##    }
##  ]
##}    



###------post the message in the browser----

@app.route('/', methods=['POST'])
def webhook():
    payload=request.get_data()

    for sender_id, message in messaging_event(payload):

        try:
            response=processIncoming(sender_id,message)

            if response is not None:
                send_message(PAT,sender_id,response)

            else:
                send_message(PAT,sender_id, "Sorry, send it again!")
        except Exception as e:
            print(e)
            traceback.print_exc()
    return "ok"
   
        
Help=['help', 'please help', 'help me', 'hlp', 'halp', 'Can you help?', 'can you help please?']


def processIncoming(user_id, message):
    if message["type"]=="text":
        message_text=message["data"]
        #return message_text
        #log.insert(message_text)

        if message_text in Greetings:
            return random.choice(Greetings_answer)

        if message_text.lower() in Help:
            handle_help(user_id)
            return ''

        if message_text[-1] != ".":
            dott_message=message_text + '.'
            s=split_into_sentences(dott_message)
          
                                 
                
def messaging_event(payload):
    data=json.loads(payload.decode('utf-8'))
    messaging_events=data["entry"][0]["messaging"]

    for event in messaging_events:
        sender_id = event["sender"]["id"]

        if "message" not in event:
            yield sender_id, None

        if "message" in event and "text" in event["message"] and "quick_reply" not in event["message"]:
            text_msg=event["message"]["text"]
            log_message(log,sender_id, 'text', text_msg)
            yield sender_id, {'type':'text', 'data': text_msg, 'message_id': event['message']['mid']}
            

def log_message(log, sender, mes_type, message):
    now = datetime.now()
    timeStr = datetime.strftime(now,"%Y-%m-%d %H:%M:%S")
    log.insert_one({"sender":sender, "type": mes_type, 
        "message":message, "timestamp": timeStr })


def send_message(token,user_id,text):
    r = requests.post("https://graph.facebook.com/v2.6/me/messages",
                      params={"access_token": token},
                      data=json.dumps({
                          "recipient": {"id": user_id},
                          "message": {"text": text}
                      }),
                      headers={'Content-type': 'application/json'})
    if r.status_code != requests.codes.ok:
        print (r.text)

  

def handle_help(user_id):
    intro = "I can help you answer questions and will keep you entertained"
    send_message(PAT, user_id, intro)
    




caps = "([A-Z])"
prefixes = "(Mr|St|Mrs|Ms|Dr)[.]"
suffixes = "(Inc|Ltd|Jr|Sr|Co)"
starters = "(Mr|Mrs|Ms|Dr|He\s|She\s|It\s|They\s|Their\s|Our\s|We\s|But\s|However\s|That\s|This\s|Wherever)"
acronyms = "([A-Z][.][A-Z][.](?:[A-Z][.])?)"
websites = "[.](com|net|org|io|gov)"

def split_into_sentences(text):
    text = " " + text + "  "
    text = text.replace("\n"," ")
    text = re.sub(prefixes,"\\1<prd>",text)
    text = re.sub(websites,"<prd>\\1",text)
    if "Ph.D" in text: text = text.replace("Ph.D.","Ph<prd>D<prd>")
    text = re.sub("\s" + caps + "[.] "," \\1<prd> ",text)
    text = re.sub(acronyms+" "+starters,"\\1<stop> \\2",text)
    text = re.sub(caps + "[.]" + caps + "[.]" + caps + "[.]","\\1<prd>\\2<prd>\\3<prd>",text)
    text = re.sub(caps + "[.]" + caps + "[.]","\\1<prd>\\2<prd>",text)
    text = re.sub(" "+suffixes+"[.] "+starters," \\1<stop> \\2",text)
    text = re.sub(" "+suffixes+"[.]"," \\1<prd>",text)
    text = re.sub(" " + caps + "[.]"," \\1<prd>",text)
    if "”" in text: text = text.replace(".”","”.")
    if "\"" in text: text = text.replace(".\"","\".")
    if "!" in text: text = text.replace("!\"","\"!")
    if "?" in text: text = text.replace("?\"","\"?")
    text = text.replace(".",".<stop>")
    text = text.replace("?","?<stop>")
    text = text.replace("!","!<stop>")
    text = text.replace("<prd>",".")
    sentences = text.split("<stop>")
    sentences = sentences[:-1]
    sentences = [s.strip() for s in sentences]
    return sentences


if __name__ == '__main__':
    if len(sys.argv) == 2: # Allow running on customized ports
        app.run(port=int(sys.argv[1]))
    else:
        app.run() # Default port 5000
    
    
