import requests
from bs4 import BeautifulSoup

session = requests.Session()

def get_ooni_data(url):
    response = session.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        return None

def get_subdomains(domain):
    subdomains = []
    url = f"https://crt.sh/?q={domain}"
    try:
        response = session.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            subdomain_elements = soup.select("tr td:nth-child(5)")
            for element in subdomain_elements:
                subdomain = element.text.strip().rstrip(".")
                subdomains.append(subdomain)
    except requests.exceptions.ConnectionError:
        print(f"Error: Could not connect to {url}")
    return subdomains

def process_ooni_data(url):
    ooni_data = get_ooni_data(url)
    if ooni_data is not None:
        data = ooni_data.get("results")
        for item in data:
            domain = item.get("input").split("://", 2)[1][:-1]
            subdomains = get_subdomains(domain)
            unique_set = set(subdomains)
            subdomains = list(unique_set)
            try:
                with open(f"{domain}.txt", "a") as f:
                    f.writelines(f"{subdomain} \n" for subdomain in subdomains)
            except FileNotFoundError:
                print(f"Error: Could not write to file {domain}.txt")
        next_link = ooni_data.get("metadata").get("next_url")
        if next_link is not None:
            process_ooni_data(next_link)
    else:
        print("Failed to retrieve data.")

url = "https://api.ooni.io/api/v1/measurements?probe_cc=IR&confirmed=true&offset=0&limit=10"
process_ooni_data(url)
