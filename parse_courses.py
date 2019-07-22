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

"""

# Creates a tsv file containing course data for each UW Campus

import re
import csv
import time
import urllib3 as URL
from bs4 import BeautifulSoup as Soup
from tqdm import tqdm


CAMPUSES = {                                                                                
    'Bothell': 'http://www.washington.edu/students/crscatb/',                               
    'Seattle': 'http://www.washington.edu/students/crscat/',                                
    'Tacoma': 'http://www.washington.edu/students/crscatt/'                                 
}                                                                                           


# Replaces all occurances of un-numbered courses in the given course description
# 'description': The course description
def complete_description(description):
    find_all = re.findall(r'[A-Z& ]+/\s?[A-Z& ]+/\s?[A-Z& ]+\s?\d+', description)
    find_one = re.findall(r'[A-Z& ]+/\s?[A-Z& ]+\s?\d+', description)
    
    def remove_in(a, b):
        remove = []
        for x in a: 
            for y in b: 
                if y in x: remove.append(y)
        for x in b: a.append(x)
        for x in remove: a.remove(x)
        return [x for x in a]
            
    if len(find_one) is not 0:
        find_all = remove_in(find_all, find_one)
        for i, x in enumerate(find_all):
            completed = []
            old = find_all[i]
            find_all[i] = x.replace(' ', '')
            number = re.search(r'\d{3}', find_all[i]).group(0)
            for crs in re.findall(r'[A-Z& ]+', find_all[i]):
                completed.append('{}{}'.format(crs, number))
            description = description.replace(old, '/'.join(completed), 1)
    find_series_2 = re.findall(r'[A-Z& ]+\d+, ?\d+', description)
    find_series_3 = re.findall(r'[A-Z& ]+\d+, \d+, ?\d+', description)
    find_series_2 = remove_in(find_series_3, find_series_2)
    for i, series in enumerate(find_series_2):
        find_series_2[i] = series.replace(' ', '')
        number = find_series_2[i][-3:]
        depmnt = None
        course_dep = re.search(r'[A-Z& ]+', find_series_2[i])
        if course_dep: 
            depmnt = course_dep.group(0)
            description = description.replace(series, '{}{}'.format(depmnt, number), 1)
    return description


# Returns the number of credits for the course if there are any
# Otherwise returns an empty String
# 'description': The course description
def get_credits(description):
    match = re.search(r'\(\[?\d', description)
    return int(match.group(0).replace('(', '').replace('[', '')) if match else ''


# Returns the prerequisite courses for the course if there are any
# Otherwise returns an empty String
# 'description': The course description
prereq_regex = re.compile(r';|:|and either|and one of')
not_offered = re.compile(r'[Nn]ot open to students')
def get_requisites(description, type):
    if type not in description:                                                             
        return ''       
    description = description.replace('AND', 'and').replace('OR', 'or').replace('Minimum', 'minimum')  
    description = description.replace('A minimum', 'a minimum')                                                                     
    parts = not_offered.split(description.split('Offered:')[0].split(type)[1])[0]                               
    POI = ''
    if 'permission of' in parts.lower(): POI = 'POI'                        
    required = prereq_regex.split(parts.split('(')[0])
    result = ''

    def remove_unnessecary(course_sub):
        course_sub = re.sub(r'(E|e)ither', '', course_sub)
        course_sub = re.sub(r'[a-z]+', '', course_sub)
        course_sub = re.sub(r'\d?\.\d', '', course_sub)
        return course_sub

    def split_courses(required_list, join_char, split_char, resulting):
        for course_option in required_list:
            reqcrs = [crs.strip() for crs in re.findall(r'([A-Z& ]+\s?\d+)', course_option)]
            resulting += join_char.join(list(filter(('').__ne__, reqcrs)))
            resulting += split_char
        return resulting

    def filter_result(result):
        result = result.replace(' ', '').strip(';').strip(',').strip('\"').strip('.').strip('\\').strip('n').strip('&')
        result = re.sub(r';+', ';', result)
        result = re.sub(r',+', ',', result)
        return result

    for course in required:
        if 'either' in course or 'Either' in course:
            if 'with either' in course:
                with_either = course.split('with either')
                course = '{}{}{}'.format(with_either[0], '&&', with_either[1].replace('or', '/'))
            reqs = course.split('or')
            if 'and' in course:
                for c in reqs:
                    c = c.replace('and', '&&').replace(' ', '')
                    c = remove_unnessecary(c)
                    result += c
                    result += ','
            else:
                result = split_courses(reqs, ',', ',', result)
        elif 'both' in course or 'in each of' in course:
            result = split_courses(course.split('or'), '&&', ',', result)
        elif 'minimum grade' in course:
            course = course.replace('and', '&&').replace('or', ',')
            course = remove_unnessecary(course)
            result += course
        elif 'and' in course and 'or' not in course:
            result = split_courses(course.split('and'), ',', ';', result)
        else:
            course = course.replace('and', '&&').replace(' ', '').replace('/', ',').replace('or', ',')
            course = remove_unnessecary(course)
            remove = []
            course_list = course.split(',')
            for i, x in enumerate(list(filter(('').__ne__, course_list))):
                match = re.search(r'[A-Z& ]+\s?\d{3}(&&[A-Z& ]+\s?\d{3})?', x)
                if not match: remove.append(x)
                else: course_list[i] = match.group(0)
            for x in remove: 
                if x in course_list:
                    course_list.remove(x)
            result += ','.join(course_list)
            result += ','
        result += ';'
    result += ',{}'.format(POI)
    result_replace = [[',;', ';'], [';,', ';'], [';&&', ';'], ['&&;', ';'], [',&&', ','], ['&&,', ',']]
    for check in result_replace:
        result = result.replace(check[0], check[1])
    result_regex = [[r';+', ';'], [r',+', ','], [r';\d,', ';'], [r',\d,', ','], [r';\d&', ';&'], 
                    [r',\d&', ',&'], [r',\.?[A-Z]?;', ';'], [r',\d+,?', ','], [r',\d+;', ';'],
                    [r';\d+;', ';']]
    for check in result_regex:
        result = re.sub(check[0], check[1], result)
    if result[0].isdigit():
        result = result[1:]
    result_replace_2 = [['.C', ''], ['/-', ''], ['.', ','], [',;', ';'], [';,', ';']]
    for check in result_replace_2:
        result = result.replace(check[0], check[1])
    result = filter_result(result)
    result = filter_result(result)
    for check in result_replace:
        result = result.replace(check[0], check[1])
    result = filter_result(result)
    result = ','.join(list(dict.fromkeys(result.split(','))))
    return result if len(result) > 4 and 'POI' not in result else ''


# Returns the Quarters that the course is offered if there are any
# Otherwise returns an empty String
# 'description': The course description
def get_offered(description):
    if 'Offered:' not in description:                                                       
        return ''                                                                           
    check_parts = description.split('Offered:')[1]                                         
    parts = check_parts.split(';')[1] if ';' in check_parts else check_parts
    parts = re.sub(r'([A-Z& ]+\s?\d+)', '', parts)
    result = []
    quarters = ['A', 'W', 'Sp', 'S']
    for quarter in quarters:
        if quarter in parts:
            result.append(quarter)
            parts = parts.replace(quarter, '')
    return ','.join(result)
    

# Returns the courses offered jointly with the course if there are any
# Otherwise returns an empty String
# 'description': The course description
def get_jointly(description):
    if 'jointly with' not in description:                                                   
        return ''
    parts = description.split('jointly with ')[1].split(';')                                
    course = ''
    for course_option in list(filter(('').__ne__, parts)):
        reqcrss = [crs.strip() for crs in re.findall(r'([A-Z& ]+\s?\d+)', course_option)]     
        course += ','.join(reqcrss)                                                         
        course += ';'
    course = course.replace(',;', ';')
    course = re.sub(r';+', ';', course)
    return course.replace(' ', '').strip(';').strip()                            


# Returns the credit types offered for the course if there are any
# Otherwise returns an empty String
# 'description': The course description
def get_credit_types(description):
    match = re.search(r'((I&S|DIV|NW|VLPA|QSR)(,?\s?/?))+', description)
    return match.group(0).strip() if match else ''


# Returns the course name
# Otherwise returns an empty String
# 'description': The course description
def get_name(description, number):
    match = re.search(r'[^\(]+', description)
    return match.group(0).split(number.replace('&', ''))[1].strip() if match else ''


# Removes instructor names from description
# 'description': The course description
# 'credit_type': The credit types for the course
def extract_description(description, credit_type):
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
            description = '{} {}'.format(match_match.group(0), description.strip())
    else:
        match = re.search(r'[A-Z][a-z]+[A-Z]', description)
        if match:
            found = match.group(0)
            description = description.split(found)[1]
            description = '{}{}'.format(found[-1], description)
    return description


# Returns a list of all the information for the given course in the 'description'
# 'campus': The campus the course is offered
# 'department': The abbreviated department name that the course is offered in
# 'number': The course number
# 'description': The course description
def get_course_data(campus, department, number, description):
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


# Returns a BeautifulSoup object for the given link
# 'website_link': The website to be web scraped
def get_web_soup(website_link):
    website = URL.PoolManager()
    source = website.request('GET', website_link)
    return Soup(source.data, features='lxml')


# Creates a .tsv file with all the course offered on the given 'campus'
# 'course_data': BeautifulSoup object with the department list website for the given 'campus'
# 'campus': The campus to get the courses from
# 'path': The file path to the directory storing all .tsv files for each campus
def read_department_courses(course_data, campus, path):
    with open('{}\\{}\\{}.tsv'.format(path, 'TSV', campus), mode='w', newline='') as courses:
        column_names = ['Campus', 'Department Name', 'Course Number', 'Course Name', 'Credits',
                        'Areas of Knowledge', 'Quarters Offered', 'Offered with', 
                        'Prerequisites', 'Co-Requisites', 'Description']
        csv_writer = csv.writer(courses, delimiter='\t')
        csv_writer.writerow(column_names)
        for dep_link in tqdm(course_data.find_all('a')):
            dep_file = dep_link.get('href')
            if '.html' in dep_file and '/' not in dep_file:
                file_name = '{}{}'.format(CAMPUSES[campus], dep_file)   
                department = get_web_soup(file_name)
                for course in department.find_all('a'):
                    course_ID = course.get('name')             
                    department_name = None
                    course_number = None
                    if course_ID:
                        department_name = re.sub(r'\d+', '', course_ID).upper()
                        course_number = re.sub(r'[A-Z]+', '', course_ID.upper())
                        csv_writer.writerow(get_course_data(campus, department_name, 
                                            course_number, course.get_text()))


# Creates a .tsv file for every UW campus
# 'path': The file path to the directory storing all .tsv files for each campus
def gather(path):
    t1 = time.perf_counter()
    for campus, link in CAMPUSES.items():
        read_department_courses(get_web_soup(link), campus, path)
    t2 = time.perf_counter()
    print('Course Catalogs for {} have been sucessfully created in: \n\t{}'.format(str(list(CAMPUSES.keys()))[1:-1].replace("'", ''), path))
    print('Script ran in {:.1f} seconds'.format(t2 - t1))
