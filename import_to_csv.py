import csv
import gspread
import getpass

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


def main():
	"import the spreadsheet into csv files"
	_user = raw_input('Account name: ')
	_pw = getpass.getpass()

	g = gspread.login(_user, _pw)

	docid = '0AsY0MoR7nxqgdEl3RlNlNFhiNGFpY1Mwcm91a05QaVE'
	#SSHT_URL = 'https://docs.google.com/a/umich.edu/spreadsheet/ccc?key=0AsY0MoR7nxqgdEl3RlNlNFhiNGFpY1Mwcm91a05QaVE'
	spreadsheet = g.open_by_key(docid)

	filenames = ['faclist', 'stulist', 'assignment'];
	for i, worksheet in enumerate(spreadsheet.worksheets()):
	    with open(filenames[i], 'wb') as f:
	        writer = csv.writer(f)
	        writer.writerows(worksheet.get_all_values())

if __name__ == '__main__':
	main()
