
import gspread
import getpass

GEMAIL = 'chansoo.eph'
SSHT_URL = 'https://docs.google.com/a/umich.edu/spreadsheet/ccc?key=0AsY0MoR7nxqgdEl3RlNlNFhiNGFpY1Mwcm91a05QaVE'
DOCID = '0AsY0MoR7nxqgdEl3RlNlNFhiNGFpY1Mwcm91a05QaVE'
FAC_NAME_HEAD = 'fac_name'
STUD_NAME_HEAD = 'student_name'
RANK_NUM = 5

def full_login_and_get_ss(docid):
	_user = raw_input('Account name: ')
	_pw = getpass.getpass()

	g = gspread.login(_user, _pw)
	#SSHT_URL = 'https://docs.google.com/a/umich.edu/spsht/ccc?key=0AsY0MoR7nxqgdEl3RlNlNFhiNGFpY1Mwcm91a05QaVE'
	spsht = g.open_by_key(docid)
	return spsht

def login_and_get_ss():
	# Login and return the spreadsheet of interest
	gc = gspread.login(GEMAIL, _pw)
	spsht = gc.open_by_url(SSHT_URL)
	return spsht

def get_faculty_and_student_data():
	# Grab the google spreadsheet data and clean up
	spsht = full_login_and_get_ss(DOCID)
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
	spsht = full_login_and_get_ss(DOCID)
	[facsht,studsht,asssht] = spsht.worksheets()
	faculty = assmnts.keys()
	faculty.sort()
	cells = []
	def lup(row,col,val):
		asssht.update_cell(row,col,val)
		# cell = asssht.cell(row,col)
		# cell.value = val
		# cells.append(cell)
	for sind,slot in enumerate(slots):
		lup(1,sind+2,slot)

	for ind,fac in enumerate(faculty):
		row = ind + 2
		lup(row,1,fac)
		for sind,slot in enumerate(slots):
			if assmnts[fac][slot] is not None: val = assmnts[fac][slot]
			else: val = ""
			lup(row,sind+2,val)

	# asssht.update_cells(cells)

def main():
	[fac_avail, student_rankings, slots] = get_faculty_and_student_data()

	import pprint, pickle
	pkl_file = open('data.pkl', 'wb')

	pickle.dump(fac_avail, pkl_file, -1)
	pickle.dump(student_rankings, pkl_file, -1)
	pickle.dump(slots, pkl_file, -1)
	pkl_file.close()


if __name__ == '__main__':
	main()
