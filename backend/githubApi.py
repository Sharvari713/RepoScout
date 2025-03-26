import requests
import json
import torch
from transformers import AutoModel, AutoTokenizer
from sentence_transformers import util

# Load SBERT model for semantic similarity
model_name = "sentence-transformers/all-MiniLM-L6-v2"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModel.from_pretrained(model_name)

# Hardcoded GitHub repository (Change it as needed)
GITHUB_REPO = "https://github.com/torvalds/linux" 

##PART 1 
# Extract owner and repo name from URL
def extract_repo_details(url):
    parts = url.rstrip("/").split("/")
    return parts[-2], parts[-1]  # (owner, repo)

def get_repo_metadata(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        # Uncomment and add your token if you hit rate limits
        # "Authorization": "token YOUR_GITHUB_PAT"
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}, {response.json()}")
        return None

def preprocess_metadata(data):
    structured_data = {
        "Repository Name": data.get("name"),
        "Owner": data.get("owner", {}).get("login"),
        "Description": data.get("description"),
        "Stars": data.get("stargazers_count"),
        "Forks": data.get("forks_count"),
        "Open Issues": data.get("open_issues_count"),
        "Primary Language": data.get("language"),
        "Created At": data.get("created_at"),
        "Updated At": data.get("updated_at"),
        "License": data.get("license", {}).get("name") if data.get("license") else "No License",
        "Clone URL": data.get("clone_url"),
        "Contributors URL": data.get("contributors_url"),
        "Topics": data.get("topics", []),
    }
    return structured_data


##PART 2
def get_embedding(text):
    inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True)
    with torch.no_grad():
        embeddings = model(**inputs).last_hidden_state.mean(dim=1)
    return embeddings

def compute_similarity(text1, text2):
    emb1 = get_embedding(text1)
    emb2 = get_embedding(text2)
    return util.pytorch_cos_sim(emb1, emb2).item()

def fetch_additional_repo_data(repo_full_name):

    headers = {"Accept": "application/vnd.github.v3+json"}

    # Get Forks
    forks_url = f"https://api.github.com/repos/{repo_full_name}"
    forks_response = requests.get(forks_url, headers=headers)
    forks_count = forks_response.json().get("forks_count", 0) if forks_response.status_code == 200 else 0

    # Get Open Issues
    open_issues_url = f"https://api.github.com/repos/{repo_full_name}/issues"
    issues_response = requests.get(open_issues_url, headers=headers)
    open_issues_count = len(issues_response.json()) if issues_response.status_code == 200 else 0

    # Get Pull Requests
    pulls_url = f"https://api.github.com/repos/{repo_full_name}/pulls"
    pulls_response = requests.get(pulls_url, headers=headers)
    pr_count = len(pulls_response.json()) if pulls_response.status_code == 200 else 0

    # Get Recent Commits
    commits_url = f"https://api.github.com/repos/{repo_full_name}/commits"
    commits_response = requests.get(commits_url, headers=headers)
    recent_commits = len(commits_response.json()) if commits_response.status_code == 200 else 0

    # Compute Activity Score
    activity_score = recent_commits + open_issues_count + pr_count

    return forks_count, activity_score

def search_repos_by_topic(topic="NLP embedded analysis"):
    url = f"https://api.github.com/search/repositories?q=topic:{topic}"
    headers = {"Accept": "application/vnd.github.v3+json"}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        repos = data.get("items", [])
        print("Repos received:", len(repos))

        if not repos:
            print(f"No repositories found for topic: {topic}")
            return []

        structured_data = []
        for repo in repos:
            repo_full_name = repo["full_name"]

            # Fetch additional repo details
            forks_count, activity_score = fetch_additional_repo_data(repo_full_name)

            structured_data.append({
                "name": repo["name"],
                "owner": repo["owner"]["login"],
                "url": repo["html_url"],
                "stars": repo["stargazers_count"],
                "forks": forks_count,
                "activity": activity_score,
                "description": repo["description"] or "",
                "language": repo.get("language", "") or "",
            })

        return structured_data

    else:
        print(f"Failed to fetch data. Status Code: {response.status_code}")
        return []

def rank_repositories(repos, topic):

    ranked_repos = []

    for repo in repos:
        stars = repo["stars"]
        forks_count = repo["forks"]
        activity_score = repo["activity"]
        description = repo["description"]
        language = repo["language"]

        # Compute relevance score using SBERT
        topic_similarity = compute_similarity(topic, description)
        language_match = 1 if topic.lower() in language.lower() else 0
        relevance_score = (topic_similarity * 0.8) + (language_match * 0.2)

        # Compute final weighted score
        final_score = (stars * 0.4) + (forks_count * 0.2) + (activity_score * 0.2) + (relevance_score * 0.2)

        ranked_repos.append({
            "name": repo["name"],
            "owner": repo["owner"],
            "url": repo["url"],
            "stars": stars,
            "forks": forks_count,
            "activity": activity_score,
            "relevance": relevance_score,
            "final_score": final_score
        })

    # Sort by final score and return top 10
    ranked_repos = sorted(ranked_repos, key=lambda x: x["final_score"], reverse=True)[:10]

    return ranked_repos




# Main execution
# owner, repo = extract_repo_details(GITHUB_REPO)
# metadata = get_repo_metadata(owner, repo)
# if metadata:
#     structured_data = preprocess_metadata(metadata)
#     print(json.dumps(structured_data, indent=4))  
    
    
##PART 2
topic = "sentence comparision using Sbert"
repos = search_repos_by_topic(topic)
if repos:
    top_repos = rank_repositories(repos, topic)
    for repo in top_repos:
        print(repo)
