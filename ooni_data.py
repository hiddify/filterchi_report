import requests
from bs4 import BeautifulSoup

def get_ooni_data(offset=0, limit=100):
    url = f"https://api.ooni.io/api/v1/measurements?probe_cc=IR&confirmed=true&offset={offset}&limit={limit}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        return None



def get_subdomains(domain):
    subdomains = []
    url = f"https://crt.sh/?q={domain}"
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        subdomain_elements = soup.select("tr td:nth-child(5)")
        for element in subdomain_elements:
            subdomain = element.text.strip().rstrip(".")
            subdomains.append(subdomain)
    return subdomains




ooni_data = get_ooni_data(None, 0, 10)
while (ooni_data is not None):
    data = ooni_data.get("results");
    for item in data:
        domain = item.get("input").split("://",2)[1][:-1];
        #print(domain)
        subdomains = get_subdomains(domain)
        unique_set = set(subdomains)
        subdomains = list(unique_set)
        for subdomain in subdomains:
            with open(f"{domain}.txt", "a") as f:
                f.writelines(f"{subdomain} \n")
        
        next_link = ooni_data.get("metadata").get("next_url")
        ooni_data =get_ooni_data(next_link)
else:
    print("Failed to retrieve data.")