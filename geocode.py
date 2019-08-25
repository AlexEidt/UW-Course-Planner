"""Geocodes all Building on the UW Seattle Campus
Finds all combinations of classes given a list of courses to search"""

import json, re, os, logging, itertools, time
from datetime import datetime as dttime
from threading import Timer
from parse_schedules import get_next_quarter, get_quarter, CAMPUSES
from parse_schedules import main as parse_schedules
from UW_Buildings import main as get_campuses
from utility import logger, get_web_soup, check_connection, UW_Buildings, UW_Time_Schedules, Organized_Time_Schedules
try:
    import requests as r
except Exception:
    raise Exception('Requests not installed. Try installing with "pip install requests"')
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
except Exception:
    raise Exception('selenium not installed. Try installing with "pip install selenium"')


def get_all_buildings(uw_campus):
    """Creates a dictionary with building abbreviations and their full names
    Returns
        Dictionary with abbreviation, full name pairings for all buildings
    """
    upcoming_quarter = get_next_quarter()
    current_quarter = get_quarter(filter_=True)
    year = dttime.now().year
    if upcoming_quarter == 'WIN':
        if dttime.now().month in [10, 11, 12]:
            year += 1
    if type(current_quarter) == type([]):
        current_quarter = ''.join(current_quarter)
    upcoming_courses_link = '{}{}{}/'.format(CAMPUSES[uw_campus]['link'], upcoming_quarter, year)
    quarter = upcoming_quarter if r.get(upcoming_courses_link).ok else current_quarter

    get_campuses()

    try:
        os.mkdir(UW_Time_Schedules)
    except Exception: pass
    if f'{uw_campus}_{quarter}{year}.json' not in os.listdir(UW_Time_Schedules):
        if check_connection():
            parse_schedules(console=False, update=True)
        else:
            logger.critical('No Internet Connection')
            print('No Internet Connection')

    with open(os.path.normpath(f'{UW_Time_Schedules}/{uw_campus}_{quarter}{year}.json'), mode='r') as file:
        courses = json.loads(file.read())

    campus = set()
    for _, dep_courses in courses.items():
        for _, data in dep_courses.items():
            for course_data in data:
                for x in course_data['Building']:
                    campus.add(x)

    with open(os.path.normpath(f'{UW_Buildings}/UW_Buildings.json'), mode='r') as file:
        buildings = json.loads(file.read())
    total = set(itertools.chain(campus, buildings[uw_campus].keys()))
    check = [x for x in total if x not in buildings[uw_campus].keys()]
    for x in check:
        buildings[uw_campus][x] = {'Name': ''}
    return (buildings, courses)


def geocode(campus):
    """Gets the GPS Coordinates for every building at UW
    @params
        'campus': The UW Campus to get Building Coordinates from
    Returns
        Dictionary of all courses offered at the given campus
        for the current quarter
    """
    dicts = get_all_buildings(campus)
    buildings = dicts[0]
    if campus == 'Seattle':
        plus_codes_url = 'https://plus.codes/map/UW'
    else:
        plus_codes_url = 'https://plus.codes/map/UW {}'.format(campus)

    if f'{campus}_Coordinates.json' not in os.listdir(UW_Buildings):

        def select_url(browser, url, key, full_name, end):
            browser.get(url)
            time.sleep(5)
            html = browser.execute_script("return document.getElementsByTagName('html')[0].innerHTML")
            match = re.search(r'\d+\.\d+,-\d+\.\d+', str(html))
            coords = match.group(0).split(',', 1) if match else ''
            if coords:
                if campus == 'Seattle':
                    check_coords = int(coords[0].split('.', 1)[0]) == 47 and int(coords[1].split('.', 1)[0]) == -122
                else:
                    check_coords = True
            else:
                check_coords = False
            if coords and check_coords:
                buildings[campus][key].update({'Latitude': coords[0], 'Longitude': coords[1]})
            elif end <= 1:
                if end == 0:
                    select_url(browser, f'{plus_codes_url} {key}', key, full_name, end + 1)
                else:
                    select_url(browser, f'{plus_codes_url} {full_name} {key}', key, full_name, end + 1)
            browser.quit()

        for key, value in buildings[campus].items():
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            browser = webdriver.Chrome(options=chrome_options)
            full_name = value['Name'].split('wings')[0]
            total = '{} {}'.format(plus_codes_url, full_name if value['Name'] else key)
            window_open = Timer(0.1, select_url, args=(browser, total, key, full_name, 0))
            window_open.start()

        def create_json():
            new_buildings = {}
            for key, value in buildings[campus].items():
                new_buildings[key] = value
                if 'Latitude' not in value:
                    new_buildings[key].update({'Latitude': '', 'Longitude': ''})
            with open(os.path.normpath(f'{UW_Buildings}/{campus}_Coordinates.json'), mode='w') as file:
                json.dump(new_buildings, file, sort_keys=True, indent=4)

        Timer(10.0, create_json).start()
    return dicts[1]


