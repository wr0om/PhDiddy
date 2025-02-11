import os
import requests
from bs4 import BeautifulSoup

OUTPUT_DIR="researchers_db"

DDS_URL = 'https://dds.technion.ac.il/people/academic_staff/'
CS_URL = 'https://cs.technion.ac.il/research-areas/'
ECE_URL = 'https://ece.technion.ac.il/people/faculty-members/'

# Function to get researcher names from Technion's webpage
def get_researcher_names(faculty="dds"):
    if faculty == "dds":
        url = DDS_URL
    elif faculty == "cs":
        url = CS_URL
    elif faculty == "ece":
        url = ECE_URL
    else:
        raise ValueError(f"Faculty '{faculty}' is not supported.")

    response = requests.get(url, verify=False)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    if faculty == "dds":
        links = soup.find_all('a', class_='card-link')
        researcher_names = [link.get('href').rstrip('/').split('/')[-1] for link in links if link.get('href')]
        formatted_names = []
        for name in researcher_names:
            parts = name.split('-')
            formatted_name = ' '.join(part.capitalize() for part in parts)
            formatted_names.append(formatted_name)
        researcher_names = formatted_names
    elif faculty == "cs":
        divs = soup.find_all('div', class_='pp_bmenu_linksX ral')
        # for each div, get all a tags and extract the text in them
        researcher_names = [a.text for div in divs for a in div.find_all('a')]
    elif faculty == "ece":
        divs = soup.find_all('div', class_='sm-name')
        # get text from divs
        researcher_names = [div.text for div in divs]
        researcher_names = [name.replace('\xa0', ' ').strip() for name in researcher_names]
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
    formatted_name = name.lower().replace(' ', '_')
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, f"{formatted_name}.txt")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"Recent papers for {name}:\n\n")
        for paper in papers:
            f.write(f"{paper['year']}: {paper['title']}\n")
            f.write(f"Abstract: {paper.get('abstract', 'No abstract available')}\n\n")

# Main flow to create database of researchers
def create_researcher_database(api_key=None, output_dir="researchers_db", faculty="dds"):
    researcher_names = get_researcher_names(faculty)
    for researcher in researcher_names:
        try:
            author = find_author_with_most_publications(researcher, api_key)
            print(f"Processing {researcher} (ID: {author['authorId']})")
            recent_papers = get_recent_papers(author["authorId"], api_key)
            save_researcher_data(researcher, recent_papers, output_dir)
        except ValueError as e:
            print(f"Skipping {researcher}: {e}")
        except requests.HTTPError as e:
            print(f"HTTP error occurred for {researcher}: {e}")
        except Exception as e:
            print(f"An error occurred for {researcher}: {e}")

def get_researcher_names():
    # search for researcher names in the files in the output directory
    researcher_names = []
    for file in os.listdir(OUTPUT_DIR):
        if file.endswith(".txt"):
            # extract the name from the first line which is: "Recent papers for {name}:"
            with open(os.path.join(OUTPUT_DIR, file), "r", encoding="utf-8") as f:
                name = f.readline().split("for ")[1].strip(":\n")
                researcher_names.append(name)
                
    print(f"There were {len(researcher_names)} researcher names found")
    # save the names to a txt file, where each line is one name
    with open("researcher_names.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(researcher_names))

