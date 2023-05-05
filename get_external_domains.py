import requests
from urllib.parse import urlparse
from bs4 import BeautifulSoup

def get_all_external_domains(url):
    """Gets all the external domains in the HTML document at the specified URL.

    Args:
        url: The URL of the HTML document.

    Returns:
        A list of the external domains.
    """

    # Parse the URL and get the domain name.
    domain = urlparse(url).netloc

    # Make a request to the website.
    response = requests.get(url)

    # Check if request was successful.
    if response.status_code == 200:
        # Parse the HTML with BeautifulSoup.
        soup = BeautifulSoup(response.content, 'html.parser')

        # Find all links in the HTML, including links in CSS and JavaScript.
        links = soup.find_all(['a', 'link', 'script', 'img', 'video', 'audio', 'source'])

        # Use a list comprehension to create a list of all the external domains.
        external_domains = [
            urlparse(link.get('href', link.get('src'))).netloc
            for link in links
            if link.get('href') is not None
            and (link.get('href').startswith('http://') or link.get('href').startswith('https://'))
            and urlparse(link.get('href')).netloc != domain
        ]

        # Remove duplicate domains from the list.
        external_domains = list(set(external_domains))

        return sorted(external_domains)
    else:
        return None


# if __name__ == "__main__":
    # Get the external domains for the Google homepage.
#     external_domains = get_all_external_domains("https://www.google.com")

    # Print the external domains.
#     print(external_domains)
