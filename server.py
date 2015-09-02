from flask import Flask, request, Response
from elasticsearch import Elasticsearch
import re
import random
import redis
import hashlib
import json
import time


app = Flask(__name__)
es = Elasticsearch([
    # 'http://ec2-52-25-78-6.us-west-2.compute.amazonaws.com:9200',
    'http://localhost:9200'
])
storage = redis.StrictRedis(host='localhost', port=6379, db=0)
m = hashlib.md5()


@app.route('/', methods=['POST'])
def recommend():
    text = str(request.form['text'])
    # print(text)
    excluded = {}
    if 'excluded' in request.form:
        excluded = request.form['excluded'].split(',')

    splitted = re.split(',| ', text)
    sample = random.sample(splitted, len(splitted)/4)
    sampled_text = ' '.join(sample)
    print(sampled_text)
    print(excluded)
    result = es.search(
        index='trippr',
        body={
            "query": {
                "more_like_this": {
                    "like_text": sampled_text,
                    "min_term_freq": 1,
                    "min_doc_freq": 1
                }
            }
        }
    )
    total = result['hits']['total']
    print total
    print("Got %d Hits:" % total)

    hits = result['hits']['hits']
    city = ''

    for hit in hits:
        if hit['_source']['name'] in excluded:
            continue
        else:
            city = hit['_source']['name'] \
                + ':' \
                + hit['_source']['country'] \
                + ':' \
                + hit['_source']['countrycode'] \
                + ':' \
                + hit['_source']['airportcode'] \
                + ':' \
                + hit['_source']['banner']

    print city
    return city

@app.route('/v1/search', methods=['POST'])
def v1_search():
    text = str(request.form['text'])
    # print(text)
    excluded = {}
    if 'excluded' in request.form:
        excluded = request.form['excluded'].split(',')

    splitted = re.split(',| ', text)
    sample = random.sample(splitted, len(splitted)/1)
    sampled_text = ' '.join(sample)
    print(sampled_text)
    print(excluded)
    result = es.search(
        index='trippr',
        body={
            "query": {
                "more_like_this": {
                    "like_text": sampled_text,
                    "min_term_freq": 1,
                    "min_doc_freq": 1
                }
            }
        }
    )
    total = result['hits']['total']
    print("Got %d Hits:" % total)

    hits = result['hits']['hits']
    city = ''
    result = {}

    for hit in hits:
        if hit['_source']['name'] in excluded:
            continue
        else:
            result['city'] = hit['_source']['name']
            result['country'] = hit['_source']['country']
            result['countrycode'] = hit['_source']['countrycode']
            result['airportcode'] = hit['_source']['airportcode']
            result['banner'] = hit['_source']['banner']
            result['booking_city_id'] = hit['_source']['booking_city_id']

    return Response(response=json.dumps(result),
                    status=200,
                    mimetype="application/json")

@app.route('/v1/hit', methods=['POST'])
def hit():
    text = str(request.form['text'])
    result = str(request.form['result'])
    m.update(text)
    key = m.hexdigest()
    storage.zincrby(key, result, 1)
    storage.zincrby('top', result, 1)
    print key
    return key + ' added'


@app.route('/v1/pics', methods=['GET'])
def pics():
    pics = []
    with open("/usr/share/flickr/pics_file.txt", "r") as myfile:
        for line in myfile:
            data = line.split('.jpg:')
            element = {'src': data[0] + '.jpg' , 'tags': data[1].replace(',', ' ').replace('\n','').replace(';','')}
            pics.append(element)

    result = {'date': time.strftime("%Y/%m/%d"), 'pics': pics}
    return Response(response=json.dumps(result),
                    status=200,
                    mimetype="application/json")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)

