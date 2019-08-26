from models import Interactome
import networkx as nx
import csv
import pickle as pk
import os
import json

BIOGRID_TAB2_FILENAME = os.path.abspath("../data/biogrid.txt")
NEW_PICKLE = os.path.abspath("../data/newpickle2.p3")

BIOGRID_TAB2_NODE1_LABEL = "INTERACTOR_A"
BIOGRID_TAB2_NODE2_LABEL = "INTERACTOR_B"

ORG1 = "ORGANISM_A_ID"
ORG2 = "ORGANISM_B_ID"

interactome = Interactome()

def set_graph_from_file():
    with open(BIOGRID_TAB2_FILENAME) as f:
        reader = csv.DictReader(f, delimiter='\t')
        data = list(reader)

    G = nx.Graph()
    for line in data:
        if int(line[ORG1]) == 3702 and int(line[ORG2]) == 3702:

            node1 = line[BIOGRID_TAB2_NODE1_LABEL]
            G.add_node(node1)
            G.nodes[node1]['biogrid'] = {
                    'INTERACTOR': line['INTERACTOR_A'],
                    'OFFICIAL_SYMBOL': line['OFFICIAL_SYMBOL_A'],
                    'ALIASES': line['ALIASES_FOR_A'],
                    'ORGANISM': line['ORGANISM_A_ID']
            }

            node2 = line[BIOGRID_TAB2_NODE2_LABEL]
            G.add_node(node2)
            G.nodes[node2]['biogrid'] = {
                    'INTERACTOR': line['INTERACTOR_B'],
                    'OFFICIAL_SYMBOL': line['OFFICIAL_SYMBOL_B'],
                    'ALIASES': line['ALIASES_FOR_B'],
                    'ORGANISM': line['ORGANISM_B_ID']
            }

            G.add_edge(node1, node2)
            G.edges[node1, node2]['biogrid'] = line
    
    nx.write_gpickle(G, NEW_PICKLE)    

set_graph_from_file()
