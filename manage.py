
# import getpass
# # import gdata.docs.service
# import gdata.spreadsheet.service

# # client = gdata.docs.service.DocsService()
# print "please enter your Google Apps password: "
# client.ClientLogin('jabernet@umich.edu',getpass.getpass())

# documents_feed = client.GetDocumentListFeed()
# for document_entry in documents_feed.entry:
#   # Display the title of the document on the command line.
#   print document_entry.title.text

# Useful page: http://www.payne.org/index.php/Reading_Google_Spreadsheets_in_Python

# gdc = gdata.spreadsheet.service.SpreadsheetsService()
# gdc.password = getpass.getpass()
# gdc.email = 'jakeyboy@gmail.com'
# gdc.ProgrammaticLogin()
# fee = gdc.GetSpreadsheetsFeed()
# q = gdata.spreadsheet.service.DocumentQuery()
# q['title'] = 'Faculty Visit Day Availability'
# q['title-exact'] = 'true'
# feed = gdc.GetSpreadsheetsFeed(query=q)
# spid = feed.entry[0].id.text.rsplit('/',1)[1]
# feed = gdc.GetWorksheetsFeed(spid)
# woid = feed.entry[0].id.text.rsplit('/',1)[1]
# rows = gdc.GetListFeed(spid,woid).entry

# for row in rows:
#         for key in row.custom:
#                 print " %s: %s" % (key, row.custom[key].text)
# print "\n"

# gc = gspread.login('jakeyboy@gmail.com', getpass.getpass())

# sht = gc.open_by_url('https://docs.google.com/a/umich.edu/spreadsheet/ccc?key=0AsY0MoR7nxqgdEl3RlNlNFhiNGFpY1Mwcm91a05QaVE')

import get_data_from_google as gdg 

[fac_avail, student_rankings, slots] = gdg.get_faculty_and_student_data()

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
		# returns success and the slot that was found
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
		# we loop until we were unable to fill any slots
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

assmnts = greedy_assignment()

gdg.upload_assignments(assmnts,slots)



