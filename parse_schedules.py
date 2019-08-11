"""
Parses UW Time Schedules for each UW Campus and creates a JSON file with all courses that are available in the
upcoming quarter of UW. If the courses for the upcoming quarter are not available, those from the current quarter
are used. The current quarter is calculated, no need to enter any information.
"""

import json
import math
import re
import calendar
import datetime
import logging
import time
import os
import requests as r
import urllib3 as URL
from datetime import datetime as dttime
from datetime import timedelta as td
from bs4 import BeautifulSoup as Soup
from tqdm import tqdm as AddProgressBar

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(name)s -- %(asctime)s -- %(levelname)s : %(message)s')
handler = logging.FileHandler('Log.log')
handler.setLevel(logging.DEBUG)
handler.setFormatter(formatter)
logger.addHandler(handler)


CAMPUSES = {
    'Seattle': 
        {
            'link': 'https://www.washington.edu/students/timeschd/',
            'schedule': 'https://www.washington.edu/students/timeschd/',
            'upper_case': True
        },
    'Bothell': 
        {
            'link': 'https://www.uwb.edu/registration/time/',
            'schedule': 'http://www.washington.edu/students/timeschd/B/',
            'upper_case': False
        },
    'Tacoma': 
        {
            'link': 'https://www.washington.edu/students/timeschd/T/',
            'schedule': 'https://www.washington.edu/students/timeschd/T/',
            'upper_case': True
        }
}

QUARTERS = {
    'AUT': 'WIN', 
    'WIN': 'SPR',
    'SPR': 'SUM',
    'SUM': 'AUT',
    'SUMA': 'AUT',
    'SUMB': 'AUT'
}

COURSE_KEYS = ['Section', 'Type', 'Days', 'Time', 'Building', 'Room Number']

TIME_SCHEDULES_DIR = 'UW_Time_Schedules'


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


def quarter_dates():
    """Parses UW's Academic Calendar to find current date ranges
       for every quarter
    Returns
        Dictionary with Quarter Abbreviation keys mapping to list of 
        datetime objects representing the range of dates for that quarter
    """
    year = dttime.now().year
    academic_year = ''
    if dttime.now().month >= 9:
        academic_year = str(year)[2:] + str(year + 1)[2:]
    else:
        academic_year = str(year - 1)[2:] + str(year)[2:]
    UW_Academic_Calendar = f'https://www.washington.edu/students/reg/{academic_year}cal.html'
    if r.get(UW_Academic_Calendar).ok:
        quarter_data = get_web_soup(UW_Academic_Calendar)
        table = quarter_data.find('table')
        index = 0
        temp = []
        start_end = {}
        month_names = {m: n for n, m in enumerate(calendar.month_name)}
        for date_range in table.find_all('td'):
            text = date_range.text
            if '-' not in text and re.search(r'[A-Z][a-z]+ \d+, \d+', text) and text:
                temp.append(text.replace(',', '', 1))
                if len(temp) == 2:
                    datetimes = []
                    for date in temp:
                        month, day, year = date.split(' ')
                        datetimes.append(datetime.date(int(year), month_names[month], int(day)))
                    start_end[list(QUARTERS.keys())[math.floor(index / 2)]] = [d for d in datetimes]
                    temp.clear()
                index += 1
        return start_end
    logger.log(f'''Could not access UW Academic Calendar at {UW_Academic_Calendar}. 
                    HTTP Status Code: {r.get(UW_Academic_Calendar).status_code}''')
    return {}


def get_quarter():
    """Calculates the current quarter based on the current date
    Returns
        List representing the current quarter(s) 
        NOTE: Summer Quarter has two terms, A and B
    """
    # [Q] Quarter for [Q] Quarter and [D] Dates in Quarter Ranges if 
    # today's date is in the range of that Quarters dates
    date_range = quarter_dates()
    current_quarters = [q for q, d in date_range.items() if d[0] < datetime.date.today() < d[1]]
    if not current_quarters:
        range_ = []
        d = list(date_range.values())
        for i in range(len(QUARTERS) - 2):
            range_.append([d[i][0], (d[i + 1][0] if i < len(QUARTERS) - 3 else (d[0][0] + td(days=365))) - td(days=1)])
        return [q for q, d in zip(QUARTERS.keys(), range_) if d[0] < datetime.date.today() < d[1]]
    return current_quarters


def get_next_quarter():
    """Gets the upcoming quarter based on the current quarter
    Returns
        Upcoming Quarter as a String
    """
    return ''.join({QUARTERS[q] for q in get_quarter()})


