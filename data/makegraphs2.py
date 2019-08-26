import networkx as nx
import csv
import pickle
import os
import json
from networkx.algorithms import community

# https://wiki.thebiogrid.org/doku.php/biogrid_ptmtab_ptmrel
# https://wiki.thebiogrid.org/doku.php/biogrid_tab_version_2.0

TAB2_FILENAME = os.path.abspath("./tab2.txt")
NEW_PICKLE = os.path.abspath("./graphs2/")

ENTREZ_ID_A = "Entrez Gene Interactor A"
ENTREZ_ID_B = "Entrez Gene Interactor B"
BIOGRID_ID_A = "BioGRID ID Interactor A"
BIOGRID_ID_B = "BioGRID ID Interactor B"
SYSTEMATIC_ID_A = "Systematic Name Interactor A"
SYSTEMATIC_ID_B = "Systematic Name Interactor B"
OFFICIAL_SYMBOL_A = "Official Symbol Interactor A"
OFFICIAL_SYMBOL_B = "Official Symbol Interactor B"
SYNONYMS_A = "Synonyms Interactor A"
SYNONYMS_B = "Synonyms Interactor B"
ORG_ID_A = "Organism Interactor A"
ORG_ID_B = "Organism Interactor B"
EXPERIMENTAL_SYSTEM_TYPE = "Experimental System Type"
EXPERIMENTAL_SYSTEM = "Experimental System"
SOURCE = "Source Database"
PUBID = 'Pubmed ID'


def set_graph_from_file():

    organisms = {}  # Maps organism IDs to their NetworkX graphs
    ID_map = {}     # Maps any identiier to the associated Biogrid ID 
    with open(TAB2_FILENAME) as f:
        reader = csv.DictReader(f, delimiter='\t')
        
        i = 0
        for line in reader:
            i += 1
            if (i % 5000 == 0):
                print('Line ' + str(i))

            orgA = line[ORG_ID_A]
            orgB = line[ORG_ID_B]
            bioA = line[BIOGRID_ID_A]
            bioB = line[BIOGRID_ID_B] 

            if '-' in [orgA, orgB, bioA, bioB]: # Ignore entries with blank organism IDs or Biogrid IDs
                continue

            for org in set([orgA, orgB]): # Don't repeat for the same organism

                if orgA not in ID_map.keys():
                    ID_map[org] = {}

                for key in [line[SYSTEMATIC_ID_A], line[OFFICIAL_SYMBOL_A], line[BIOGRID_ID_A]]:
                    if key == '-':
                        continue
                    elif key in ID_map[orgA].keys() and ID_map[orgA][key] != bioA:
                        print('Duplicate key: ' + key + '-> ' + ID_map[orgA][key] + ', ' + bioA)
                    else:
                        ID_map[orgA][key] = bioA

                for key in [line[SYSTEMATIC_ID_B], line[OFFICIAL_SYMBOL_B], line[BIOGRID_ID_B]]:
                    if key == '-':
                        continue
                    elif key in ID_map[orgB].keys() and ID_map[orgB][key] != bioB:
                        print('Duplicate key: ' + key + '-> ' + ID_map[orgB][key] + ', ' + bioA)
                    else:
                        ID_map[orgB][key] = bioB

                if not org in organisms.keys():
                    organisms[org] = nx.Graph() # Instantiate empty graphs for new organisms

                G = organisms[org] 

                source = line[SOURCE]

                for bio_id in set([bioA, bioB]):
                    if not G.has_node(bio_id):
                        G.add_node(bio_id)
                
                G.nodes[bioA][source] = {
                        'Entrez Gene Interactor': line[ENTREZ_ID_A],
                        'BioGRID ID Interactor': line[BIOGRID_ID_A],
                        'Systematic Name Interactor': line[SYSTEMATIC_ID_A],
                        'Official Symbol Interactor': line[OFFICIAL_SYMBOL_A],
                        'Synonyms Interactor': line[SYNONYMS_A]
                } 

                G.nodes[bioB][source] = {
                        'Entrez Gene Interactor': line[ENTREZ_ID_B],
                        'BioGRID ID Interactor': line[BIOGRID_ID_B],
                        'Systematic Name Interactor': line[SYSTEMATIC_ID_B],
                        'Official Symbol Interactor': line[OFFICIAL_SYMBOL_B],
                        'Synonyms Interactor': line[SYNONYMS_B]
                }

                if not G.has_edge(bioA, bioB):
                    G.add_edge(bioA, bioB)
                    G.edges[bioA, bioB]['experimental'] = {}
                    G.edges[bioA, bioB]['sources'] = []

                if not line[EXPERIMENTAL_SYSTEM_TYPE] in G.edges[bioA, bioB]['experimental'].keys():
                    G.edges[bioA, bioB]['experimental'][EXPERIMENTAL_SYSTEM_TYPE] = {}

                if not line[EXPERIMENTAL_SYSTEM] in G.edges[bioA, bioB]['experimental'][EXPERIMENTAL_SYSTEM_TYPE].keys():
                    G.edges[bioA, bioB]['experimental'][EXPERIMENTAL_SYSTEM_TYPE][EXPERIMENTAL_SYSTEM] = 0

                G.edges[bioA, bioB]['experimental'][EXPERIMENTAL_SYSTEM_TYPE][EXPERIMENTAL_SYSTEM] += 1

                G.edges[bioA, bioB]['sources'].append(line) 

    print(json.dumps(ID_map))

    for org in organisms:
        print('Org: ' + org)
        graph = organisms[org]

        for nodelist in community.greedy_modularity_communities(graph):
            for node in nodelist:
                graph.nodes[node]['bio-cluster'] = i
            i += 1

        for a, b in graph.edges:
            graph.edges[a, b]['bio-cluster-a'] = graph.nodes[a]['bio-cluster']
            graph.edges[a, b]['bio-cluster-b'] = graph.nodes[b]['bio-cluster']

        nx.write_gpickle(graph, os.path.abspath('./graphs2/' + str(org) + '.p3'))

    for orgmap in ID_map:
        path = os.path.abspath('./ID_maps/' + str(orgmap) + '.p3')
        with open(path, 'wb') as mapfile:
            pickle.dump(ID_map[orgmap], mapfile, protocol=pickle.HIGHEST_PROTOCOL)
    

set_graph_from_file()
