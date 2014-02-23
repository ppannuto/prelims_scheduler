import csv
import gspread
import getpass

DOCID = '0AsY0MoR7nxqgdEl3RlNlNFhiNGFpY1Mwcm91a05QaVE'

def get_faculty_and_student_data():
	# Grab the google spsht data and clean up
	# spsht = login_and_get_ss()
	# [facsht,studsht,asssht] = spsht.worksheets()
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


def main2():
	spsht = get_docid(DOCID)

	[facsht,studsht,asssht] = spsht.worksheets()
	filenames = ['faclist', 'stulist', 'assignment'];

	for i, worksheet in enumerate(spsht.worksheets()):
		avail_hash = worksheet.get_all_records()
	    with open(filenames[i], 'wb') as f:
	        writer = csv.DictWriter(f, )
	        writer.writerows(worksheet.get_all_records())

	# fac_avail = {}
	# slots = None
	# for avail_hash in facsht.get_all_records():
	# 	fac_name = avail_hash.pop(FAC_NAME_HEAD)
	# 	if slots is None:
	# 		slots = avail_hash.keys()
	# 		slots.sort()
	# 	fac_avail[fac_name] = avail_hash

	# csv.DictWriter
	# student_rankings = {}

def main():
	"import the spsht into csv files"
	spsht = get_docid(DOCID)

	filenames = ['faclist', 'stulist', 'assignment'];
	for i, worksheet in enumerate(spsht.worksheets()):
	    with open(filenames[i], 'wb') as f:
	        writer = csv.writer(f)
	        writer.writerows(worksheet.get_all_values())

if __name__ == '__main__':
	main2()
