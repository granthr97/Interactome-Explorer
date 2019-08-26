import csv
import sys
import json
import os
TAB2_LABEL1 = "Systematic Name Interactor A"
TAB2_LABEL2 = "Systematic Name Interactor B"
ORG1 = "Organism Interactor A"
ORG2 = "Organism Interactor B"
ARABIDOPSIS_ID = 3702
# Finds the number of arabidopsis instances in ptm.txt (only 9)
def main(args):
    with open(os.path.abspath('biogrid/tab2.txt')) as f:
        reader = csv.DictReader(f, delimiter='\t')
        for line in reader:

            if not line[ORG1] or not line[ORG2]:
                continue

            if int(line[ORG1]) != ARABIDOPSIS_ID or int(line[ORG2]) != ARABIDOPSIS_ID:
                continue

            if line[TAB2_LABEL1] == line[TAB2_LABEL2]:
                print(line[TAB2_LABEL1])

if __name__ == '__main__':
    main(sys.argv) 
