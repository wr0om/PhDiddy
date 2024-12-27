import os
import requests
from bs4 import BeautifulSoup

# Function to get researcher names from Technion's webpage
def get_researcher_names(url):
    response = requests.get(url, verify=False)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    links = soup.find_all('a', class_='card-link')
    researcher_names = [link.get('href').rstrip('/').split('/')[-1] for link in links if link.get('href')]
    return researcher_names

# Semantic Scholar API functions
def search_authors_by_name(author_name, api_key=None):
    url = "https://api.semanticscholar.org/graph/v1/author/search"
    params = {"query": author_name}
    headers = {"x-api-key": api_key} if api_key else {}
    response = requests.get(url, params=params, headers=headers)
    response.raise_for_status()
    return response.json()

def get_author_details(author_id, api_key=None):
    url = f"https://api.semanticscholar.org/graph/v1/author/{author_id}"
    params = {"fields": "name,paperCount"}
    headers = {"x-api-key": api_key} if api_key else {}
    response = requests.get(url, params=params, headers=headers)
    response.raise_for_status()
    return response.json()

def find_author_with_most_publications(author_name, api_key=None):
    search_results = search_authors_by_name(author_name, api_key)
    authors = search_results.get("data", [])
    if not authors:
        raise ValueError(f"No authors found with name '{author_name}'.")
    author_details = [get_author_details(author["authorId"], api_key) for author in authors]
    return max(author_details, key=lambda x: x.get("paperCount", 0))

def get_recent_papers(author_id, api_key=None, limit=20):
    url = f"https://api.semanticscholar.org/graph/v1/author/{author_id}/papers"
    params = {"fields": "title,year,abstract", "limit": limit, "sort": "year:desc"}
    headers = {"x-api-key": api_key} if api_key else {}
    response = requests.get(url, params=params, headers=headers)
    response.raise_for_status()
    return response.json().get("data", [])

# Function to save researcher data to a file
def save_researcher_data(name, papers, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, f"{name}.txt")
    with open(filepath, "w", encoding="utf-8") as f:
        for paper in papers:
            f.write(f"{paper['year']}: {paper['title']}\n")
            f.write(f"Abstract: {paper.get('abstract', 'No abstract available')}\n\n")

# Main flow to create database of researchers
def create_researcher_database(researcher_url, api_key=None, output_dir="researchers_db"):
    researcher_names = get_researcher_names(researcher_url)
    for researcher in researcher_names:
        try:
            author = find_author_with_most_publications(researcher, api_key)
            print(f"Processing {author['name']} (ID: {author['authorId']})")
            recent_papers = get_recent_papers(author["authorId"], api_key)
            save_researcher_data(author['name'], recent_papers, output_dir)
        except ValueError as e:
            print(f"Skipping {researcher}: {e}")
        except requests.HTTPError as e:
            print(f"HTTP error occurred for {researcher}: {e}")
        except Exception as e:
            print(f"An error occurred for {researcher}: {e}")