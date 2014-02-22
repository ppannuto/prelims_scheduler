
import gspread
import getpass

_pw = getpass.getpass()
GEMAIL = 'jakeyboy@gmail.com'
SSHT_URL = 'https://docs.google.com/a/umich.edu/spreadsheet/ccc?key=0AsY0MoR7nxqgdEl3RlNlNFhiNGFpY1Mwcm91a05QaVE'
FAC_NAME_HEAD = 'fac_name'
STUD_NAME_HEAD = 'student_name'
RANK_NUM = 5

def login_and_get_ss():
	# Login and return the spreadsheet of interest
	gc = gspread.login('jakeyboy@gmail.com', _pw)
	spsht = gc.open_by_url(SSHT_URL)
	return spsht

def get_faculty_and_student_data():
	# Grab the google spreadsheet data and clean up
	spsht = login_and_get_ss()
	[facsht,studsht,asssht] = spsht.worksheets()
	fac_avail = {}
	slots = None
	for avail_hash in facsht.get_all_records():
		fac_name = avail_hash.pop(FAC_NAME_HEAD)
		if slots is None:
			slots = avail_hash.keys()
			slots.sort()
		fac_avail[fac_name] = avail_hash

	student_rankings = {}

	for rank_hash in studsht.get_all_records():
		student_name = rank_hash.pop(STUD_NAME_HEAD)
		student_rankings[student_name] = [rank_hash[str(ind)] for ind in range(1,RANK_NUM+1)]

	return [fac_avail, student_rankings, slots]

def upload_assignments(assmnts,slots):
	spsht = login_and_get_ss()
	[facsht,studsht,asssht] = spsht.worksheets()
	faculty = assmnts.keys()
	faculty.sort()
	cells = []
	def lup(row,col,val):
		cell = asssht.cell(row,col)
		cell.value = val
		cells.append(cell)
	for sind,slot in enumerate(slots):
		lup(1,sind+2,slot)

	for ind,fac in enumerate(faculty):
		row = ind + 2
		lup(row,1,fac)
		for sind,slot in enumerate(slots):
			if assmnts[fac][slot] is not None: val = assmnts[fac][slot]
			else: val = ""
			lup(row,sind+2,val)

	asssht.update_cells(cells)


