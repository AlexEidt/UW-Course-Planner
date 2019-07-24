# UW Course Tool

 Search for any course offered at any one of the three UW Campuses and see a full tree of prerequisites for that course. There is also an option to scan in your transcript as a `.txt` file to eliminate any course in the tree that has already been taken. 

***

**Always make sure to check the actual prerequisites for any course before making a decision on which course to take!**

***

### UW Course Catalogs
 >[Bothell](http://www.washington.edu/students/crscatb/)                             
 [Seattle](http://www.washington.edu/students/crscat/)                                
 [Tacoma](http://www.washington.edu/students/crscatt/) 

### Prerequisite Tree
A prerequisite tree for any course offered at the UW can be created as a PNG file or in the console (see below).
The prerequisite tree for **EE235** as a PNG is shown below.

All courses at the same 'level' in the tree are the same color. Courses with the same shape at the end of the arrow
indicate that **ONE** of those courses is enough to statisfy the prerequisite requirement. 

<p align = "center">
    <img src = "Prereq Trees/EE235.png" width = 600 alt="EE235 Prerequisite Tree">
</p>

### Console Display
The following prerequisite tree for **EE235** is shown below.
Courses connected with a | and that have a * next to them indicates that any one of those courses will fulfill the prerequisite requirement for the course. This can be seen below with **MATH136, MATH307, AMATH351** which each have a * next to them and are all at the same 'level' in the prerequisite tree. The same can be seen for **MATH120**, as **MATH098, MATH103, or MATH109** will suffice to fulfill the prerequisite requirement for that course. 

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

***

Course Data | Description 
:--- | ---
**Campus** | The campus the course is offered at
**Department Name** | The name of the department the course is a part of. Denoted by a series of capital letters with no spaces.
**Course Number** | The 3 digit number identifying the course.
**Course Name** | The name of the course
**Credits** | The number of credits offered for the course. Some courses have variable credits offered/different credit options. Check out the UW's guide for the credit system [here](http://www.washington.edu/students/crscat/glossary.html)
**Areas of Knowledge** | Areas of Knowledge essentially are credit types. [More Information](https://www.washington.edu/uaa/advising/degree-overview/general-education/)
**Quarters Offered** | The quarters of the year the course is offered. **A**utumn, **W**inter, **Sp**ring, **S**ummer.
**Offered with** | At times, a course may be offered alongside a similar course in a different department. 
**Prerequisites** | Courses that must be taken in order to take the course. 
**Co-Requisites** | Courses that must be taken at the same time the desired course is being taken.
**Description** | The description of the course objectives

***

### Requirements/Dependencies
Python 3.7
```
 - tqdm         [pip install tqdm]
 - bs4          [pip install bs4]
 - Graphviz     [pip install graphviz]
```
In order for the visual representation with Graphviz to work, [Graphviz](https://graphviz.gitlab.io/download/) must be downloaded. Once downloaded go to `create_tree.py` and change the System Path under `GRAPHVIZ PATH SETUP`
Make sure to add the `bin` folder of the downloaded Graphviz folder to the end of the system path.

```python
# --------------------------GRAPHVIZ PATH SETUP-------------------------- #
os.environ["PATH"] += os.pathsep + [FILE PATH TO GRAPHVIZ bin FOLDER] 
# ----------------------------------------------------------------------- #
```

#### 'Graphviz Executables not on system Path' Error
If this error comes up try:
```
pip install graphviz
```
followed by:
```
conda install graphviz
```

If the error persists:

##### MAC:
```
brew install graphviz
```
##### Ubuntu
```
sudo apt-get install graphviz
```
