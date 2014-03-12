import get_data_from_google as getgoog
import manage
getgoog.get_and_save_all_data()
data = getgoog.load_all_data()
assments = manage.lp_assignment(data['fac_avail'], data['student_rankings'], data['slots'],RANK=7)
manage.write_to_csv(assments, data['fac_avail'], data['slots'])
