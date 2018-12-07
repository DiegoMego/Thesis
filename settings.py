import os

current_folder = os.path.dirname(__file__)
report_file = "report.txt"
temp_folder = "temp\\"
temp_foldername = "temp"
py_ext = ".py"
program_file = "TRITYP"
test_file = "TRITYP_test"
original = "original"
command = "mut.py --target {} -u {} -m".format(temp_foldername + "." + original, test_file)
main = "main"
