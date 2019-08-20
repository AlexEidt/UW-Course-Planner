"""
MIT License

Copyright (c) 2017 Kamil Jiwa

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

*****************************************************************************
NOTE from Alex Eidt:
Building off the script by Kamil Jiwa, the following changes were made:

    -BeautifulSoup used for web scraping
    -TSV files created with new data for each course:
        -Co-requisites
        -Jointly offered courses
        -Course Descriptions
        -Courses offered with that course
    -All course data written to JSON files as well
    -Courses split by campus
    -New system for displaying prerequisite courses using ';', '&&' and ','
    -Progress bar for parsing
"""

""" Creates a tsv file containing course data for each UW Campus """

import re
import csv
import time
import logging
import json
import os
import urllib3 as URL
try:
    import requests as r
except Exception:
    raise Exception('Requests not installed. Try installing with "pip install requests"')
try:
    from bs4 import BeautifulSoup as Soup
except Exception:
    raise Exception('bs4 not installed. Try installing with "pip install beautifulsoup4"')
try:
    from tqdm import tqdm as AddProgressBar
except Exception:
    raise Exception('tqdm not installed. Try installing with "pip install tqdm"')

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(name)s -- %(asctime)s -- %(levelname)s : %(message)s')
handler = logging.FileHandler('Log.log')
handler.setLevel(logging.DEBUG)
handler.setFormatter(formatter)
logger.addHandler(handler)

course_dir = 'UW_Campus_Catalogs' # Name of Folder with Campus tsv/json files
course_files_dir = f'{os.getcwd()}\\{course_dir}' # course_dir file path

CAMPUSES = {                                                                                
    'Bothell': 'http://www.washington.edu/students/crscatb/',                               
    'Seattle': 'http://www.washington.edu/students/crscat/',                                
    'Tacoma': 'http://www.washington.edu/students/crscatt/'                                 
}                                                                                           

COLUMN_NAMES = ['Campus', 'Department Name', 'Course Number', 'Course Name', 'Credits',
                'Areas of Knowledge', 'Quarters Offered', 'Offered with', 
                'Prerequisites', 'Co-Requisites', 'Description']


def complete_description(description):
    """Replaces all occurances of un-numbered courses in the given course description
    @params
        'description': The course description
    Returns 
        Completed courses in description
    """
    find_all = re.findall(r'[A-Z& ]+/[A-Z& ]+/[A-Z& ]+\d+', description)
    find_one = re.findall(r'[A-Z& ]+/[A-Z& ]+\d+', description)
    
    def remove_in(a, b):
        remove = [y for x in a for y in b if y in x]
        for x in b: a.append(x)
        for x in remove: a.remove(x)
        return [x for x in a]
            
    if find_one:
        find_all = remove_in(find_all, find_one)
        for i, x in enumerate(find_all):
            completed = []
            find_all[i] = x.replace(' ', '')
            number = re.search(r'\d{3}', find_all[i]).group(0)
            for crs in re.findall(r'[A-Z& ]+', find_all[i]):
                completed.append(f'{crs}{number}')
            description = description.replace(x, '{}{}'.format(' ', '/'.join(completed)), 1)

    find_series_2 = re.findall(r'[A-Z& ]+\d+, ?\d{3}', description)
    find_series_3 = re.findall(r'[A-Z& ]+\d+, ?\d{3}, ?\d{3}', description)
    find_series_2 = remove_in(find_series_3, find_series_2)
    for i, series in enumerate(find_series_2):
        find_series_2[i] = series.replace(' ', '')
        number = find_series_2[i][-3:]
        depmnt = None
        course_dep = re.search(r'[A-Z& ]+', find_series_2[i])
        if course_dep: 
            depmnt = course_dep.group(0)
            description = description.replace(series, f'{depmnt}{number}', 1)
    return description


def get_credits(description):
    """Gets the number of credits the course is offered at
    @params
        'description': The course description
    Returns 
        The number of credit offered for the course if there are any, otherwise an empty String
    """
    match = re.search(r'\([\*,\[\]\.max\d/ \-]+\)', description)
    return match.group(0)[1:-1] if match else ''


