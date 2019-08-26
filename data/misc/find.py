import csv
import sys
import json
import os
# Finds the number of arabidopsis instances in ptm.txt (only 9)
def main(args):
    count = {}
    orgs = {}
    instances = {}
    with open(os.path.abspath('biogrid/ptm.txt')) as f:
        reader = csv.DictReader(f, delimiter='\t')
        for line in reader:
            org = line['Organism ID']
            if not org in count.keys():
                count[org] = 1
                orgs[org] = str(line['Organism Name'])
            else:
                count[org] = int(count[org]) + 1
            
            if len(args) > 1 and org == sys.argv[1]:
                print(json.dumps(line))

        for org in orgs:
            print (str(org) + '\t' + orgs[org] + '\t' + str(count[org]))

if __name__ == '__main__':
    if len(sys.argv) == 1:
        sys.exit('Error: must include path!')
    main(sys.argv) 
