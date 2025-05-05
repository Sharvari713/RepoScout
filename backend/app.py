from flask import Flask, request, jsonify
from flask_cors import CORS
from githubApi import GitHubAPI, RepoProcessor, SemanticAnalyzer, KeywordExtractor, RelatedRepoFinder
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize the components
github_token = os.getenv('GITHUB_TOKEN', '')  # Get token from environment variable
github_api = GitHubAPI(token=github_token)
repo_processor = RepoProcessor()
semantic_analyzer = SemanticAnalyzer()
keyword_extractor = KeywordExtractor()
related_repo_finder = RelatedRepoFinder(github_api, repo_processor, semantic_analyzer, keyword_extractor)

@app.route('/api/related-repos', methods=['POST'])
def get_related_repositories():
    """
    API Endpoint 1: Find related repositories based on a GitHub URL
    """
    data = request.get_json()
    if not data or 'url' not in data:
        return jsonify({'error': 'Please provide a GitHub repository URL'}), 400
    
    github_url = data['url']
    try:
        related_repositories = related_repo_finder.find_related_repositories(github_url)
        return jsonify({
            'status': 'success',
            'data': related_repositories
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/repo-metadata', methods=['POST'])
def get_repo_metadata():
    """
    API Endpoint 2: Get detailed metadata for a GitHub repository
    """
    data = request.get_json()
    if not data or 'url' not in data:
        return jsonify({'error': 'Please provide a GitHub repository URL'}), 400
    
    github_url = data['url']
    try:
        owner, repo_name = github_api.extract_repo_details(github_url)
        metadata = github_api.get_repo_metadata(owner, repo_name)
        if metadata:
            structured_metadata = repo_processor.preprocess_metadata(metadata)
            return jsonify({
                'status': 'success',
                'data': structured_metadata
            })
        else:
            return jsonify({'error': 'Repository not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/search-by-topic', methods=['POST'])
def search_by_topic():
    """
    API Endpoint 3: Search repositories by topic
    """
    data = request.get_json()
    if not data or 'topic' not in data:
        return jsonify({'error': 'Please provide a search topic'}), 400
    
    topic = data['topic']
    try:
        searched_repos = github_api.search_repos_by_topic(topic)
        if searched_repos:
            ranked_searched_repos = related_repo_finder.rank_repositories(searched_repos, topic)
            return jsonify({
                'status': 'success',
                'data': ranked_searched_repos[:5]  # Return top 5 results
            })
        else:
            return jsonify({'error': 'No repositories found for the given topic'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)