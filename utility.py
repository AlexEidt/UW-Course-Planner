"""Common methods and Directory Names used by the other scripts"""

import logging, re, json, os
import urllib3 as URL
try:
    import requests
except Exception:
    raise Exception('Requests not installed. Try installing with "pip install requests"')
try:
    from bs4 import BeautifulSoup as Soup
except Exception:
    raise Exception('bs4 not installed. Try installing with "pip install beautifulsoup4"')

# -----------------------Directories----------------------- #
UW_Course_Catalogs = os.path.normpath(f'{os.getcwd()}/static/UW_Course_Catalogs')
UW_Time_Schedules = os.path.normpath(f'{os.getcwd()}/static/UW_Time_Schedules')
Organized_Time_Schedules = os.path.normpath(f'{UW_Time_Schedules}/Organized_Time_Schedules')
UW_Buildings = os.path.normpath(f'{os.getcwd()}/static/UW_Buildings')
Prerequisite_Trees = os.path.normpath(f'{os.getcwd()}/static/Prerequisite_Trees')
# --------------------------------------------------------- #


# -----------------------Logger----------------------- #
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(name)s -- %(asctime)s -- %(levelname)s : %(message)s')
handler = logging.FileHandler('Log.log')
handler.setLevel(logging.DEBUG)
handler.setFormatter(formatter)
logger.addHandler(handler)
# ---------------------------------------------------- #


# -----------------------Methods----------------------- #
def get_web_soup(website_link):
    """Creates BeautifulSoup for the given website link
    @params
        'website_link': The website to be scraped
    Returns
        BeautifulSoup object for the given link
    """
    website = URL.PoolManager()
    source = website.request('GET', website_link)
    return Soup(source.data, features='lxml')


def scan_transcript(course_dict, webapp=False):
    """Asks the user if their transcript should be scanned in to remove classes from the class
       tree that they've already taken.
    @params 
        'course_dict': The dictionary of courses scanned in from the campus selected by the user
    Returns
        List of courses taken from the transcript given
    """
    if not webapp:
        print('If you would like to scan in your transcript to eliminate searching courses you have')
        print("already taken, go to MyUW under 'Unofficial Transcript' and press CTRL+A and paste")
        print('your transcript into a text file in the same directory as this script.')
        transcript = input('Scan in Transcript? (y/n): ').lower()
        file_name = ''
        if 'y' in transcript.lower():
            check = False
            while not check:
                file_name = input('Transcript file name: ')
                check = file_name in os.listdir(os.getcwd())
        else:
            return []
    else:
        try:
            open('Transcript.txt')
        except Exception:
            return []
        else:
            file_name = 'Transcript.txt'
    courses_taken = []
    with open(file_name, mode='r') as transcript:
        for line in transcript:
            if 'CUMULATIVE CREDIT SUMMARY' in line:
                break
            match = re.search(r'([A-Z& ]+\s?\d{3})', line)
            if match:
                dropped = re.search(r'\d\.\d\s+W\d\s', line)
                line_data = match.group(0).replace(' ', '')
                if line_data in course_dict and not dropped:
                    courses_taken.append(line_data)
    return courses_taken


def check_connection(url='https://www.google.com/'):
    """Checks for a connection to the internet
    Returns
        True if internet is connected, False otherwise
    """
    try:
        requests.get(url)
    except Exception:
        return False
    else:
        return True