not_offered = re.compile(r'[Nn]ot open to students')
co_req = re.compile(r'[Cc]o-?[Rr]equisites?')
def get_requisites(description, type):
    """Gets the requisite courses for the given course
    @params
        'description': The course description
        'type': Either 'Prerequisite' or 'Co-Requisite'
    Returns 
        The requisite courses. 
        If type='Prerequisite', courses are separated by ';', '/', '&&', and/or ','
    """
    if type not in description:                                                             
        return ''       
    description = description.replace(' AND ', ' and ').replace(' OR ', ' or ').replace('; or', '/')
    description = description.replace('and either', ';').replace('and one of', ';')
    description = re.sub(r'([Cc]annot|[Mm]ay not) be taken for credit if (credit received for|student has taken)?[A-Z& ]+\d{3}', '', description)
    description = not_offered.split(description.split('Offered:')[0].split(type)[1])[0]
    multiple = re.search(r'[A-Z& ]+\d{3}/[A-Z& ]+\d{3}/[A-Z& ]+\d{3} and', description)
    if multiple:
        description = description.replace(multiple.group(0), f'{multiple.group(0)[:-4]};', 1)
    if 'Prerequisite' in type: description = co_req.split(description)[0]                         
    POI = ',POI' if 'permission' in description.lower() else '' 
    new_result = []
    for course in description.split('(')[0].split(';'):
        if ', and' in course:
            new_result.append(course.replace(',', ';'))     
        else:
            new_result.append(course)
    description = ';'.join(new_result)

    if 'with either' in description:
            with_either = description.split('with either')
            description = '{}&&{}'.format(with_either[0], with_either[1].replace('or', '/'))
    description = description.replace('and', '&&').replace('or', ',')

    def extract(course_option, split_char):
        elements = []
        for next_option in list(filter(('').__ne__, course_option.split(split_char))):
            find_match(next_option, elements)
        return elements

    def find_match(to_match, to_append):
        match = re.search(r'([A-Z& ]{2,}\d{3})', to_match)
        if match: to_append.append(match.group(0))

    semi_colon = []
    for crs in list(filter(('').__ne__, description.split(';'))):
        comma = []
        for option in list(filter(('').__ne__, crs.split(','))):
            if '/' in option and '&&' not in option:
                comma.append('/'.join(extract(option, '/')))
            elif '/' not in option and '&&' in option:
                comma.append('&&'.join(extract(option, '&&')))
            elif '/' in option and '&&' in option:
                doubleand = ['/'.join(extract(x, '/')) for x in list(filter(('').__ne__, option.split('&&')))]
                comma.append('&&'.join(doubleand))
            else:
                find_match(option, comma) 
        semi_colon.append(','.join(list(filter(('').__ne__, comma))))
    result = ';'.join(list(filter(('').__ne__, semi_colon))).replace(' ', '')
    result = result.strip(',').strip(';').strip('&').replace(';,', ';')
    result = f'{result}{POI}'
    result = re.sub(r'&{3,}', '', result)
    result = ','.join(list(filter(('').__ne__, result.split(','))))
    result = ';'.join(list(filter(('').__ne__, result.split(';'))))
    result = ','.join(list(dict.fromkeys(result.split(',')))).replace(';&&', ';').strip('&')
    result = ';'.join(list(dict.fromkeys(result.split(';'))))
    result = result.strip(',').strip(';').strip('&').replace(';,', ';').strip()
    filter_result = []
    for course in result.split(';'):
        if '/' in course and '&&' not in course:
            filter_result.append(course.replace('/', ','))
        elif '/' not in course and '&&' in course and ',' not in course:
            filter_result.append(course.replace('&&', ';'))
        else:
            filter_result.append(course)
    return ';'.join(filter_result)


def get_offered(description):
    """Gets the quarters the course is offered
    @params
        'description': The course description
    Returns 
        Quarters offered as comma separated list (A, W, Sp, S)
    """
    if 'Offered:' not in description:                                                       
        return ''                                                                           
    check_parts = description.split('Offered:')[1]                                         
    parts = check_parts.split(';')[1] if ';' in check_parts else check_parts
    parts = re.sub(r'([A-Z& ]+\d+)', '', parts)
    result = []
    quarters = ['A', 'W', 'Sp', 'S']
    for quarter in quarters:
        if quarter in parts:
            result.append(quarter)
            parts = parts.replace(quarter, '')
    return ','.join(result)
    

