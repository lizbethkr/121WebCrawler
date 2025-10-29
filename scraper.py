import re
import gc
import os
from urllib.parse import urljoin, urldefrag, urlparse
from bs4 import BeautifulSoup
from lxml import html

os.makedirs('Report', exist_ok=True)

DO_NOT_ENTER = set()
VISITED = set() #CHANGE ALL VISITED TO SEEN 
COMMON_WORDS = dict()
SUBDOMAINS = dict()
LONGEST_PAGE = ('', 0)

def scraper(url, resp):
    global DO_NOT_ENTER

    links = extract_next_links(url, resp)
    valids = [link for link in links if is_valid(link)]

    if resp.status == 200 and url not in DO_NOT_ENTER:
        VISITED.add(url)
        subdomains(url)

        tokens = tokenize(resp)
        if tokens:
            confirm_longest_page(url, len(tokens))
            word_freq(tokens)


    if len(VISITED) % 50 == 0:
        common_words_file()
        longest_page_file()
        subdomain_write()
        unique_urls_write()
        print(f"[WRITE UPDATE] Processed {len(VISITED)} pages")
    return valids

def extract_next_links(url, resp):
    """ Take a url and it's HTTP response. 
        Return a set of valid links found on the page, so it can be crawled.
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content
    """
    links = set()

    # log urls without 200 response (okay) and return empty set
    if resp.status != 200 or resp.raw_response is None:
        DO_NOT_ENTER.add(url)
        print(f'Skip {url} - HTTP: {resp.status}')
        return list(links)

    # check for non-HTML pages (pdf, css, js, etc.)
    page_type = resp.raw_response.headers.get('Content-Type', '').lower()
    if 'text/html' not in page_type:
        DO_NOT_ENTER.add(url)
        return list(links)

    # Avoid urls with too little/much info
    if word_count_check(resp):
        DO_NOT_ENTER.add(url)
        return list(links)

    # Already Seen, ignore
    if url in VISITED:
        print(f'Seen: {url}')
        return list(links)

    # Ensure url contains text, not binary
    try:
        decoded_html = resp.raw_response.content.decode('utf-8', errors='replace')
    except Exception as e:
        DO_NOT_ENTER.add(url)
        return list(links)

    # Add url to visited and update subdomains
    VISITED.add(url)
    subdomains(url)

    # Retrieve links without fragments and complete checks to ensure validity
    try:
        soup = BeautifulSoup(decoded_html, 'lxml')
        for tag in soup.find_all('a', href=True):
            og_url= urljoin(url, tag['href'])
            clean_url, _ = urldefrag(og_url)
            # check validity
            if is_valid(clean_url):
                links.add(clean_url)
    except Exception as e:
        print(f"Error extracting links from {url}: {e}")
    finally: # memory
        if 'soup' in locals():
            del soup
    if 'decoded_html' in locals():
        del decoded_html
    gc.collect()

    return list(links)


