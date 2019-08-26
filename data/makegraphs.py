import networkx as nx
import csv
import pickle as pk
import os
import json
from networkx.algorithms import community

# https://wiki.thebiogrid.org/doku.php/biogrid_ptmtab_ptmrel
# https://wiki.thebiogrid.org/doku.php/biogrid_tab_version_2.0

TAB2_LABEL1 = "Systematic Name Interactor A"
TAB2_LABEL2 = "Systematic Name Interactor B"

ORG1 = "Organism Interactor A"
ORG2 = "Organism Interactor B"

SOURCE = "Source Database"


def set_graph_from_file(tab2_filename, pickle_filename):

    print('Reading original/tab2')
    # tab2: has a list of interactions
    organisms = {}
    i = 0
    with open(tab2_filename) as f:
        reader = csv.DictReader(f, delimiter='\t')
        for line in reader:
            i += 1
            if (i % 10000 == 0):
                print('Number: ' + str(i))

            if not line[ORG1] or not line[ORG2] or not line[ORG1] == line[ORG2]:
                continue

            if not line[TAB2_LABEL1] or not line[TAB2_LABEL2]:
                continue

            if not line[ORG1] in organisms.keys():
                organisms[line[ORG1]] = nx.Graph()

            G = organisms[line[ORG1]]

            node1 = line[TAB2_LABEL1]
            node2 = line[TAB2_LABEL2]
            source = line[SOURCE]

            if not G.has_node(node1):
                G.add_node(node1)
                G.nodes[node1]['info'] = {}
                G.nodes[node1]['info']['tab2'] = {}

            # Add each dict to avoid a key error
            G.nodes[node1]['info']['tab2'][source] = {}
            G.nodes[node1]['info']['tab2'][source] = {
                'Entrez Gene Interactor': line['Entrez Gene Interactor A'],
                'BioGRID ID Interactor': line['BioGRID ID Interactor A'],
                'Systematic Name Interactor':
                line['Systematic Name Interactor A'],
                'Official Symbol Interactor':
                line['Official Symbol Interactor A'],
                'Synonyms Interactor': line['Synonyms Interactor A']
            }

            if not G.has_node(node2):
                G.add_node(node2)
                G.nodes[node2]['info'] = {}
                G.nodes[node2]['info']['tab2'] = {}

            G.nodes[node2]['info']['tab2'][source] = {
                'Entrez Gene Interactor': line['Entrez Gene Interactor B'],
                'BioGRID ID Interactor': line['BioGRID ID Interactor B'],
                'Systematic Name Interactor':
                line['Systematic Name Interactor B'],
                'Official Symbol Interactor':
                line['Official Symbol Interactor B'],
                'Synonyms Interactor': line['Synonyms Interactor B']
            }

            if not G.has_edge(node1, node2):
                G.add_edge(node1, node2)
                G.edges[node1, node2]['info'] = {}
                G.edges[node1, node2]['info']['tab2'] = {}
                G.edges[node1, node2]['experimental'] = {}

            system = line['Experimental System']
            systype = line['Experimental System Type']
            if not systype in G.edges[node1, node2]['experimental'].keys():
                G.edges[node1, node2]['experimental'][systype] = {}

            if not system in G.edges[node1,
                                     node2]['experimental'][systype].keys():
                G.edges[node1, node2]['experimental'][systype][system] = 0

            G.edges[node1, node2]['experimental'][systype][system] += 1

            bioID = line['Pubmed ID']
            G.edges[node1, node2]['info']['tab2'][bioID] = line

    for org in organisms:
        print('Org: ' + org)
        graph = organisms[org]
        nx.write_gpickle(graph, pickle_filename + str(org) + '.p3')


'''
        for nodelist in community.greedy_modularity_communities(graph):
            for node in nodelist:
                graph.nodes[node]['bio-cluster'] = i
            i += 1

        for a, b in graph.edges:
            graph.edges[a, b]['bio-cluster-a'] = graph.nodes[a]['bio-cluster']
            graph.edges[a, b]['bio-cluster-b'] = graph.nodes[b]['bio-cluster']
'''