def parse_departments(campus):
    """Finds all department schedule websites for the given campus
    @params:
        'campus': The campus to get schedules from
    """
    upcoming_quarter = get_next_quarter()
    current = get_quarter()
    current_quarter = ''.join(current) if 'SUM' not in current else 'SUM'
    if not CAMPUSES[campus]['upper_case']:
        upcoming_quarter = upcoming_quarter.lower()
        current_quarter = current_quarter.lower()
    upcoming_courses_link = '{}{}{}/'.format(CAMPUSES[campus]['link'], upcoming_quarter, dttime.now().year)
    current_courses_link = '{}{}{}/'.format(CAMPUSES[campus]['link'], current_quarter, dttime.now().year)
    courses_link = ''
    schedule_link = ''

    if r.get(upcoming_courses_link).ok:
        courses_link = '{}{}{}/'.format(CAMPUSES[campus]['schedule'], upcoming_quarter.upper(), dttime.now().year)
        schedule_link = upcoming_courses_link
    elif r.get(current_courses_link).ok:
        courses_link = '{}{}{}/'.format(CAMPUSES[campus]['schedule'], current_quarter.upper(), dttime.now().year)
        schedule_link = current_courses_link
        logger.warning(f'Could not access upcoming course schedule for {upcoming_quarter}{dttime.now().year}')
    else:
        logger.critical('Could not access course schedules for current or upcoming quarters.')
        return None
    
    current_quarter = courses_link.split('/')[-2]
    campus_schedules = {}
    if campus == 'Bothell':
        dep_soup = re.compile(r'<h2>[A-Z][a-z]+ \d{4} Time Schedule</h2>').split(str(get_web_soup(schedule_link).html), 1)[-1]
        dep_soup = Soup(re.compile(r'<hr ?/>').split(dep_soup, 1)[-1], features='lxml')
    else:
        dep_soup = get_web_soup(schedule_link)
    anchor_tag = []
    for link in dep_soup.find_all('a'):
        department = link.get('href')
        if department:
            page = department.replace(courses_link, '', 1)
            if bool('.html' in page or courses_link in department) and '/' not in page:
                anchor_tag.append((department.split('#', 1)[0], link.text))
    list_items = dep_soup.find_all('li')
    for link, li in AddProgressBar(zip(anchor_tag, list_items), total=min((len(anchor_tag), len(list_items)))):
        dep_schedule = '{}{}'.format(courses_link, link[0].rsplit('/', 1)[-1])
        get_course = lambda x: x.rsplit('(', 1)[-1].split(')', 1)[0]
        if campus == 'Bothell':
            dep = get_course(li.get_text()).upper()
        else:
            dep = get_course(link[1])
        request = r.get(dep_schedule)
        if not re.search(r'[a-z]+', dep):
            if request.ok:
                new_dep = ''.join([s for s in dep if s.isupper()])
                if new_dep in campus_schedules:
                    campus_schedules[new_dep].append(parse_schedules(get_web_soup(dep_schedule)))
                else:
                    campus_schedules[new_dep] = [parse_schedules(get_web_soup(dep_schedule))]
            else:
                logger.critical(f'Could not access {dep_schedule}. HTTP Status Code: {request.status_code}')
    new_dict = {}
    for key, value in campus_schedules.items():
        try:
            old_key = list(campus_schedules[key][0].keys())[0]
        except Exception:
            pass
        else:
            new_key = re.sub(r'\d+', '', old_key)
            if len(value) > 1:
                courses_dict = {}
                for d in value:
                    courses_dict.update(d)
                value = courses_dict
            else:
                value = value[0]
            new_dict[new_key if new_key != key else key] = value
    with open(f'{TIME_SCHEDULES_DIR}\\{campus}_{current_quarter}.json', mode='w') as file:
        json.dump(new_dict, file, indent=4)


sln_split = re.compile(r'\d{5,}')
def parse_schedules(department):
    """Creates a dictionary of course, schedule pairings
    @params:
        'department': BeautifulSoup object of the department schedule website
    Returns
        Dictionary of course, schedule pairings
    """
    department_schedule = {}
    course_schedule = str(department.html).split('<br/>', 2)[-1]
    for course_options in course_schedule.split('<br/>'):
        options = Soup(course_options, features='lxml')
        course_data = []
        crs_listed = None
        for table, course in zip(options.find_all('table'), options.find_all('a')):
            crs = course.get('name')
            if crs:
                crs_listed = crs.upper()
            filter_empty = list(filter(('').__ne__, sln_split.split(table.text, 1)[-1].split(' ')))
            if not re.search(r'\n[A-Z&]+', ','.join(filter_empty[:-1])):
                if re.search(r'[\*,\[\]\.max\d/ \-]+', filter_empty[1]):
                    filter_empty[1] = 'LECT'
                if 'to,be,arranged' not in ','.join(filter_empty[i] for i in range(2, 5)).replace(' ', '') and filter_empty:
                    data = filter_empty[0:6]
                    if bool(data[-1] != '*' and data[-2] != '*') or bool(data[-1] == '*' and data[-2] != '*'):
                        data = list(map(lambda x: x.replace(' ', ''), data))
                        course_data.append({k: v for k, v in zip(COURSE_KEYS, data)})
        if crs_listed:
            if course_data:
                department_schedule[crs_listed] = course_data
    return department_schedule
    

def check_connection(url='https://www.google.com/'):
    """Checks for a connection to the internet
    Returns
        True if internet is connected, False otherwise
    """
    try:
        r.get(url)
    except Exception:
        return False
    else:
        return True


if __name__ == '__main__':
    try:
        os.mkdir(TIME_SCHEDULES_DIR)
    except Exception:
        last_updated = str(dttime.fromtimestamp(os.stat(TIME_SCHEDULES_DIR).st_mtime)).split('.')[0]
        print(f'Campus Time Schedules were last updated on {last_updated}')
        update = input('Update UW Course Time Schedules? (y/n): ').lower()
    else:
        update = 'y'
    finally:
        if 'y' in update:
            if check_connection():
                t1 = time.perf_counter()
                for campus in CAMPUSES.keys():
                    parse_departments(campus)
                t2 = time.perf_counter()
                logger.info(f'{__name__} ran in {(t2 - t1):.1f} seconds')
            else:
                logger.critical('No Internet Connection')
                print('No Internet Connection')