def is_valid(url):
    """ Decide whether to crawl this url (True) or not (False) """
    global DO_NOT_ENTER
    try:
        parsed = urlparse(url)
        clean_url, _ = urldefrag(url)
        domain = parsed.netloc.lower()

        # print(f"[DEBUG] Testing URL: {url}")
        # print(f"[DEBUG] Domain: '{domain}'")
        # print(f"[DEBUG] Clean URL: {clean_url}")

        if clean_url in DO_NOT_ENTER or clean_url in VISITED:
            # print(f"[DEBUG] REJECTED: Already in DO_NOT_ENTER or VISITED")
            return False

        if parsed.scheme not in set(["http", "https"]):
            # print(f"[DEBUG] REJECTED: Invalid scheme: {parsed.scheme}")
            return False

        allowed_domains = ["ics.uci.edu", "cs.uci.edu", "informatics.uci.edu", "stat.uci.edu"]
        domain_check_results = [domain.endswith(allowed_domain) for allowed_domain in
                                allowed_domains]

        # print(f"[DEBUG] Domain check results: {domain_check_results}")
        # print(f"[DEBUG] Allowed domains: {allowed_domains}")

        if not any(domain_check_results):
            # print(f"[DEBUG] REJECTED: Domain not in allowed list")
            return False

        trap_detected = any(keyword in clean_url.lower() for keyword in trap_keywords)
        if trap_detected:
            # print(f"[DEBUG] REJECTED: Trap keyword detected")
            DO_NOT_ENTER.add(clean_url)
            return False

        file_match = re.search(
            r"\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())

        if file_match:
            # print(f"[DEBUG] REJECTED: File extension detected: {file_match.group()}")
            return False

        # print(f"[DEBUG] ACCEPTED: URL is valid")
        return True

    except Exception as error:
        print(f"[IS_VALID ERROR] Failed to validate {url}: {error}")
        DO_NOT_ENTER.add(url)
        return False

# HELPER FUNCTIONS:
# 4 analytics functions + their helpers
def unique_urls_write(): #done/untested
    """ Q1:Writes the total # of unique URLs successfully crawled to a file """
    with open("Report/unique_urls.txt", "w") as unique_urls:
        unique_urls.write(f"Unique Pages: {len(VISITED)}") #Unique Pages: 1247
    return


def confirm_longest_page(url, pageLength): #done/untested
    '''Q2: Check if url is the new longest page and update LONGEST_PAGE.'''
    global LONGEST_PAGE
    if LONGEST_PAGE[1] < pageLength:
        LONGEST_PAGE = (url, pageLength)
    return


def longest_page_file(): #done/untested
    '''Q2: Write the longest page's url and # of words.'''
    global LONGEST_PAGE
    with open('Report/LongestPage.txt', 'w') as txtfile:
        txtfile.write(f'Longest Page URL: {LONGEST_PAGE[0]} - {LONGEST_PAGE[1]}')


def common_words_file(): #done/untested
    '''Q3: Write 50 most common words and their frequency in entire set of pages crawled. '''
    global COMMON_WORDS
    # ignore english stop words
    with open('Report/CommonWords.txt', 'w') as txtfile:
        string = ""  # Initialize string variable
        for freq, item in enumerate(sorted(COMMON_WORDS.items(), key=lambda x: x[1], reverse=True)[:50]):
            string += f'{freq+1}, {item[0]} - {item[1]}\n'
        txtfile.write(string)  # Write the complete string

# def subdomains(url): #done/untested
#     '''Q4: Update list of subdomains (alphabetically), and # of unique pages in each.
#     List contents: Subdomain, Number of Unique Pages. '''
#     global SUBDOMAINS
#     # confirm if in UCI domain
#     if '.uci.edu' not in url:
#         return
#     # grab urls ending in .uci.edu
#     structure = r'https?://(.*)\.uci.edu'
#     subdomain_struct = re.search(structure,url).group(1).lower()
#     # ignore www.uci.edu main page, only want other subdomains
#     if subdomain_struct == 'www':
#         return
#     # create dict key
#     subdomain_key = subdomain_struct + '.uci.edu'
#     if subdomain_key in subdomain_struct:
#         subdomain_struct[subdomain_key] +=1
#     else:
#         subdomain_struct[subdomain_key] = 1
#     return

def subdomains(url):
    '''Q4: Update list of subdomains (alphabetically), and # of unique pages in each.'''
    global SUBDOMAINS
    # confirm if in UCI domain
    if '.uci.edu' not in url:
        return

    try:
        # grab urls ending in .uci.edu
        structure = r'https?://(.*)\.uci.edu'
        match = re.search(structure, url)
        if not match:
            return

        subdomain_name = match.group(1).lower()  # Renamed variable to avoid confusion
        # ignore www.uci.edu main page, only want other subdomains
        if subdomain_name == 'www':
            return
        # create dict key
        subdomain_key = subdomain_name + '.uci.edu'

        # FIXED: Use SUBDOMAINS dict, not the string variable
        if subdomain_key in SUBDOMAINS:
            SUBDOMAINS[subdomain_key] += 1
        else:
            SUBDOMAINS[subdomain_key] = 1
    except Exception as e:
        print(f"Error in subdomains for {url}: {e}")
    return


def subdomain_write(): #done/untested
    """ Q4 Writes what subdomains are visited in a file """
    with open("Report/subdomains.txt", "w") as subdomains:
        subdomains.write(f"Subdomain Number: {len(SUBDOMAINS)}\n") # Subdomain Number: 3
        subdomains.write("SubSubdomain, Number of Unique Pages Crawled in that Subdomain")
        for item in sorted(SUBDOMAINS):
            subdomains.write(f"{item}, {SUBDOMAINS[item]}") # cs.uci.edu, 25
    return
    
    
def tokenize(resp): #done/untested
    """ Extracts & filters alphanumeric tokens """
    try:
        tree = html.fromstring(resp.raw_response.content)
        text = tree.text_content()  
        
        tokens = re.findall(r'\b[a-zA-Z0-9]{3,}\b', text)
        token_list = [token.lower() for token in tokens]
        return token_list
    except (AttributeError, TypeError) as error:
        print(f"[TOKENIZER ERROR] {error}")
        return []
    return

    
def word_freq(token_list): #done/untested
#TODO: use counters instead of dict
    """ Counts word frequencies from token list """
    global COMMON_WORDS
    for token in token_list:
        if token not in stop_words and token.isalpha():
            if token not in COMMON_WORDS:
                COMMON_WORDS[token] = 1
            else:
                COMMON_WORDS[token] += 1


def word_count_check(resp): #done/untested
    """ Check if webpage has useable word count (100-100000) """
    word_count = len(tokenize(resp))

    if word_count < 100:
        print(f"[WORD COUNT] {word_count} < 100)")
        return True
    elif word_count > 100000:
        print(f"[WORD COUNT] {word_count} > 100000)")
        return True
    
    return False # ok to crawl

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
