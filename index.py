import json
import pickle
import time
from datetime import timedelta
import redis
import requests
import os
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, render_template, request
import config as cfg

def slack_config(slack_notification):
	slack_link = cfg.slack["slack_webhook"]
	response = requests.post(slack_link, data=json.dumps({'blocks': slack_notification}), headers={'Content-Type': 'application/json'})
	if response.status_code != 200:
		raise ValueError('Request to slack returned an error %s, the response is:\n%s' % (response.status_code, response.text))
	return 0
#rendering data as per slack need
def slack_data(bdata, key_set):
	landing_url = os.environ.get('landing_url')
	base_array = json.loads(bdata)
	alerts = base_array["data"]["result"][0]["values"][0]
	message_block = ''
	for index, i in enumerate(base_array["data"]["result"]):
		alerts = i["values"]
		clustername = i["stream"]["clustername"] if 'clustername' in i["stream"] else 'unavailable'
		app = i["stream"]["app"] if 'app' in i["stream"] else 'unavailable'
		message = alerts[0][1]
		if len(message) > 60:
			message = message[:59]
		if index == 5:
			break
		message_block += "\nClustername-> "+clustername+" App-> "+app+"\n"+message+"\n"
	slack_message = [{"type":"section", "text":{"type":"mrkdwn", "text":'<'+str(landing_url)+'/search?key='+str(key_set)+' | Loki Alert>'+'```'+message_block+'```'}}]
	#sending to func to make slack request
	slack_config(slack_message)
	return 0
#getting logs from loki
def get_alert():
	session = requests.Session()
	session.auth = (cfg.loki["username"], cfg.loki["password"])
	hostname = cfg.loki["hostname"]
	#query loki api for logs with filter for prod namespace and capitals error
	response = session.get(hostname + '/loki/api/v1/query', params={'query':'{namespace="prod"} |= "ERROR"'})
	bdata = response.text.encode('utf-8')
	#making a connection to redis
	redis_connect = redis.StrictRedis(host=redis_host, port=redis_port, db=11)
	pickled_obj = pickle.dumps(bdata)
	#making every key time based
	key_set = time.time()
	print(key_set)
	#setting log as data with time as key and ttl as 6 hours
	redis_connect.set(key_set, pickled_obj, timedelta(hours=6))
	#sending to func to render data as per slack need
	slack_data(bdata, key_set)
	return 0
redis_host = os.environ.get('redis_host')
redis_port = os.environ.get('redis_port')
SCHEDULER = BackgroundScheduler()
#scheduler to run for every 1 minute
SCHEDULER.add_job(func=get_alert, trigger="interval", seconds=59)
SCHEDULER.start()

APP = Flask(__name__)

@APP.route('/', methods=['GET'])
def homepage():
	redis_connect = redis.StrictRedis(host=redis_host, port=redis_port, db=11)
	base_array = []
	#for all keys
	for i in redis_connect.keys():
		#get the log from redis , unload from pickle , unload as json
		base_array.append(json.loads(pickle.loads(redis_connect.get(i))))
	return render_template('index.html', title="loki_alert", ba=base_array)
@APP.route('/search', methods=['GET'])
def searchpage():
	#accept the key as an argument from slack
	redis_key = request.args['key']
	redis_connect = redis.StrictRedis(host=redis_host, port=redis_port, db=11)
	base_array = []
	#get the log from redis , unload from pickle , unload as json
	base_array.append(json.loads(pickle.loads(redis_connect.get(redis_key))))
	return render_template('index.html', title="loki_alert", ba=base_array)
if __name__ == "__main__":
	APP.run(host= '0.0.0.0')