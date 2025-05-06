from flask import Flask, request, jsonify
from flask_cors import CORS
from githubApi import GitHubAPI, RepoProcessor, SemanticAnalyzer, KeywordExtractor, RelatedRepoFinder
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize the components
github_token = os.getenv('GITHUB_TOKEN', '')  # Get token from environment variable
if not github_token:
    print("Warning: GITHUB_TOKEN not found in environment variables. API rate limits will be restricted.")
else:
    print("GitHub token found. Checking rate limits...")

github_api = GitHubAPI(token=github_token)
# Check rate limits on startup
github_api.check_rate_limit()
repo_processor = RepoProcessor()
semantic_analyzer = SemanticAnalyzer()
keyword_extractor = KeywordExtractor()
repo_finder = RelatedRepoFinder(github_api, repo_processor, semantic_analyzer, keyword_extractor)

@app.route('/api/search', methods=['POST'])
def search_repos():
    data = request.get_json()
    github_url = data.get('github_url')
    selected_languages = data.get('languages', [])
    
    if not github_url:
        return jsonify({'error': 'GitHub URL is required'}), 400
    
    try:
        repos = repo_finder.find_related_repositories(github_url)
        if selected_languages:
            repos = [repo for repo in repos if repo['language'] in selected_languages]
        
        # Get unique languages for filtering
        languages = github_api.get_unique_languages(repos)
        
        return jsonify({
            'repositories': repos,
            'languages': languages
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/metadata', methods=['POST'])
def get_metadata():
    data = request.get_json()
    github_url = data.get('github_url')
    
    if not github_url:
        return jsonify({'error': 'GitHub URL is required'}), 400
    
    try:
        owner, repo = github_api.extract_repo_details(github_url)
        if not owner or not repo:
            return jsonify({'error': 'Invalid GitHub URL'}), 400
        
        metadata = github_api.get_repo_metadata(owner, repo)
        if not metadata:
            return jsonify({'error': 'Failed to fetch repository metadata'}), 404
        
        processed_metadata = repo_processor.preprocess_metadata(metadata)
        return jsonify(processed_metadata)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/topic-search', methods=['POST'])
def topic_search():
    data = request.get_json()
    topic = data.get('topic')
    selected_languages = data.get('languages', [])
    
    if not topic:
        return jsonify({'error': 'Topic is required'}), 400
    
    try:
        repos = github_api.search_repos_by_topic(topic)
        if not repos:
            return jsonify([])
        
        # Get unique languages for filtering
        languages = github_api.get_unique_languages(repos)
        
        # Rank repositories with language filter
        ranked_repos = repo_finder.rank_repositories(repos, topic, selected_languages)
        
        return jsonify({
            'repositories': ranked_repos,
            'languages': languages
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/match-profile', methods=['POST'])
def match_profile():
    data = request.get_json()
    profile_text = data.get('profile')
    repositories = data.get('repositories', [])
    
    if not profile_text or not repositories:
        return jsonify({'error': 'Profile text and repositories are required'}), 400
    
    try:
        # Get profile embedding
        profile_embedding = semantic_analyzer.get_embedding(profile_text)
        
        # Calculate similarity scores for each repository
        repo_scores = []
        
        for repo in repositories:
            # Calculate individual field similarities with weights
            similarities = {}
            
            # Description (highest weight - 0.4)
            if repo.get('description'):
                # Clean and normalize both texts
                clean_profile = profile_text.lower().strip()
                clean_desc = repo['description'].lower().strip()
                
                # Calculate similarity
                desc_similarity = semantic_analyzer.compute_similarity(clean_profile, clean_desc)
                
                # If the profile text is a substring of the description or vice versa, boost the similarity
                if clean_profile in clean_desc or clean_desc in clean_profile:
                    desc_similarity = max(desc_similarity, 0.8)  # Boost to at least 0.8 if it's a substring
                
                similarities['description'] = desc_similarity * 0.4
            else:
                similarities['description'] = 0
            
            # Topics (second highest weight - 0.3)
            if repo.get('topics'):
                topics_text = " ".join(repo['topics'])
                topics_similarity = semantic_analyzer.compute_similarity(profile_text, topics_text)
                similarities['topics'] = topics_similarity * 0.3
            else:
                similarities['topics'] = 0
            
            # Language (weight - 0.2)
            if repo.get('language'):
                lang_text = f"Written in {repo['language']}"
                lang_similarity = semantic_analyzer.compute_similarity(profile_text, lang_text)
                similarities['language'] = lang_similarity * 0.2
            else:
                similarities['language'] = 0
            
            # Name (lowest weight - 0.1)
            if repo.get('name'):
                name_similarity = semantic_analyzer.compute_similarity(profile_text, repo['name'])
                similarities['name'] = name_similarity * 0.1
            else:
                similarities['name'] = 0
            
            # Calculate total weighted similarity
            total_similarity = sum(similarities.values())
            
            # Prepare debug information
            debug_info = {
                'field_similarities': similarities,
                'description': repo.get('description', ''),
                'topics': repo.get('topics', []),
                'language': repo.get('language', ''),
                'name': repo.get('name', ''),
                'profile_text': profile_text,  # Add profile text for debugging
                'raw_similarity': desc_similarity if repo.get('description') else 0  # Add raw similarity score
            }
            
            repo_scores.append({
                'repo': repo,
                'similarity': total_similarity,
                'debug_info': debug_info
            })
        
        # Sort by similarity score
        repo_scores.sort(key=lambda x: x['similarity'], reverse=True)
        
        # Get the most similar repository
        most_similar = repo_scores[0] if repo_scores else None
        
        return jsonify({
            'most_similar_repo': most_similar['repo'] if most_similar else None,
            'similarity_score': most_similar['similarity'] if most_similar else 0,
            'debug_info': {
                'most_similar_debug': most_similar['debug_info'] if most_similar else None,
                'all_scores': [{
                    'repo_name': score['repo']['name'],
                    'score': score['similarity'],
                    'field_scores': score['debug_info']['field_similarities'],
                    'raw_description_similarity': score['debug_info']['raw_similarity']
                } for score in repo_scores]
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/test-token', methods=['GET'])
def test_token():
    try:
        # Check rate limits
        github_api.check_rate_limit()
        
        # Try to fetch a public repository to test the token
        test_repo = github_api.get_repo_metadata('octocat', 'Hello-World')
        
        if test_repo:
            return jsonify({
                'status': 'success',
                'message': 'GitHub token is working correctly',
                'rate_limit_info': {
                    'limit': github_api.headers.get('X-RateLimit-Limit', 'Unknown'),
                    'remaining': github_api.headers.get('X-RateLimit-Remaining', 'Unknown'),
                    'reset': github_api.headers.get('X-RateLimit-Reset', 'Unknown')
                }
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to fetch test repository'
            }), 500
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)