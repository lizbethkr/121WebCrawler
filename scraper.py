import re
from urllib.parse import urljoin, urldefrag, urlparse
from bs4 import BeautifulSoup
import lxml


def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

def extract_next_links(url, resp):
    links = []
    
    try:
        if resp.status != 200 or is_valid(url) == False:
            return links
        soup = BeautifulSoup(resp.raw_response.content, 'lxml')
        # extract hyperlinks
        for tag in soup.find_all('a', href=True):
            link = tag['href']
            absolute_url = urljoin(url, tag['href'])
            clean_url, _ = urldefrag(absolute_url)
            links.append(clean_url)

    #Implement stats
    #dynamically update variables after scraping website
    #(most common words, unique pages, longest page, subdomains)
    except Exception as e:
        print(f"Error extracting links from {url}: {e}")
    # Implementation required.
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content
    
    return links

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    try:
        #TODO: Check for traps/infinite loops
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False
            
        domain = parsed.netloc.lower()
        if not (
            domain.endswith(".ics.uci.edu") or
            domain.endswith(".cs.uci.edu") or
            domain.endswith(".informatics.uci.edu") or
            domain.endswith(".stat.uci.edu")
        ):
            return False
            
        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())
    except TypeError:
        print ("TypeError for ", parsed)
        raise
