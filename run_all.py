"""
Generates all Filess for the UW Course Tool
Takes about 10 minutes to run.
"""

import shutil
from utility import UW_Buildings, UW_Course_Catalogs, UW_Time_Schedules, check_connection
from parse_courses import gather
from geocode import main as geocode


if __name__ == '__main__':
    try:
        shutil.rmtree(UW_Buildings)
    except Exception: pass
    try:
        shutil.rmtree(UW_Course_Catalogs)
    except Exception: pass
    try:
        shutil.rmtree(UW_Time_Schedules)
    except Exception: pass
    if check_connection():
        gather()
        geocode()
    else:
        print('No Internet Connection')