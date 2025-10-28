import re
from urllib.parse import urljoin, urldefrag, urlparse
from bs4 import BeautifulSoup
import lxml

DO_NOT_ENTER = set()
VISITED = set()
COMMON_WORDS = dict()
SUBDOMAINS = dict()
LONGEST_PAGE = ('Link', 0)

def scraper(url, resp):
    # have a do not crawl list
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]
    # check if it is NOT in do not crawl list
        # if it isn't in do not crawl, tokenize and begin analytics
    # call analytics functions

def extract_next_links(url, resp):
    links = []
    
    try:
        if resp.status != 200 or is_valid(url) == False or resp.raw_response is None:
            return links
        # normalized_url = normalize_url(url)
        
        # Normalize URL
        # Check/add to unique pages 
        
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


# HELPER FUNCTIONS:
# 4 analytics functions
def commonWordsWrite(): #writes the 50 most common words along with their word counts
    return
def longestPageCheck(url, lengthOfPage): #checks if url is the new longest page
    return
def longestPageWrite(): #writes longest page's url and token count to a file
    return
def subdomainUpdate(url): #updates whenever a subdomain is visited
    return


def subdomainWrite(): #writes subdomains visited to a file
    return
def uniqueWrite(): #writes the amount of unique urls visited to a file
    return


def tokenize(resp): #tokenizer function, ignores anything that is not alphanumeric
    return
def computeWordFrequencies(tokenList): #counts the common words --> useful for the common word file
    return
def wordCountCheck(resp): #check if the given site has too little or too much information
    return





trap_keywords = [
    'ical=', 'outlook-ical', 'eventdisplay=past', 'tribe-bar-date', 'action=', 'share=', 'swiki',
    'calendar', 'event', 'events', '/?page=', '/?year=', '/?month=', '/?day=', '/?view=archive',
    '/?sort=', 'sessionid=', 'utm_', 'replytocom=', '/html_oopsc/', '/risc/v063/html_oopsc/a\\d+\\.html',
    '/doku', '/files/', '/papers/', '/publications/', '/pub/', 'wp-login.php', '?do=edit', '?do=diff','?rev=',
    '/~eppstein/', '/covid19/' , '/doku', 'seminar-series', 'doku.php', 'seminarseries' , 'department-seminars',
    '/Nanda', '/seminar'
    ]
    
stop_words = [
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", 
    "any", "are", "aren", "t", "as", "at", "be", "because", "been", "before", "being", 
    "below", "between", "both", "but", "by", "can", "cannot", "could", "couldn", "did", "didn", 
    "do", "does", "doesn", "doing", "don", "down", "during", "each", "few", "for", "from", "further", "had", 
    "hadn", "has", "hasn", "have", "haven", "having", "he", "d", "ll", "s", "her", "here", "hers", "herself", 
    "him", "himself", "his", "how", "i", "m", "ve", "if", "in", "into", "is", "isn", "it", "its", "itself", 
    "let", "me", "more", "most", "mustn", "my", "myself", "no", "nor", "not", "of", "off", "on", "once", 
    "only", "or", "other", "ought", "our", "ours", "ourselves", "out", "over", "own", "same", "shan", 
    "she", "should", "shouldn", "so", "some", "such", "than", "that", "the", "their", "theirs", "them", 
    "themselves", "then", "there", "these", "they", "re", "ve", "this", "those", "through", "to", "too", 
    "under", "until", "up", "very", "was", "wasn", "we", "were", "weren", "what", "when", "where", "which", 
    "while", "who", "whom", "why", "with", "won", "would", "wouldn", "you", "your", "yours", "yourself", "yourselves"
]
