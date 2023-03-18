import csv
import datetime
import requests
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import re

# Using class objects to hold datas
class Domain:
    def __init__(self, name, isFilter, dateChecked, source, scheme = "null"):
        self.scheme = scheme
        self.name = name
        self.isFilter = isFilter
        self.dateChecked = dateChecked
        self.source = source


class FilterChi:

    def __init__(self, quantity):
        # a temporary list to hold checked main domains
        self.mainDomains = []
        # a temporary list to hold all domains and subdomains
        self.alldomains = []
        # a temporary dict to hold subdomains
        self.subdomains = {}
        # a list to help prevent duplications
        self.mainDomainsBackup = []
        # current url to get datas from ooni.io
        self.currentUrl = "https://api.ooni.io/api/v1/measurements?probe_cc=IR&confirmed=true&offset=0&limit=3"
        # retrieved metadatas
        self.results = ""
        # max quantity of the main domains
        self.quantity = quantity

    # a function to get things going
    def start(self):
        # a counter to keep track of domains and sub domains
        counter = 0
        while 1:
            # get the metadatas
            self.getMetaData()

            if len(self.results) == 0:
                print("There are no metadatas!")
                break
            else:
                # Extract main domains and add to list
                self.extractDomains()
                # Extract subdomains
                self.extractSubdomains()
                self.extractExternalSubdomains()
                # Add subdomains to the list
                self.addSubdomainsToList()
                # write the domains and subdomains details
                self.writeToCSV()
                print(f"------------\n{len(self.alldomains)} domains added to CSV file\n------------")
                # Reset the lists
                self.resetValues()

            counter += 3
            if (counter >= self.quantity):
                break

    def getMetaData(self):
        # retrieve the ooni data
        response = requests.get(self.currentUrl)
        if response.status_code == 200:
            jsonRes = response.json()
            # get the results 
            self.results = jsonRes.get("results")
            # get the next url
            self.currentUrl = jsonRes.get("metadata").get("next_url")
        else:
            print(f"Connection error occurred during get MetaData from OONI\nStatus Code: {response.status_code}")

    def extractDomains(self):
        for row in self.results:
            # get the website url
            fullUrl = row.get("input").split("://",2)
            # get the scheme -> http:// or https://
            scheme = fullUrl[0] + "://"
            # get domain and remove the www. (because it doesn't work when
            #  you try to find subdomains using crt.sh)
            fullDomain = fullUrl[1]
            name = fullDomain[:fullDomain.find("/")].replace("www.", "")
            # is it filtered or not
            isFilter = str(row.get("confirmed")).lower()
            # get the date
            dateChecked = row.get("measurement_start_time")[:10]
            # create a domain object
            domain =  Domain(name, isFilter, dateChecked, "ooni.com", scheme)
            # check if it's unique
            if domain.name not in self.mainDomainsBackup: 
                # append it to the list
                self.mainDomains.append(domain)
                self.mainDomainsBackup.append(domain.name)
                self.alldomains.append(domain)
                # print the main domain
                print(f"{domain.name} added!")


    def extractSubdomains(self):
        for mainDomain in self.mainDomains:
            subdomain = ""
            try: 
                url = f"https://crt.sh/?q={mainDomain.name}"
                response = requests.get(url, timeout=30)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, "html.parser")
                    subdomain_elements = soup.select("tr td:nth-child(5)")
                    for element in subdomain_elements:
                        subdomain = element.text.strip().rstrip(".")
                        self.subdomains[subdomain] = mainDomain
            except Exception as err:
                print(f"extractSubDomains Error: {mainDomain}: {err}")

    
    def extractExternalSubdomains(self):
        for mainDomain in self.mainDomains:
            # Make a request to the website
            try: 
                url = mainDomain.scheme + mainDomain.name
                response = requests.get(url, timeout=20)
                # Check if request was successful
                if response.status_code == 200:
                    # Parse the HTML with BeautifulSoup
                    soup = BeautifulSoup(response.content, 'html.parser')
                    # Find all links in the HTML, including links in CSS and JavaScript
                    links = soup.find_all(['a', 'link', 'script', 'img', 'video', 'audio', 'source'])
                    # Loop through links to check for external domains
                    for link in links:
                        # Get the src or href attribute of the link
                        if link.name == 'a' or link.name == 'link':
                            href = link.get('href')
                        else:
                            href = link.get('src')
                        # Skip link if it's None (Empty)
                        if href is None:
                            continue
                        # As you know "//*" links are external and "/*" are internal
                        # Skip link if it's internal link
                        # Something like "/assets/layout.css"
                        regex = re.compile(r'^/[-a-zA-Z0-9@:%._\+~#=]')
                        if regex.search(href):
                            continue

                        # Parse the URL of the link and get the domain name
                        link_domain = ''
                        if href.startswith('http://') or href.startswith('https://'):
                            link_domain = urlparse(href).netloc
                        elif href.startswith("//"):
                            # Extract domain even if something like "//www.domain.com/path"
                            if href.startswith('//www.'):
                                www_domain = urlparse(href).netloc
                                link_domain = www_domain.replace('www.','')
                            else:
                                # Remove "//" charachters from link
                                # After that we should have something like "fonts.googleapis.com" (it doesn't have "//" prefix)
                                link_domain = href.removeprefix("//")
                        elif href.startswith('www.'):
                            link_domain = href.replace('www','')
                        
                        # Check link_domain isn't empty and check if the domain name of the link is different from the original domain
                        if link_domain.strip() != "":
                            if link_domain != mainDomain.name:
                                # Add the external domain to the list
                                self.subdomains[link_domain] = mainDomain


            except Exception as err: 
                print(f"extractExternalSubdomains Error: {url}: {err}")




    def addSubdomainsToList(self):
        # Loop through dict
        for subdomain, mainDomain in self.subdomains.items():
            # add it to the domains list if it's unique
            if self.isUnique(subdomain):
                # Check if it's filtered
                filtered = str(self.isFiltered(mainDomain.name, subdomain)).lower()
                # Create Domain object
                subdomainObject = Domain(subdomain, filtered, mainDomain.dateChecked, mainDomain.name)
                # Add it to list
                self.alldomains.append(subdomainObject)
        

    def isFiltered(self, domain, subdomain):
        # If subdomain is in root -> Filtered
        if domain in subdomain:
            return True
        # Check the subdomain in ooni.io
        try:
            res = requests.get("https://api.ooni.io/api/v1/measurements?" +
            f"domain={subdomain}&probe_cc=IR&limit=1", timeout=10)
            jsonRes = res.json()
            results = jsonRes.get("results")
            # Check if subdomain is blocked
            if len(results) > 0:
                if not results[0].get("confirmed"):
                    return False
        except Exception as err:
            print(f"isFiltered Error: {subdomain}: {err}")
        return True
                

    def writeToCSV(self):
        # check if the csv file is already created
        path = Path('./result.csv')
        if not path.is_file():
            # specify the header
            header = ["domain", "date", "filter", "source"]
            # open the csv file
            with open('result.csv', 'w', newline="") as f:
                writer = csv.writer(f)
                # write the header
                writer.writerow(header)
                # write multiple rows
                for domain in self.alldomains:
                    writer.writerow([domain.name, domain.dateChecked, domain.isFilter, domain.source])
        # file is already created just write the rows
        else:
            with open('result.csv', 'a', newline="") as f:
                writer = csv.writer(f)

                for domain in self.alldomains:
                    writer.writerow([domain.name, domain.dateChecked, domain.isFilter, domain.source])
            

    # a function to avoid duplicates
    def isUnique(self, domainName):
        isUnique = True
        for i in self.alldomains:
            if domainName == i.name:
                isUnique = False
                break
        return isUnique
    
    def resetValues(self):
        self.mainDomains = []
        self.alldomains = []
        self.subdomains = {}


if __name__ == "__main__":
    # specify the quantity of the main domains (a main domian may contains subdomains)
    quantity = int(input("How many domains do you wanna check? (choose a num divisible by 3): "))
    filterchi = FilterChi(quantity)
    filterchi.start()
 
