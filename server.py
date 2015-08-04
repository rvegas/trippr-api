from flask import Flask, request
from elasticsearch import Elasticsearch
import re
import random


app = Flask(__name__)
es = Elasticsearch([
    # 'http://ec2-52-25-78-6.us-west-2.compute.amazonaws.com:9200',
    'http://localhost:9200'
])


@app.route('/', methods=['POST'])
def hello_world():
    text = str(request.form['text'])
    # print(text)
    excluded = {}
    if 'excluded' in request.form:
        excluded = request.form['excluded'].split(',')

    splitted = re.split(',| ', text)
    sample = random.sample(splitted, len(splitted)/8)
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
		+ hit['_source']['airportcode']

    print city
    return city

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
