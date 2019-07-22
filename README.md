# UW Course Tool

### Requirements
```python
 - Python 3.7.2 or higher
 - tqdm [pip install tqdm]
 - bs4 [pip install bs4]
```

### UW Course Catalogs
 >[Bothell](http://www.washington.edu/students/crscatb/)                             
 [Seattle](http://www.washington.edu/students/crscat/)                                
 [Tacoma](http://www.washington.edu/students/crscatt/) 

### Files Created
A tsv and JSON file are created for every UW Campus, as well as an additional file 'Total' with all courses from each campus.
Each course has the following data:

For the example course **EE235** shown below, the prerequisites for that course are listed as follows in the tsv and JSON files:

**MATH136,MATH307,AMATH351;PHYS122;CSE142,CSE143**

As mentioned in the table above, courses separated by commas indicate that one course in that comma separated list will fulfill that part of the requirement. Every course (or course group) enclosed by semi-colons indicate that one of those course **MUST** be taken to fulfill that part of the requirement.


***

Data | Description
:--- | ---
**Campus** | The campus the course is offered at
**Department Name** | The name of the department the course is a part of. Denoted by a series of capital letters with no spaces.
**Course Number** | The 3 digit number identifying the course.
**Course Name** | The name of the course
**Credits** | The number of credits offered for the course
**Areas of Knowledge** | Areas of Knowledge essentially are credit types. [More Information](https://www.washington.edu/uaa/advising/degree-overview/general-education/)
**Quarters Offered** | The quarters of the year the course is offered. **A**utumn, **W**inter, **Sp**ring, **S**ummer.
**Offered with** | At times, a course may be offered alongside a similar course in a different department. 
**Prerequisites** | Courses that must be taken in order to take the course. In the tsv and JSON files, Prerequisite courses are split using a series of characters. An group of courses enclosed by **;** mean that at least one of those courses must be taken as a prerequisite. Any group of courses separated by **,** mean that at least one course in that comma separated list must be taken as a prerequisite. Any two courses or group of courses connect with **&&** mean that both courses must be taken to fulfill requirements. Courses separated by a **/** mean that either one of the courses must be taken as a prerequisite.
**Co-Requisites** | Courses that must be taken at the same time the desired course is being taken.
**Description** | The description of the course objectives

***

### Console Display
The following prerequisite tree for **EE235** is shown below.
Courses connected with a | and that have a * next to them indicates that any one of those courses will fulfill the prerequisite requirement for the course. This can be seen below with **MATH136, MATH307, AMATH351** which each have a * next to them and are all at the same 'level' in the prerequisite tree. The same can be seen for **MATH120**, as **MATH098, MATH103, or MATH109** will suffice to fulfill the prerequisite requirement for that course. 

>There is also an option to scan in the students transcript as a `.txt` file to eliminate any course in the tree that has already been taken by the student.

```
MATH136*
|   MATH135
|   |   MATH134
MATH307*
|   MATH125
|   |   MATH124
|   |   |   MATH120
|   |   |   |   MATH098*
|   |   |   |   MATH103*
|   |   |   |   |   MATH102
|   |   |   |   |   |   MATH100
|   |   |   |   MATH109*
AMATH351*
|   MATH125*
|   |   MATH124
|   |   |   MATH120
|   |   |   |   MATH098*
|   |   |   |   MATH103*
|   |   |   |   |   MATH102
|   |   |   |   |   |   MATH100
|   |   |   |   MATH109*
|   MATH135*
|   |   MATH134

```
There is a space between the **MATH136, MATH307, AMATH351** branch and the **PHYS122** branch. This indicated that in order to take **EE235**, the student must take one of **MATH136, MATH307, or AMATH351** AND **PHYS122**. 
```
PHYS122
|   MATH125*
|   |   MATH124
|   |   |   MATH120
|   |   |   |   MATH098*
|   |   |   |   MATH103*
|   |   |   |   |   MATH102
|   |   |   |   |   |   MATH100
|   |   |   |   MATH109*
|   MATH134*

|   PHYS121
|   |   MATH124*
|   |   |   MATH120
|   |   |   |   MATH098*
|   |   |   |   MATH103*
|   |   |   |   |   MATH102
|   |   |   |   |   |   MATH100
|   |   |   |   MATH109*
|   |   MATH134*
```
Below the **PHYS122** branch **CSE142** and **CSE143** are both shown with a * next to them, indicating that either one of these courses along with one of **MATH136, MATH307, or AMATH351** AND **PHYS122** will fulfill the prerequisite requirement.
```
CSE142*
CSE143*
|   CSE142
```
