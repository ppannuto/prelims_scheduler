import get_data_from_google as gdg 



def greedy_assignment():
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
			is_slot_avail = assmnts[fact][slot] is None 
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
	[fac_avail, student_rankings, slots] = gdg.get_faculty_and_student_data()

	# Do the greedy assignment
	assmnts = greedy_assignment()
	
	# Upload the results to google
	gdg.upload_assignments(assmnts,slots)



