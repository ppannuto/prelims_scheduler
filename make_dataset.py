import numpy as np
import random

NUMFAC = 40
NUMSTU = 32
NUMSLOT = 20

faculty = ["facmem_%i" % ind for ind in range(NUMFAC)]

students = ["student_%i" % ind for ind in range(NUMSTU)]

slots = range(NUMSLOT)

assments = {facmem : {slotid : None for slotid in slots} for facmem in faculty}

fac_avail = {facmem : [slot for slot in slots if random.random() < 0.60] 
	for facmem in faculty}

for fac in faculty:
	for slot in slots:
		if slot not in fac_avail[fac]:
			assments[fac][slot] = "N/A"

stucounts = {student : 0 for student in students}
faccounts = {fac: 0 for fac in faculty}

while True:
	for stud in students:
		fac = random.choice(faculty)
		slot = random.choice(fac_avail[fac])
		if assments[fac][slot] is None:
			assments[fac][slot] = stud
			stucounts[stud] += 1
			faccounts[fac] += 1
	lowest_stu_count = min(stucounts.values())
	lowest_fac_count = min(faccounts.values())
	if (lowest_fac_count > 3) and (lowest_stu_count > 4):
		break


student_rankings = {student : set([]) for student in students}

while True:
	fac = random.choice(faculty)
	slot = random.choice(slots)
	if (assments[fac][slot] is not None) and (assments[fac][slot] is not "N/A"):
		student = assments[fac][slot]
		# assments[fac][slot] = None
		if (len(student_rankings[student]) < 5):
			student_rankings[student].add(fac)
	if min([len(s) for s in student_rankings.values()]) > 4:
		break

rankings = {student: list(ranking) for student,ranking in student_rankings.items()}

data = {'faculty_names' : faculty, 
'faculty_availability' : fac_avail, 
'legal_assignment' : assments, 
'student_names' : students,
'slots' : slots,
'student_rankings': rankings}

# import pickle
# with open("random_ranking_availability_data.pkl", "w+") as output:
# 	pickle.dump(data, output)

import gspread
import getpass

gc = gspread.login('jakeyboy@gmail.com', getpass.getpass())

spsht = gc.open_by_url('https://docs.google.com/a/umich.edu/spreadsheet/ccc?key=0AsY0MoR7nxqgdEl3RlNlNFhiNGFpY1Mwcm91a05QaVE')

[facsht,studsht] = spsht.worksheets()

for ind,fac in enumerate(faculty):
	row = ind + 2
	facsht.update_cell(row,1,fac)
	for slot in slots:
		avail = 0
		if slot in fac_avail[fac]: avail = 1
		col = slot + 2
		facsht.update_cell(row,col,avail)

for ind,stud in enumerate(students):
	row = ind + 2
	studsht.update_cell(row,1,stud)
	for fin,fac in enumerate(rankings[stud]):
		col = fin + 2
		studsht.update_cell(row,col,fac)






