from flask import Flask, request, jsonify
from flask_cors import CORS
from github_parser import parse_github_repo
from embedding_store import embed_and_search

import os

app = Flask(__name__)
CORS(app)

@app.route('/ask', methods=['POST'])
def ask():
    data = request.json
    repo_url = data['repoUrl']
    question = data['question']

    chunks = parse_github_repo(repo_url)
    print(chunks)
    answer = embed_and_search(chunks, question)

    return jsonify({"answer": answer})

if __name__ == '__main__':
    app.run(port=5001)
