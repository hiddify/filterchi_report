import requests
from urllib.parse import urlparse
from bs4 import BeautifulSoup

def get_all_external_domains(url):
    # Parse the URL and get the domain name
    domain = urlparse(url).netloc
    
    # Make a request to the website
    response = requests.get(url)
    
    # Check if request was successful
    if response.status_code == 200:
        # Parse the HTML with BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find all links in the HTML, including links in CSS and JavaScript
        links = soup.find_all(['a', 'link', 'script', 'img', 'video', 'audio', 'source'])
        
        # Initialize a list to store external domains
        external_domains = []
        
        # Loop through links to check for external domains
        for link in links:
            # Get the src or href attribute of the link
            if link.name == 'a':
                href = link.get('href')
            else:
                href = link.get('src')
            
            # Check if the attribute is not empty and starts with http or https
            if href is not None and (href.startswith('http://') or href.startswith('https://')):
                # Parse the URL of the link and get the domain name
                link_domain = urlparse(href).netloc
                
                # Check if the domain name of the link is different from the original domain
                if link_domain != domain:
                    # Add the external domain to the list
                    external_domains.append(link_domain)
        
        # Remove duplicate domains from the list
        external_domains = list(set(external_domains))
        
        # Return the list of external domains
        return external_domains
    else:
        # Return None if request was not successful
        return None