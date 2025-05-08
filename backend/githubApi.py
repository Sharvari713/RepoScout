import requests
import json
import torch
from transformers import AutoModel, AutoTokenizer
from sentence_transformers import util
from urllib.parse import quote
from keybert import KeyBERT
import time
import os
from datetime import datetime, timezone, timedelta

class GitHubAPI:
    def __init__(self, token=None):
        self.headers = {"Accept": "application/vnd.github.v3+json"}
        if token:
            self.headers["Authorization"] = f"token {token}"

    def check_rate_limit(self):
        response = requests.get("https://api.github.com/rate_limit", headers=self.headers)
        if response.status_code == 200:
            data = response.json()
            core = data["rate"]
            print(f"Core Limit: {core['limit']}")
            print(f"Core Remaining: {core['remaining']}")
            print(f"Core Reset: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(core['reset']))}")
        else:
            print(f"Failed to fetch rate limit status: {response.status_code}")

    def extract_repo_details(self, url):
        parts = url.rstrip("/").split("/")
        return parts[-2], parts[-1]  # (owner, repo)

    def get_repo_metadata(self, owner, repo):
        url = f"https://api.github.com/repos/{owner}/{repo}"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error fetching metadata for {owner}/{repo}: {response.status_code}, {response.json()}")
            return None

    def calculate_repo_health(self, repo_full_name):
        # Get recent commits (last 30 days)
        commits_url = f"https://api.github.com/repos/{repo_full_name}/commits"
        commits_response = requests.get(commits_url, headers=self.headers)
        recent_commits = 0
        if commits_response.status_code == 200:
            commits = commits_response.json()
            thirty_days_ago = datetime.now(timezone.utc).timestamp() - (30 * 24 * 60 * 60)
            recent_commits = sum(1 for commit in commits if datetime.strptime(commit['commit']['author']['date'], '%Y-%m-%dT%H:%M:%SZ').timestamp() > thirty_days_ago)

        # Get issues and their resolution time
        issues_url = f"https://api.github.com/repos/{repo_full_name}/issues?state=closed"
        issues_response = requests.get(issues_url, headers=self.headers)
        avg_resolution_time = 0
        if issues_response.status_code == 200:
            issues = issues_response.json()
            if issues:
                resolution_times = []
                for issue in issues:
                    if issue.get('closed_at'):
                        created = datetime.strptime(issue['created_at'], '%Y-%m-%dT%H:%M:%SZ')
                        closed = datetime.strptime(issue['closed_at'], '%Y-%m-%dT%H:%M:%SZ')
                        resolution_times.append((closed - created).total_seconds() / 3600)  # in hours
                avg_resolution_time = sum(resolution_times) / len(resolution_times) if resolution_times else 0

        # Get maintainer responsiveness (time to first response on issues)
        issues_url = f"https://api.github.com/repos/{repo_full_name}/issues?state=all"
        issues_response = requests.get(issues_url, headers=self.headers)
        avg_response_time = 0
        if issues_response.status_code == 200:
            issues = issues_response.json()
            if issues:
                response_times = []
                for issue in issues:
                    comments_url = f"https://api.github.com/repos/{repo_full_name}/issues/{issue['number']}/comments"
                    comments_response = requests.get(comments_url, headers=self.headers)
                    if comments_response.status_code == 200:
                        comments = comments_response.json()
                        if comments:
                            first_comment = min(comments, key=lambda x: x['created_at'])
                            created = datetime.strptime(issue['created_at'], '%Y-%m-%dT%H:%M:%SZ')
                            first_response = datetime.strptime(first_comment['created_at'], '%Y-%m-%dT%H:%M:%SZ')
                            response_times.append((first_response - created).total_seconds() / 3600)  # in hours
                avg_response_time = sum(response_times) / len(response_times) if response_times else 0

        # Calculate health score (0-100)
        # Weights: recent commits (40%), issue resolution (30%), maintainer responsiveness (30%)
        commit_score = min(recent_commits * 10, 40)  # Max 40 points for commits
        resolution_score = max(30 - (avg_resolution_time / 24), 0)  # Max 30 points for resolution time
        response_score = max(30 - (avg_response_time / 24), 0)  # Max 30 points for response time
        
        health_score = commit_score + resolution_score + response_score
        
        return {
            "health_score": round(health_score, 1),
            "metrics": {
                "recent_commits": recent_commits,
                "avg_issue_resolution_time": round(avg_resolution_time, 1),
                "avg_maintainer_response_time": round(avg_response_time, 1)
            }
        }

    def fetch_additional_repo_data(self, repo_full_name):
        print(f"\nFetching data for {repo_full_name}")
        
        try:
            # Get repository data in a single API call
            repo_url = f"https://api.github.com/repos/{repo_full_name}"
            repo_response = requests.get(repo_url, headers=self.headers)
            if repo_response.status_code != 200:
                print(f"WARNING: Failed to fetch repository data: {repo_response.status_code}")
                return 0, 0, {"health_score": 0, "metrics": {"recent_commits": 0, "avg_issue_resolution_time": 0, "avg_maintainer_response_time": 0}}
            
            repo_data = repo_response.json()
            forks_count = repo_data.get("forks_count", 0)
            
            # Get recent activity data in parallel
            print("Calculating repository health metrics...")
            
            # Calculate commit activity (last 30 days)
            commits_url = f"{repo_url}/commits"
            commits_response = requests.get(commits_url, headers=self.headers, params={"since": datetime.now(timezone.utc) - timedelta(days=30)})
            recent_commits = len(commits_response.json()) if commits_response.status_code == 200 else 0
            print(f"Recent commits: {recent_commits}")
            
            # Get open issues count
            open_issues_count = repo_data.get("open_issues_count", 0)
            print(f"Open issues: {open_issues_count}")
            
            # Get pull requests count (only open PRs)
            pulls_url = f"{repo_url}/pulls"
            pulls_response = requests.get(pulls_url, headers=self.headers, params={"state": "open"})
            pr_count = len(pulls_response.json()) if pulls_response.status_code == 200 else 0
            print(f"Open PRs: {pr_count}")
            
            # Calculate activity score
            activity_score = recent_commits + open_issues_count + pr_count
            
            # Calculate health score
            commit_score = min(recent_commits * 10, 40)  # Max 40 points for commits
            issue_ratio = open_issues_count / (repo_data.get("stargazers_count", 1) + 1)  # Issues relative to project size
            issue_score = max(30 - (issue_ratio * 100), 0)  # Max 30 points for issue management
            pr_ratio = pr_count / (repo_data.get("stargazers_count", 1) + 1)  # PRs relative to project size
            pr_score = max(30 - (pr_ratio * 100), 0)  # Max 30 points for PR management
            
            health_score = commit_score + issue_score + pr_score
            
            health_data = {
                "health_score": round(health_score, 1),
                "metrics": {
                    "recent_commits": recent_commits,
                    "open_issues": open_issues_count,
                    "open_prs": pr_count,
                    "commit_score": round(commit_score, 1),
                    "issue_score": round(issue_score, 1),
                    "pr_score": round(pr_score, 1)
                }
            }
            
            print(f"Health Score: {health_score:.1f}/100")
            print(f"Finished processing {repo_full_name}\n")
            
            return forks_count, activity_score, health_data
            
        except Exception as e:
            print(f"ERROR: Failed to process {repo_full_name}: {str(e)}")
            return 0, 0, {"health_score": 0, "metrics": {"recent_commits": 0, "avg_issue_resolution_time": 0, "avg_maintainer_response_time": 0}}

    def search_repos_by_topic(self, topic):
        encoded_query = quote(topic)
        url = f"https://api.github.com/search/repositories?q={encoded_query}&sort=stars&order=desc"
        print(f"\nSearching GitHub for: {topic}")
        response = requests.get(url, headers=self.headers)

        if response.status_code == 200:
            data = response.json()
            repos = data.get("items", [])
            total_count = data.get("total_count", 0)
            print(f"Found {total_count} total repositories")
            print(f"Processing top {len(repos)} repositories by stars\n")
            return repos
        else:
            print(f"ERROR: Failed to fetch data for topic '{topic}'. Status Code: {response.status_code}")
            return []

    def get_unique_languages(self, repos):
        languages = set()
        for repo in repos:
            if repo.get("language"):
                languages.add(repo["language"])
        return sorted(list(languages))

