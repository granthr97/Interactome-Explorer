import numpy as np
import networkx as nx
import logging
from interruptingcow import timeout

logger = logging.getLogger('testlogger')


class AdaptiveInteractomeHelper():
    def __init__(self, threshold, graph, weights, nodes, depth,
                 num_edges=5000):
        self.threshold = threshold
        self.graph = graph
        self.weights = weights
        self.nodes = nodes
        self.depth = depth
        self.num_edges = num_edges

    def get_pruned_graph(self, threshold):
        edges_to_remove = [(u, v)
                           for (u, v), w in zip(self.graph.edges, self.weights)
                           if w > threshold]
        pruned_graph = self.graph.copy()
        pruned_graph.remove_edges_from(edges_to_remove)
        return pruned_graph

    def get_graph_queried_graph(self, graph):
        output_graph = nx.Graph()
        for node in self.nodes:
            if graph.has_node(node):
                edges = nx.bfs_edges(
                    G=graph,
                    source=node,
                    reverse=False,
                    depth_limit=self.depth)
                output_graph.add_edges_from(edges)
            else:
                output_graph.add_node(node)
        result = graph.subgraph(output_graph.nodes)
        result = nx.compose(output_graph, result)
        return result

    def get_num_nodes_in_pruned_graph(self, threshold):
        pruned_graph = self.get_pruned_graph(threshold)
        graph_queried_graph = self.get_graph_queried_graph(pruned_graph)
        return len(graph_queried_graph.nodes)

    def get_num_edges_in_pruned_graph(self, threshold):
        pruned_graph = self.get_pruned_graph(threshold)
        graph_queried_graph = self.get_graph_queried_graph(pruned_graph)
        return len(graph_queried_graph.edges)

    def get_min_threshold(self, start=0, end=1):
        for threshold in np.linspace(start, end, 20):
            num_edges = self.get_num_edges_in_pruned_graph(threshold)
            #logger.info("min_threshold: {}, num_edges: {}".format(
            #   threshold, num_edges))
            if num_edges > 0:
                return threshold
        raise Exception("No valid min threshold found")

    def get_max_threshold(self, start=1, end=0):
        for threshold in np.linspace(start, end, 20):
            try:
                with timeout(3):
                    num_edges = self.get_num_edges_in_pruned_graph(threshold)
            except:
                continue
            #logger.info("max_threshold: {}, num_edges: {}".format(
            #   threshold, num_edges))
            if num_edges <= self.num_edges:
                return threshold
        raise Exception("No valid max threshold found")

    def get_adaptive_threshold(self):
        min_threshold = self.get_min_threshold()
        max_threshold = self.get_max_threshold()
        adaptive_threshold = self.threshold * (
            max_threshold - min_threshold) + min_threshold
        return adaptive_threshold
