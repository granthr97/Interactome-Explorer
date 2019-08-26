import csv
import requests
import json
import networkx as nx
import csv
import pickle as pk
import os
import copy
from networkx.algorithms import community
import logging
import numpy as np
import glob
from api.helper_models import AdaptiveInteractomeHelper

logger = logging.getLogger('testlogger')

BIOGRID_KEY = "39557a40f8059e8b4adbf4e0286cd02b"
JONES_CSV_FILENAME = os.path.abspath("data/jones_data.csv")
BIOGRID_TAB2_FILENAME = os.path.abspath("data/biogrid.txt")
GRAPH_DIRECTORY = os.path.abspath("data/graphs") + '/'
JONES_CSV_NODE1_LABEL = "Bait Locus"
JONES_CSV_NODE2_LABEL = "Prey Locus"
BIOGRID_TAB2_NODE1_LABEL = "OFFICIAL_SYMBOL_A"
BIOGRID_TAB2_NODE2_LABEL = "OFFICIAL_SYMBOL_B"

EXPERIMENT_WEIGHTS = {
    "Affinity Capture-Luminescence": 0.5,
    "Affinity Capture-MS": 0.5,
    "Affinity Capture-RNA": 0.7,
    "Affinity Capture-Western": 0.5,
    "Biochemical Activity": 0.5,
    "Co-crystal Structure": 0.99,
    "Co-fractionation": 0.7,
    "Co-localization": 0.7,
    "Co-purification": 0.7,
    "Far Western": 0.5,
    "FRET": 0.5,
    "PCA": 0.3,
    "Protein-peptide": 0.7,
    "Protein-RNA": 0.3,
    "Proximity Label-MS": 0.3,
    "Reconstituted Complex": 0.3,
    "Two-hybrid": 0.3,
}

INTERACTIONS_WEIGHTS = {
    "Dosage Growth Defect": 0.3 * 0.7,
    "Dosage Lethality": 0.3 * 0.7,
    "Dosage Rescue": 0.5 * 0.7,
    "Negative Genetic": 0.99 * 0.7,
    "Phenotypic Enhancement": 0.45 * 0.7,
    "Phenotypic Suppression": 0.75 * 0.7,
    "Positive Genetic": 0.99 * 0.7,
    "Synthetic Growth Defect": 0.99 * 0.7,
    "Synthetic Haploinsufficiency": 0.99 * 0.7,
    "Synthetic Lethality": 0.99 * 0.7,
    "Synthetic Rescue": 0.99 * 0.7
}