def geocode_all():
    """Creates UW Time Schedule and UW Buildings json files if necessary.
    Creates json files with all geocoded UW Buildings if necessary.
    """
    print('Geocoding all UW Buildings...')
    courses_offered = {}
    for campus in CAMPUSES.keys():
        courses_offered[campus] = geocode(campus)
    return courses_offered


# --------------------------Time Methods--------------------------#       
get_time = lambda t: [t[0:1], t[1:]] if len(t) == 3 else [t[0:2], t[2:]]
check_pm = lambda t: ' PM' if t else ' AM'
select_pm = lambda i, pm1, pm2: pm1 if not i else pm2
convert = lambda t: time.strftime('%H:%M:%S', time.strptime(t, '%I:%M %p'))
check_convert_pm = lambda t: convert('12:01 AM') < convert(t) < convert('6:30 AM') or convert('10:30 PM') < convert(t) < convert('11:59 PM')
convert_pm = lambda t, pm: f'{pm[0]} {switch_pm(pm[-1])}' if check_convert_pm(t) else t
switch_pm = lambda t: 'AM' if t.strip() == 'PM' else 'PM'
# --------------------------Time Methods--------------------------#    


def has_overlap(time1, time2):
    """Checks if the two times overlap
    @params
        'time1': First time to check
        'time2': Second time to check
    Returns 
        True if there is overlap, otherwise False
    """
    pm1 = 'P' in time1
    pm2 = 'P' in time2
    time1 = time1.replace('P', '')
    time2 = time2.replace('P', '')
    times = list(itertools.chain(time1.split('-', 1), time2.split('-', 1)))
    times = list(map(get_time, times))
    course_times = []
    for i in range(0, len(times), 2):
        pm = select_pm(i, pm1, pm2)
        t1 = f'{times[i][0]}:{times[i][1]}{check_pm(pm)}'
        t2 = f'{times[i + 1][0]}:{times[i + 1][1]}{check_pm(pm)}'
        time1 = convert(convert_pm(t1, t1.rsplit(' ', 1)))
        time2 = convert(convert_pm(t2, t2.rsplit(' ', 1)))
        course_times.append((time1, time2))
    t1 = course_times[0]
    return t1[0] < course_times[1][0] < t1[1] or t1[0] < course_times[1][1] < t1[1]


def get_days(offered):
    """Gets the days a course is offered
    @params
        'offered': String representing the days a course is offered
        Example: 'MWF' -> Monday, Wednesday, Friday
    Returns
        Set of abbreviated days the course is offered
    """
    days = ['Th', 'M', 'T', 'W', 'F', 'S']
    result = set()
    for day in days:
        if day in offered:
            result.add(day)
            offered = offered.replace(day, '', 1)
    return result


def check_overlap(schedule):
    """Checks if the courses in the 'schedule' overlap
    @params
        'schedule': List of dictionaries representing a combination of courses
    Returns
        True if there is overlap between any sections in the 'schedule'.
        False otherwise.
    """
    course_information = {
            'M': [], 'T': [], 'W': [], 'Th': [], 'F': [], 'S':[]
    }
    for course in schedule:
        for course_dict in course:
            for i, d in enumerate(course_dict['Days']):
                for day in get_days(d):
                    course_information[day].append(course_dict['Time'][i])
    for times in course_information.values():
        if len(set(times)) == len(times):
            date_combos = list(itertools.combinations(times, 2))
            dates = [list(set(x)) for x in date_combos if len(set(x)) > 1]
            for date in dates:
                if has_overlap(date[0], date[1]):
                    return True
        else:
            return True
    return False


