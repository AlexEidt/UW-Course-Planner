"""Geocodes all Building on the UW Seattle Campus"""

import json, re, os, logging
from time import sleep
from datetime import datetime as dttime
from threading import Timer
from itertools import chain
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
    upcoming_courses_link = '{}{}{}/'.format(CAMPUSES[uw_campus]['link'], upcoming_quarter, dttime.now().year)
    quarter = upcoming_quarter if r.get(upcoming_courses_link).ok else get_quarter(filter_=True)

    get_campuses()

    try:
        os.mkdir(UW_Time_Schedules)
    except Exception: pass
    if f'{uw_campus}_{quarter}{dttime.now().year}.json' not in os.listdir(UW_Time_Schedules):
        if check_connection():
            parse_schedules(console=False, update=True)
        else:
            logger.critical('No Internet Connection')
            print('No Internet Connection')

    with open(os.path.normpath(f'{UW_Time_Schedules}/{uw_campus}_{quarter}{dttime.now().year}.json'), mode='r') as file:
        courses = json.loads(file.read())

    campus = set()
    for _, dep_courses in courses.items():
        for _, data in dep_courses.items():
            for course_data in data:
                for x in course_data['Building']:
                    campus.add(x)

    with open(os.path.normpath(f'{UW_Buildings}/UW_Buildings.json'), mode='r') as file:
        buildings = json.loads(file.read())
    total = set(chain(campus, buildings[uw_campus].keys()))
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
            sleep(5)
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