class Interactome():
    '''
    Interactome() is a class that retrieves graph information from a specific organism,
    filters that information, integrates user-provided information, performs searches
    in those graphs, and returns formatted data.
    '''

    def __init__(self,
                 orgID=3702,
                 threshold=0.7,
                 scale=1,
                 weight_map=EXPERIMENT_WEIGHTS,
                 input_graph=None,
                 source_label=None,
                 target_label=None,
                 data_source=None,
                 source_attributes=[],
                 target_attributes=[],
                 depth=0,
                 protein=None):
        self.depth = depth

        if input_graph is not None:
            self.set_input_graph(input_graph, source_label, target_label,
                                 data_source, source_attributes,
                                 target_attributes)
        elif protein is not None:
            input_graph = nx.Graph()
            input_graph.add_node(protein)
            self.input_graph = input_graph
        self.set_biogrid_graph(orgID, threshold, scale, weight_map)

    def get_biogrid_graph(self):
        return self.biogrid_graph

    def set_biogrid_graph(self,
                          orgID=3702,
                          threshold=None,
                          scale=None,
                          weight_map=None):
        path = GRAPH_DIRECTORY + str(orgID) + '.p3'
        self.biogrid_graph = nx.read_gpickle(path)
        if threshold is not None:
            self.set_pruned_graph(threshold, scale)

    def set_pruned_graph(self, threshold=0.7, scale=0.5):
        threshold = float(threshold)

        assert threshold >= 0 and threshold <= 1

        def CD(G, u, v):
            Nu = set(list(G.neighbors(u)) + [u])
            Nv = set(list(G.neighbors(v)) + [v])
            return len(
                Nu.symmetric_difference(Nv)) / (len(Nu & Nv) + len(Nu | Nv))

        pruned = self.biogrid_graph.copy()
        weights = [CD(pruned, u, v) for u, v in pruned.edges]
        source_nodes = self.input_graph.nodes
        depth = self.depth

        adaptive_helper = AdaptiveInteractomeHelper(threshold, pruned, weights,
                                                    source_nodes, depth)
        adaptive_threshold = adaptive_helper.get_adaptive_threshold()
        # logger.info("actual_threshold: {}, adaptive_threshold: {}".format(
        #   threshold, adaptive_threshold))

        edges = [(u, v) for u, v in pruned.edges
                 if CD(pruned, u, v) > adaptive_threshold]
        pruned.remove_edges_from(edges)
        self.biogrid_pruned = pruned

    def set_input_graph(self,
                        data,
                        source_label,
                        target_label,
                        data_source='local',
                        source_attributes=[],
                        target_attributes=[]):
        self.input_graph = self.graph_from_dict(
            data, source_label, target_label, data_source, source_attributes,
            target_attributes)

    def graph_from_dict(self,
                        data,
                        source_label,
                        target_label,
                        data_source='local',
                        source_attributes=[],
                        target_attributes=[]):
        """
        Create and return a NetworkX graph from a Python dict.
        Parameters:
            data (dict): list of protein interactions
            source_label, target_label (strings): Required strings representing the key in the data
                that tracks the ID for each node, e.g. "Bait Locus" or "Prey Locus"
            data_source (string): Optional way to track where this information came from
                in each node and edge of the resulting graph
            source_attributes, target_attributes (lists): Optional list of keys in the data for attributes
                associated with the source and target nodes, e.g. "Bait Name" or "Prey Description"
        """
        G = nx.Graph()
        for row in data:
            if source_label not in row or target_label not in row:
                continue
            source = row[source_label]
            target = row[target_label]

            if source == "" or target == "":
                continue

            G.add_edge(source, target)
            G.edges[source, target][data_source] = row
            G.nodes[source][data_source] = {}
            G.nodes[target][data_source] = {}
            for attribute in source_attributes:
                G.nodes[source][data_source][attr] = data[attr]
            for attribute in target_attributes:
                G.nodes[target][data_source][attr] = data[attr]

        return G

    def graph_from_file(self,
                        filename,
                        delimiter,
                        source_label,
                        target_label,
                        data_source=None,
                        source_attributes=[],
                        target_attributes=[]):
        """
        Create a graph from a file specified by the filename.
        Convenient if the user wants to store and access a file on the server.
        Parameters:
            filename (string): path to the file
            delimiter (char): character in the file that separates values, e.g. '\t', ',', '\n'
            data (dict): list of protein interactions
            source_label, target_label (strings): Required strings representing the key in the data
                that tracks the ID for each node, e.g. "Bait Locus" or "Prey Locus"
            data_source (string): Optional way to track where this information came from
                in each node and edge of the resulting graph
            source_attributes, target_attributes (lists): Optional list of keys in the data for attributes
                associated with the source and target nodes, e.g. "Bait Name" or "Prey Description"
        """
        with open(filename) as f:
            reader = csv.DictReader(f, delimiter=delimiter)
            data = list(reader)
        return graph_from_dict(data, source_label, target_label, data_source,
                               source_attributes, target_attributes)

    def subgraph(self, root, depth, formatted=False):
        self.input_graph = nx.Graph()
        self.input_graph.add_node(root)
        return self.graph_query(depth, formatted)

    def graph_query(self, depth=0, formatted=False):
        """
        Perform a breadth-first search self.biogrid_graph on each node of in input_graph using specified depth.
        Integrate the results and attributes of each search with the original input_graph.
        Parameters:
            depth (int): Degree to which we find nodes in each search
            formatted (bool): Whether we want the result formatted for Cytoscape
        """
        biogrid = self.biogrid_graph
        pruned = self.biogrid_pruned
        input_graph = self.input_graph
        bfs = nx.Graph()
        for node in input_graph:
            if pruned.has_node(node):
                if depth > 0:
                    edges = nx.bfs_edges(
                        G=self.biogrid_pruned,
                        source=node,
                        reverse=False,
                        depth_limit=depth)
                    bfs.add_edges_from(edges)
                else:
                    bfs.add_node(node)
        result = pruned.subgraph(bfs.nodes)
        result = nx.compose(input_graph, result)

        for u, v in input_graph.edges:
            if biogrid.has_edge(u, v):
                for key in biogrid.edges[u, v]:
                    result.edges[u, v][key] = biogrid.edges[u, v][key]
            for key in input_graph.edges[u, v]:
                result.edges[u, v][key] = input_graph.edges[u, v][key]

        for node in input_graph:
            if biogrid.has_node(node):
                for key in biogrid.nodes[node]:
                    result.nodes[node][key] = biogrid.nodes[node][key]
            for key in input_graph.nodes[node]:
                result.nodes[node][key] = input_graph.nodes[node][key]

        return self.format(result) if formatted else result

    def format(self, graph, clusters=True):
        if len(graph.nodes()) > 1 and clusters:
            i = 0

            def randomcolor():
                c = '#'
                for i in range(3):
                    c += str(hex(np.random.choice(range(64, 224))))[2:]
                return c

            for nodelist in community.greedy_modularity_communities(graph):
                color = randomcolor()
                for node in nodelist:
                    graph.nodes[node]['cluster'] = i
                    graph.nodes[node]['cluster-color'] = color
                i += 1

            for a, b in graph.edges:
                graph.edges[a, b]['cluster-a'] = graph.nodes[a]['cluster']
                graph.edges[a, b]['cluster-b'] = graph.nodes[b]['cluster']
                graph.edges[a, b]['cluster-color-a'] = graph.nodes[a][
                    'cluster-color']
                graph.edges[a, b]['cluster-color-b'] = graph.nodes[b][
                    'cluster-color']
        return json.dumps(
            nx.readwrite.json_graph.cytoscape_data(graph),
            indent=4,
            separators=(',', ': '))