def get_jointly(description):
    """Gets the jointly offered courses for the given course
    @params
        'description': The course description
    Returns 
        The jointly offered courses as a comma separate list
    """
    if 'jointly with' not in description:                                                   
        return ''
    description = description.split('jointly with ')[1].split(';')[-1]                                
    return ','.join(re.findall(r'([A-Z& ]+\d+)', description)).replace(' ', '')                         


def get_credit_types(description):
    """Gets the credit types I&S/DIV/NW/VLPA/QSR for the course
    @params
        'description': The course description
    Returns 
        The credit types offered for the course if there are any, otherwise an empty String
    """
    match = re.search(r'((I&S|DIV|NW|VLPA|QSR)(,?\s?/?))+', description)
    return match.group(0).strip() if match else ''


def get_name(description, number):
    """Returns the course name, otherwise returns an empty String
    @params
        'description': The course description
    Returns
        The course name
    """
    match = re.search(r'[^\(]+', description)
    return match.group(0).split(number.replace('&', ''))[1].strip() if match else ''


def extract_description(description, credit_type):
    """Removes instructor names from description
    @params
        'description': The course description
        'credit_type': The credit types for the course
    Returns
        A description string with all instructor names removed
    """
    description = description.split('Offered: ')[0]
    description = description.split(')', 1)[1]
    if '' not in credit_type:
        description = description.split(credit_type)[1]
    match = re.search(r'[A-Z]{2,}[a-z]+', description)
    if match:
        found = match.group(0)
        description = description.split(found)[1]
        match_match = re.search(r'[A-Z][a-z]+', found)
        if match_match:
            description = f'{match_match.group(0)} {description.strip()}'
    else:
        match = re.search(r'[A-Z][a-z]+[A-Z]', description)
        if match:
            found = match.group(0)
            description = description.split(found)[1]
            description = f'{found[-1]}{description}'
    return description


def get_course_data(campus, department, number, description):
    """Puts all course data into a list
    @params
        'campus': The campus the course is offered
        'department': The abbreviated department name that the course is offered in
        'number': The course number
        'description': The course description
    Returns 
        List of all the information for the given course in the 'description'
    """
    functions = [get_credits, get_credit_types, get_offered, get_jointly]
    description = description.split('View course details in MyPlan:')[0]
    description = complete_description(description)
    data = [campus, department, number, get_name(description, number)]
    for function in functions:
        data.append(function(description))
    data.append(get_requisites(description, 'Prerequisite:'))
    data.append(get_requisites(description, "Co-requisite"))
    data.append(extract_description(description, data[5]))
    return data


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


department_dict = {} # Maps department abbreviations to names for each UW Campus
total_department_dict = {} # Department abbreviations to names for all UW Campuses
def read_department_courses(course_data, campus, path):
    """Creates a .tsv file with all the course offered on the given 'campus'
       Initalizes 'departments.json' to include a dictionary of all department
       abbreviations to actual department name for each UW Campus.
    @params
        'course_data': BeautifulSoup object with the department list website for the given 'campus'
        'campus': The campus to get the courses from
        'path': The file path to the directory storing all .tsv files for each campus
    """
    department_names = {}
    not_parsed = []
    with open(f'{path}\\TSV\\{campus}.tsv', mode='w', newline='') as courses:
        tsv_writer = csv.writer(courses, delimiter='\t')
        tsv_writer.writerow(COLUMN_NAMES)
        for dep_link in AddProgressBar(course_data.find_all('a')):
            dep_file = dep_link.get('href')
            if '.html' in dep_file and '/' not in dep_file:
                file_name = f'{CAMPUSES[campus]}{dep_file}'
                request = r.get(file_name)
                if request.ok:   
                    department = get_web_soup(file_name)
                    for course in department.find_all('a'):
                        course_ID = course.get('name')             
                        if course_ID:
                            department_name = re.sub(r'\d+', '', course_ID).upper()
                            course_number = re.sub(r'[A-Z&]+', '', course_ID.upper())
                            tsv_writer.writerow(get_course_data(campus, department_name, 
                                                course_number, course.get_text()))
                            department_full_name = dep_link.get_text().rsplit('(', 1)[0].strip()
                            department_names[department_name] = department_full_name
                            total_department_dict[department_name] = department_full_name
                else:
                    logger.critical(f'Could not access: {file_name}. HTTP Status Code: {request.status_code}')
                    not_parsed.append(dep_file.replace('.html', '', 1).upper())
    department_dict[campus] = department_names
    return not_parsed


