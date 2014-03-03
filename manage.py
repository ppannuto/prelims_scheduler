import get_data_from_google as gdg 
from pulp import *
TOL = 0.0001
ENSURE_NUM_AVAIL = 1
MIN_MEETINGS_PER_STUD = 2

def lp_assignment(fac_avail, student_rankings, slots, RANK = 5):
	facs = fac_avail.keys()
	stus = student_rankings.keys()
	prob = LpProblem("Meeting assignment", LpMinimize)
	lp_assmnts = LpVariable.dicts("Assignment", (facs, stus, slots), 0, 1)

	# objective function
	rank_weights = [-10, -5, -2, -1, -1, -1, -1, -1, -1]

	tuples = []

	for stu in stus:		
		for i in xrange(len(student_rankings[stu])):
			for slot in slots:
				tuples.append((lp_assmnts[student_rankings[stu][i]][stu][slot], rank_weights[i]))

	prob += LpAffineExpression(tuples), "preference-weighted"

	# TIme constraint
	for slot in slots:
		for fac in facs:
			if fac_avail[fac][slot]:
				# faculty meets only one person
				prob += lpSum([lp_assmnts[fac][stu][slot] for stu in stus]) <= 1, ""
			else:
				# faculty is busy
				prob += lpSum([lp_assmnts[fac][stu][slot] for stu in stus]) <= 0, ""
		for stu in stus:
			# each students meets only one faculty per slot
			prob += lpSum([lp_assmnts[facc][stu][slot] for facc in facs]) <= 1, ""

	# no student wants to meet the same person twice
	for fac in facs:
		for stu in stus:
			prob += lpSum([lp_assmnts[fac][stu][slot] for slot in slots]) <= 1, ""

	# every student should meet with at least MIN_MEETINGS_PER_STUD faculty members
	for stu in stus:
		prob += lpSum([lp_assmnts[fac][stu][slot] for fac in facs for slot in slots]) >= MIN_MEETINGS_PER_STUD, ""

	# To ensure some flexibility, we ensure that each faculty member has at least some open slots
	for fac in facs:
		totslots = sum(fac_avail[fac].values()) - ENSURE_NUM_AVAIL
		print fac
		print totslots
		prob += lpSum([lp_assmnts[fac][stu][slot]
						for stu in stus
						for slot in slots]) <= totslots, ""

	prob.writeLP('assignment.lp')
	prob.solve()
	print LpStatus[prob.status]
#	prob.roundSolution()

	# import pdb; pdb.set_trace()

	for v in prob.variables():
		if v.varValue >= TOL:
			print "Var %s has val %f" % (v.getName(), v.varValue)
			if v.varValue < 0.99:
				print "============================="
				print "=====FOUND NONINT VALUE======"
				print "============================="

	assmnts = {}
	for fac in facs:
		assmnts[fac] = {slot : None for slot in slots}
	 	for slot in slots:
	 		if fac_avail[fac][slot]:
		 		assmnts[fac][slot] = ""
		 		for stu in stus:
			 		if value(lp_assmnts[fac][stu][slot]) == 1:
		 				assmnts[fac][slot] = stu
		 	else:
		 		assmnts[fac][slot] = "Busy"


	return assmnts

    
def greedy_assignment(fac_avail, student_rankings, slots):
	assmnts = {}
	faculty = fac_avail.keys()
	students = student_rankings.keys()
	student_avail = {stud: set() for stud in students}

	for fac in faculty: 
		# By default, the assmnts[fac] is a hash with:
		#     None entries when not assigned and 
		#     N/A entries when unavailable
		assmnts[fac] = {slot : None for slot in slots}
		for slot in slots:
			if fac_avail[fac][slot] == 0:
				assmnts[fac][slot] = "N/A"


	def assign(stud,fac):
		# tries to assign the student to one of the faculty slots
		# if possible, returns success=True and the slot that was found
		success = False		
		for slot in slots:
			# Check necessary conditions if we can assign this student to this fac member
			is_fac_avail = fac_avail[fac][slot]
			is_slot_avail = assmnts[fac][slot] is None 
			is_stud_avail = (slot in student_avail[stud])
			slot = None
			if is_fac_avail and is_stud_avail and is_slot_avail:
				assmnts[fac][slot] = stud 
				success = True 
				break
		return success, slot 

	notdone = True
	while notdone: 
		# we loop until we were unable to fill any slots for any student
		notdone = False
		
		for stud in students:
			if student_rankings[stud]:
				# Get the next faculty member on the student's list
				# Then try to assign this fac to the student
				# If success, record the assignment
				# make sure to pop this fac off the student's list
				fac = student_rankings[stud][0]
				success,slot = assign(stud,fac)
				if success: student_avail[stud].add(slot)
				student_rankings[stud].remove(fac)
				notdone = notdone or success

	return assmnts


if __name__ == '__main__':
	# Get the faculty availability and student ranking data from google
	# import pickle
	# pkl_file = open('data.pkl', 'rb')
	# fac_avail = pickle.load(pkl_file)
	# student_rankings = pickle.load(pkl_file)
	# slots = pickle.load(pkl_file)
	[fac_avail, student_rankings, slots] = gdg.get_faculty_and_student_data()
		# pprint.pprint(data1)
	# data2 = pickle.load(pkl_file)
	# pprint.pprint(data2)
	# # Do the greedy assignment
	assmnts = lp_assignment(fac_avail, student_rankings, slots)

#	print assmnts

	# with open('assignment.csv', 'wb') as csvfile:
	# 	import csv
	# 	slots.insert(0, 'name')
	# 	writer = csv.DictWriter(csvfile, slots)
	# 	writer.writeheader()
	# 	for fac in fac_avail.keys():
	# 		import copy

	# 		row = copy.deepcopy(assmnts[fac])
	# 		row['name'] = fac
	# 		writer.writerow(row)

#	print assmnts
	
	# # Upload the results to google
	print "uploading to google"
	gdg.upload_assignments(assmnts,slots)