def get_combinations(planned_courses):
    """Finds all possible combinations of the courses in 'planned_courses'
    such that no sections of any course overlap
    @params
        'planned_courses': List of courses to find combinations from
    Returns
        Generator object with all valid combinations of courses
    """
    with open(os.path.normpath(f'{Organized_Time_Schedules}/Total.json'), mode='r') as file:
        courses_offered = json.loads(file.read())
    total = []
    for course in planned_courses:
        course_sections = []
        lecture = course.rsplit(' ', 1)[-1].strip().upper()
        if re.search(r'[A-Z]\d?', lecture) and ' ' in course:
            search = [courses_offered[course.rsplit(' ', 1)[0]][f'Lecture {lecture}']]
        else:
            search = courses_offered[course].values()
        # Get all Lecture/Quiz/Lab/Studio combinations for the given course
        for section in search:
            products = []
            if section['QZ']:
                products.append(section['QZ'])
            if section['LB']:
                products.append(section['LB'])
            if section['ST']:
                products.append(section['ST'])
            products.append([section['LECT']])
            course_sections.append(list(itertools.product(*products)))
        total.append([y for x in course_sections for y in x])
    # Find all course combinations where there are no course overlaps
    for combo in itertools.filterfalse(lambda x: check_overlap(x), list(itertools.product(*total))):
        yield combo


# Sections class used for the organized Time Schedule
class Sections:
    def __init__(self):
        self.LECT = ''
        self.QZ = []
        self.LB = []
        self.ST = []
    
    def add_section(self, section, data):
        if section == 'QZ':
            self.QZ.append(data)
        elif section == 'LB':
            self.LB.append(data)
        elif section == 'ST':
            self.ST.append(data)


def main():
    """Creates an Organized Time Schedule as a json file with all courses from
    all UW Campuses included for the current UW Quarter. 
    Organized Time Schedules include the Course as the Key. The associated value to 
    this key are all the lectures for this course with quiz, lab and studio sections
    included as a list
    """
    try:
        os.mkdir(UW_Time_Schedules)
    except Exception: pass
    upcoming_quarter = get_next_quarter()
    current_quarter = get_quarter(filter_=True)
    year = dttime.now().year
    if upcoming_quarter == 'WIN':
        if dttime.now().month in [10, 11, 12]:
            year += 1
    if type(current_quarter) == type([]):
        current_quarter = ''.join(current_quarter)
    upcoming_courses_link = '{}{}{}/'.format(CAMPUSES['Seattle']['link'], upcoming_quarter, year)
    quarter = upcoming_quarter if r.get(upcoming_courses_link).ok else current_quarter
    if f'Seattle_{quarter}{year}.json' not in os.listdir(UW_Time_Schedules):
        courses = geocode_all()
        all_campuses = {}
        all_campuses.update(courses['Seattle'])
        all_campuses.update(courses['Bothell'])
        all_campuses.update(courses['Tacoma'])
        total = set()
        for campus in CAMPUSES.keys():
            for department in courses[campus].values():
                for crs in department.keys():
                    total.add(crs)
        course_map = {}
        for course in total:
            department = re.search(r'[A-Z&]+', course).group(0)
            course_list = all_campuses[department][course]
            section_map = {}
            for section in course_list:
                section_type = section['Type']
                if section_type in ['LECT', 'VAR']:
                    course_sections = Sections()
                    course_sections.LECT = section
                    section_map['Lecture {}'.format(section['Section'])] = course_sections.__dict__
                else:
                    course_sections.add_section(section_type, section)
            course_map[course] = section_map
        try:
            os.mkdir(Organized_Time_Schedules)
        except Exception: pass
        with open(os.path.normpath(f'{Organized_Time_Schedules}/Total.json'), mode='w') as file:
            json.dump(course_map, file, indent=4, sort_keys=True)


if __name__ == '__main__':
    if check_connection():
        main()
    else:
        print('No Internet Connection')
        logger.critical('No Internet Connection')

