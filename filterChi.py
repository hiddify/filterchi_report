import csv
import requests
from pathlib import Path
from bs4 import BeautifulSoup


# Using class objects to hold datas
class Domain:
    def __init__(self, name, isFilter, dateChecked, source):
        self.name = name
        self.isFilter = str(isFilter).lower()
        self.dateChecked = dateChecked
        self.source = source

class FilterChi:

    def __init__(self, quantity):
        # a list to hold checked domains and subdomains
        self.domains = []
        # current url to get datas from ooni.io
        self.currentUrl = "https://api.ooni.io/api/v1/measurements?probe_cc=IR&confirmed=true&offset=0&limit=10"
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
                # extract the main domains and find the subdomains
                self.extractDomains()
                # write the domains and subdomains details
                self.writeToCSV()
                print(f"------------\n{len(self.domains)} domains added to CSV file\n------------")
                # Reset the domains list (doing this may cause duplications
                # but it will prevent ram crash)
                #self.domains = []

            counter += 10
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
            print("Connection error")

    def extractDomains(self):
        for row in self.results:
            # get the website url
            inputName = row.get("input").split("://",2)[1]
            # remove the http:// or https://
            name = inputName[:inputName.find("/")]
            # remove the www. (because it doesn't work when you try to find subdomains using crt.sh)
            name = name.replace("www.", "")
            # is it filtered or not
            isFilter = row.get("confirmed")
            # get the date
            dateChecked = row.get("measurement_start_time")[:10]
            source = "ooni.com"
            # create a domain object
            domain =  Domain(name, isFilter, dateChecked, source)
            # check if it's unique
            if self.isUnique(domain): 
                # append it to the list
                self.domains.append(domain)
                # print the main domain
                print(f"{domain.name} added!")
                # find the subdomains
                self.extractSubdomains(domain)

                

    def extractSubdomains(self, domain):
        # list to hold the subdomains
        subdomains = []
        url = f"https://crt.sh/?q={domain.name}"
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            subdomain_elements = soup.select("tr td:nth-child(5)")
            for element in subdomain_elements:
                subdomain = element.text.strip().rstrip(".")
                subdomains.append(subdomain)
        # dedup
        subdomains = list(set(subdomains))
        # add it to the domains list if it's unique
        for i in subdomains:
            subdomain = Domain(i, "unknown", domain.dateChecked, domain.name)
            if self.isUnique(subdomain):
                self.domains.append(subdomain)

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
                for domain in self.domains:
                    writer.writerow([domain.name, domain.dateChecked, domain.isFilter, domain.source])
        # file is already created just write the rows
        else:
            with open('result.csv', 'a', newline="") as f:
                writer = csv.writer(f)

                for domain in self.domains:
                    writer.writerow([domain.name, domain.dateChecked, domain.isFilter, domain.source])
            

    # a function to avoid duplicates
    def isUnique(self, domain):
        isUnique = True
        for i in self.domains:
            if domain.name == i.name:
                isUnique = False
                break
        return isUnique

if __name__ == "__main__":
    # specify the quantity of the main domains (a main domian may contains subdomains)
    quantity = int(input("How many domains do you wanna check? (choose a num divisible by 10)"))
    filterchi = FilterChi(quantity)
    filterchi.start()
 

