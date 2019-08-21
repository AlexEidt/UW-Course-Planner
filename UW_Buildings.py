"""Parses UW's Facilities Websites to get all Building Names"""

import re, json, logging, os
from parse_schedules import get_next_quarter, get_quarter, CAMPUSES
from utility import get_web_soup, check_connection, UW_Buildings
try:
    import requests as r
except Exception:
    raise Exception('Requests not installed. Try installing with "pip install requests"')
try:
    from bs4 import BeautifulSoup as Soup
except Exception:
    raise Exception('bs4 not installed. Try installing with "pip install beautifulsoup4"')


def seattle():
    """Parses UW's Facilities to get all Building Names for UW Seattle Campus
    Returns
        Dictionary with Building Name Abbreviations to full Building Names"""
    buildings_dict = {}
    # Get UW Seattle Dorm Building Abbreviations and Names
    uw_dorms = get_web_soup('https://hfs.uw.edu/Live/Undergraduate-Residence-Halls-and-Apartments')
    for img in uw_dorms.find_all('img'):
        dorm_name = str(img).rsplit('alt="', 1)[-1].split('"', 1)[0]
        if 'Hall' in dorm_name:
            dorm_site = get_web_soup(f'https://www.google.dz/search?q=http://www.washington.edu/maps UW {dorm_name}').find('html')
            match = re.search(r'\([A-Z]{3,}\)\s?((\</div\>)|(\s?\| Campus Maps))', str(dorm_site))
            if match:
                dorm_abb = re.search(r'\([A-Z]{3,}\)', match.group(0)).group(0)[1:-1]
                if dorm_abb not in buildings_dict:
                    buildings_dict[dorm_abb] = {'Name': dorm_name}

    # Get UW Seattle Classroom Building Abbreviations and Names
    uw_classrooms = get_web_soup('https://www.washington.edu/classroom/')
    uw_classrooms = uw_classrooms.find("div", {"id": "buildings"})
    for link in uw_classrooms.find_all('a'):
        if link.get('href') not in buildings_dict:
            buildings_dict[link.get('href')] = {'Name': link.text.rsplit('(', 1)[0].strip()}
        
    # Supplement previous UW Building scrape with additional data
    buildings = get_web_soup('https://www.washington.edu/students/reg/buildings.html')
    buildings = str(buildings.html).split('<h2>Code - Building Name (Map Grid)</h2>', 1)[-1]
    buildings = Soup(buildings.rsplit('<div class="uw-footer">', 1)[0], features='lxml')
    for building_group in buildings.find_all('p'):
        for building in str(building_group).split('<br/>'):
            if 'a href' in building:
                building = Soup(building, features='lxml')
                abbreviation = building.find('code').text
                name = building.find('a').text
                if abbreviation not in buildings_dict:
                    buildings_dict[abbreviation] = {'Name': name.split('\n', 1)[0].strip()}
    return buildings_dict


def bothell():
    """Parses UW's Facilities to get all Building Names for UW Bothell Campus
    Returns
        Dictionary with Building Name Abbreviations to full Building Names"""
    buildings = {}
    bothell_buildings = get_web_soup('https://www.uwb.edu/safety/hours')
    for building in bothell_buildings.find_all('div', {'class': ['col1', 'col2', 'col3']}):
        bld = str(building.find('h3'))
        if bld and '(' in bld:
            abbreviation = bld.rsplit('(', 1)[-1].split(')')[0]
            name = bld.rsplit('(', 1)[0].strip()
            buildings[abbreviation] = {'Name': name.replace('<h3>', '').replace('&amp;', '&')}
    return buildings


def tacoma():
    """Parses UW's Facilities to get all Building Names for UW Seattle Campus
    Returns
        Dictionary with Building Name Abbreviations to full Building Names"""
    buildings = {}
    tacoma_buildings = get_web_soup('https://www.tacoma.uw.edu/campus-map/buildings')
    for building in tacoma_buildings.find('div', class_='field-items').find('ul').find_all('a'):
        text = building.text
        if '(' in text:
            abbreviation = text.rsplit('(', 1)[-1].split(')')[0]
            name = text.rsplit('(', 1)[0].strip()
            buildings[abbreviation] = {'Name': name}
        else:
            link = get_web_soup('https://www.tacoma.uw.edu{}'.format(str(building.get('href'))))
            for table in link.find_all('table'):
                for l in table.find_all('a'):
                    if re.search(r'[A-Z]{2,} \d+', l.text):
                        buildings[str(l.text).split(' ', 1)[0].upper()] = {'Name': text}
                        break
    return buildings
    

def main():
    print('Scanning UW Buildings...')
    try:
        os.mkdir(UW_Buildings)
    except Exception:
        pass
    if 'UW_Buildings.json' not in os.listdir(UW_Buildings):
        buildings = {}
        buildings['Seattle'] = seattle()
        buildings['Bothell'] = bothell()
        buildings['Tacoma'] = tacoma()
        try:
            os.mkdir(UW_Buildings)
        except Exception:
            pass
        with open(os.path.normpath(f'{UW_Buildings}/UW_Buildings.json'), mode='w') as file:
            json.dump(buildings, file, sort_keys=True, indent=4)


if __name__ == '__main__':
    if check_connection():
        main()
    else:
        print('No Internet Connection')