class RepoProcessor:
    def preprocess_metadata(self, data):
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

class SemanticAnalyzer:
    def __init__(self, model_name="sentence-transformers/all-MiniLM-L6-v2"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)

    def get_embedding(self, text):
        inputs = self.tokenizer(text, return_tensors="pt", padding=True, truncation=True)
        with torch.no_grad():
            embeddings = self.model(**inputs).last_hidden_state.mean(dim=1)
        return embeddings

    def compute_similarity(self, text1, text2):

        emb1 = self.get_embedding(text1)
        emb2 = self.get_embedding(text2)
        return util.pytorch_cos_sim(emb1, emb2).item()

class KeywordExtractor:
    def __init__(self):
        self.kw_model = KeyBERT()

    def extract_keywords(self, text, top_n=3):
        keywords = self.kw_model.extract_keywords(
            text,
            keyphrase_ngram_range=(1, 2),
            stop_words='english',
            top_n=top_n
        )
        return [kw[0] for kw in keywords]

class RelatedRepoFinder:
    def __init__(self, github_api, repo_processor, semantic_analyzer, keyword_extractor):
        self.github_api = github_api
        self.repo_processor = repo_processor
        self.semantic_analyzer = semantic_analyzer
        self.keyword_extractor = keyword_extractor

    def build_query_from_repo(self, owner, repo):
        metadata = self.github_api.get_repo_metadata(owner, repo)
        if not metadata:
            return None

        description = metadata.get("description", "")
        language = metadata.get("language", "")
        topics = metadata.get("topics", [])

        top_keywords = self.keyword_extractor.extract_keywords(description, top_n=1) if description else []

        if top_keywords:
            search_terms = " ".join(top_keywords)
        else:
            search_terms = ""

        base_query = f"{search_terms} in:name,description,topics"
        if language:
            base_query += f" language:{language}"

        if len(base_query) > 256:
            fixed_part = f" in:name,description,topics"
            if language:
                fixed_part += f" language:{language}"
            allowed_length = 256 - len(fixed_part) - 1
            truncated_search_terms = search_terms[:allowed_length]
            base_query = f"{truncated_search_terms}{fixed_part}"

        print("The link query:", base_query)
        return base_query

    def rank_repositories(self, repos, topic, selected_languages=None):
        ranked_repos = []
        total = len(repos)
        print(f"\nRanking {total} repositories...")
        
        for idx, repo_data in enumerate(repos, 1):
            print(f"\nProcessing repository {idx}/{total}")
            
            # Skip if language filter is active and repo doesn't match
            if selected_languages and repo_data.get("language") not in selected_languages:
                print(f"Skipping {repo_data['full_name']} - language not in filter")
                continue

            repo_full_name = repo_data["full_name"]
            print(f"Repository: {repo_full_name}")
            
            forks_count, activity_score, health_data = self.github_api.fetch_additional_repo_data(repo_full_name)
            description = repo_data.get("description", "")
            language = repo_data.get("language", "")
            stars = repo_data["stargazers_count"]

            if not description:
                topics = repo_data.get("topics", [])
                if topics:
                    description = " ".join(topics)
                    print(f"Using topics as description: {description}")
                else:
                    description = repo_data.get("name", "")
                    print(f"Using name as description: {description}")
            
            # Compute relevance score using SBERT
            print("Computing relevance score...")
            topic_similarity = self.semantic_analyzer.compute_similarity(topic, description)
            language_match = 1 if topic.lower() in (language or "").lower() else 0
            relevance_score = (topic_similarity * 0.8) + (language_match * 0.2)
            print(f"Relevance score: {relevance_score:.2f}")

            # Compute final weighted score
            final_score = (relevance_score * 0.4) + (stars * 0.2) + (forks_count * 0.15) + (activity_score * 0.15) + (health_data["health_score"] * 0.1)
            print(f"Final score: {final_score:.2f}")

            ranked_repos.append({
                "name": repo_data["name"],
                "owner": repo_data["owner"]["login"],
                "url": repo_data["html_url"],
                "stars": stars,
                "forks": forks_count,
                "activity": activity_score,
                "relevance": relevance_score,
                "final_score": final_score,
                "language": language,
                "health": health_data,
                "description": description,
                "topics": repo_data.get("topics", [])
            })

        # Sort by final score
        ranked_repos = sorted(ranked_repos, key=lambda x: x["final_score"], reverse=True)
        print(f"\nFinished ranking {len(ranked_repos)} repositories")
        return ranked_repos

    def find_related_repositories(self, github_url):
        owner, repo = self.github_api.extract_repo_details(github_url)
        query_text = self.build_query_from_repo(owner, repo)

        if not query_text:
            print("Could not build query.")
            return []

        repos = self.github_api.search_repos_by_topic(query_text)
        if not repos:
            print("No repos found for the generated query.")
            return []

        return self.rank_repositories(repos, query_text)

