from flask import Flask, request
from elasticsearch import Elasticsearch
import re
import random
import redis
import hashlib


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

@app.route('/hit', methods=['POST'])
def hit():
    text = str(request.form['text'])
    result = str(request.form['result'])
    m.update(text)
    key = m.hexdigest()
    storage.zincrby(key, result, 1)
    storage.zincrby('top', result, 1)
    print key
    return key + ' added'


@app.route('/pics', methods=['GET'])
def pics():
    with open("/root/pics_file.txt", "r") as myfile:
        data = myfile.read().replace('\n', '')
    return data

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)