def write_json(all_courses, mode_type, campus):
    """Writes the complete course dictionary for a UW Campus to a JSON file
    @params
        'all_courses': Course dictionary
        'mode_type': Write or append to file
        'campus': The campus the courses are from
    """
    file_name = f'{course_files_dir}\\JSON\\{campus}.json'
    with open(file_name, mode=mode_type) as json_file:
        json.dump(all_courses, json_file, indent=4, sort_keys=True)


def read_file(campus):
    """Scans the tsv file for the given 'campus'
    @params
        'campus': The campus to search courses from
    Returns:
        Dictionary of all course ID's with their information
    """
    all_courses = {}
    with open(f'{course_files_dir}\\TSV\\{campus}.tsv', mode='r') as file:
        reader = csv.reader(file, delimiter='\t')
        next(reader)
        for course in reader: 
            if course:
                all_courses['{0[1]}{0[2]}'.format(course)] = {
                    COLUMN_NAMES[i]: course[i] for i in range(len(COLUMN_NAMES))
                }
    return all_courses


def gather(path):
    """Creates a .tsv file for every UW campus
    @params
        'path': The file path to the directory storing all .tsv files for each campus
    Returns
        Dictionary with missing departments for each UW Campus
    """
    not_scanned = {}
    t1 = time.perf_counter()
    for campus, link in CAMPUSES.items():
        request = r.get(link)
        not_parsed = None
        if request.ok:
            not_parsed = read_department_courses(get_web_soup(link), campus, path)
        else:
            logger.error(f'''Could not access UW {campus} Course Catalog ({CAMPUSES[campus]}). 
                            HTTP Status Code: {request.status_code}''')
        not_scanned[campus] = not_parsed

    # Remove docs with all courses to prevent appending to old files
    try: os.remove(f'{course_files_dir}\\JSON\\Total.json')
    except (FileExistsError, FileNotFoundError): pass
    try: os.remove(f'{course_files_dir}\\TSV\\Total.tsv')
    except (FileExistsError, FileNotFoundError): pass

    # Create Departments json file
    department_dict['Total'] = total_department_dict
    with open(f'{path}\\JSON\\Departments.json', mode='w') as file:
        json.dump(department_dict, file, indent=4, sort_keys=True)

    # Create Total.tsv file
    total = open(f'{course_files_dir}\\TSV\\Total.tsv', mode='a')
    csv.writer(total, delimiter='\t').writerow(COLUMN_NAMES)
    for campus in CAMPUSES.keys():
        write_json(read_file(campus), 'w', campus)
        logger.info(f'JSON File for UW {campus} created under {course_files_dir}\\JSON')
        with open(f'{course_files_dir}\\TSV\\{campus}.tsv') as campus_file: 
            next(campus_file)
            for line in campus_file:
                total.write(line)

    # Create Total.json file
    write_json(read_file('Total'), 'w', 'Total')
    logger.info(f'JSON File for All UW Campuses created under {course_files_dir}\\JSON')
    
    total.close()
    t2 = time.perf_counter()

    check = [y for x in not_scanned.values() for y in x]
    if None in not_scanned.values() or check:
        logger.critical(f'Error in parsing courses. Courses from {str(check)} not parsed')
    else:
        logger.info(f'''Course Catalogs for {', '.join(CAMPUSES.keys())} 
                    have been sucessfully created in: {path}''')
        logger.info('{} ran in {:.1f} seconds'.format(__name__, t2 - t1))


if __name__ == '__main__':
    try:
        r.get('https://www.google.com/') # Check Internet Connection
    except Exception:
        pass
    else:
        try: os.mkdir(course_dir)
        except Exception: pass
        try: os.mkdir(f'{course_files_dir}\\JSON')
        except Exception: pass
        try: os.mkdir(f'{course_files_dir}\\TSV')
        except Exception: pass
        gather(course_files_dir)