# --- Main Execution ---
if __name__ == "__main__":
    github_token = os.getenv('GITHUB_TOKEN', '')  # Get token from environment variable
    github_api = GitHubAPI(token=github_token)
    repo_processor = RepoProcessor()
    semantic_analyzer = SemanticAnalyzer()
    keyword_extractor = KeywordExtractor()
    related_repo_finder = RelatedRepoFinder(github_api, repo_processor, semantic_analyzer, keyword_extractor)

    github_api.check_rate_limit()
    # Example of Part 3 - search by URL 
    target_repo_url = "https://github.com/weiaicunzai/awesome-image-classification"
    related_repositories = related_repo_finder.find_related_repositories(target_repo_url)

    print("\nTop 10 related repositories:")
    for repo in related_repositories:
        print(json.dumps(repo, indent=2))

    # Example of Part 1  - metadata
    owner, repo_name = github_api.extract_repo_details(target_repo_url)
    metadata = github_api.get_repo_metadata(owner, repo_name)
    if metadata:
        structured_metadata = repo_processor.preprocess_metadata(metadata)
        print("\nMetadata for the target repository:")
        print(json.dumps(structured_metadata, indent=4))

    # Example of Part 2 functionality (searching by a topic)
    topic = "Machine learning projects"
    searched_repos = github_api.search_repos_by_topic(topic)
    if searched_repos:
        ranked_searched_repos = related_repo_finder.rank_repositories(searched_repos, topic)
        print(f"\nTop 5 repositories related to '{topic}':")
        for repo in ranked_searched_repos[:5]:
            print(json.dumps(repo, indent=2))