from django.test import TestCase
from rest_framework.test import APITestCase
from django.shortcuts import reverse
from api.models import Interactome
from api.helper_models import AdaptiveInteractomeHelper
import api.biogrid_version_control as biogrid_version_control
import copy
import json
import os
import networkx as nx

GET_INTERACTION_REQUIRED_PARAMS = {
    'organism_id': '3702',
    'protein_id': 'AT5G65210',
    'order': 1,
    'scale': 0.5,
    'threshold': 0.5
}

GET_INTERACTION_OPTIONAL_PARAMS = {'weight_map': {}}

GET_INTERACTION = {
    **GET_INTERACTION_REQUIRED_PARAMS,
    **GET_INTERACTION_OPTIONAL_PARAMS
}


class TestInteractomeAPI(APITestCase):
    def test_get_interactions_bad_protein(self):
        modified = copy.deepcopy(GET_INTERACTION_REQUIRED_PARAMS)
        modified['protein_id'] = 'this is definitely not a protein id'
        response = self.client.get(
            reverse("interactions"), modified, format="json")
        self.assertEqual(response.status_code, 404)

    def test_get_interactions_one_depth(self):
        modified = copy.deepcopy(GET_INTERACTION_REQUIRED_PARAMS)
        modified['order'] = 1
        response = self.client.get(
            reverse("interactions"), modified, format="json")
        decoded = json.loads(response.getvalue().decode('utf-8'))
        self.assertGreater(len(list(decoded['elements']['nodes'])), 1)

    def test_get_interactions_zero_depth(self):
        modified = copy.deepcopy(GET_INTERACTION_REQUIRED_PARAMS)
        modified['order'] = 0
        response = self.client.get(
            reverse("interactions"), modified, format="json")
        decoded = json.loads(response.getvalue().decode('utf-8'))
        self.assertEqual(len(list(decoded['elements']['nodes'])), 1)

    def test_get_interactions_bad_params(self):
        for key in GET_INTERACTION_REQUIRED_PARAMS.keys():
            modified = copy.deepcopy(GET_INTERACTION_REQUIRED_PARAMS)
            modified[key] = [
            ]  # Here we simply use any type that can't be casted to a string or float
            response = self.client.get(
                reverse("interactions"), modified, format="json")
            if response.status_code != 400:
                print(key)
                self.assertEqual(response.status_code, 400)
        self.assertTrue(True)

    def test_get_interactions_missing_optional_params(self):
        response = self.client.get(
            reverse("interactions"),
            GET_INTERACTION_REQUIRED_PARAMS,
            format="json")
        self.assertEqual(response.status_code, 200)

    def test_get_interactions_missing_required_params(self):
        for key in GET_INTERACTION_REQUIRED_PARAMS.keys():
            modified = copy.deepcopy(GET_INTERACTION)
            modified.pop(key)
            response = self.client.get(
                reverse("interactions"), modified, format="json")
            if response.status_code != 400:
                self.assertEqual(response.status_code, 400)
        self.assertTrue(True)

    def test_get_interactions_good(self):
        response = self.client.get(
            reverse("interactions"), GET_INTERACTION, format="json")
        self.assertEqual(response.status_code, 200)

    def test_version_control(self):
        current_version = biogrid_version_control.get_current_version()
        local_version = biogrid_version_control.get_latest_local_version()
        if current_version != local_version:
            zip_filename = biogrid_version_control.download_biogrid_tab2_file(
                current_version)
            unziped_filename = biogrid_version_control.unzip_and_save_biogrid_tab2_file(
                zip_filename)
            biogrid_version_control.create_and_save_pickle_file(
                unziped_filename)


class TestAdaptiveInteractomeHelper(APITestCase):
    def test_get_pruned_graph(self):
        edges = [("a", "b"), ("b", "c"), ("c", "a")]
        weights = [0.1, 0.9, 0.9]
        graph = nx.Graph(edges)
        threshold = 0.5

        helper = AdaptiveInteractomeHelper(None, graph, weights, None, None)
        expected_edges = [("a", "b")]
        pruned_graph = helper.get_pruned_graph(threshold)
        actual_edges = list(pruned_graph.edges)

        self.assertListEqual(sorted(expected_edges), sorted(actual_edges))

    def test_get_graph_queried_graph(self):
        edges = [("a", "b"), ("c", "d"), ("c", "e"), ("d", "e"), ("f", "g")]
        source_nodes = ["a", "c"]
        graph = nx.Graph(edges)
        depth = 1

        helper = AdaptiveInteractomeHelper(None, graph, None, source_nodes,
                                           depth)
        expected_edges = [("a", "b"), ("c", "d"), ("c", "e"), ("d", "e")]
        queried_graph = helper.get_graph_queried_graph(graph)
        actual_edges = list(queried_graph.edges)

        self.assertListEqual(sorted(expected_edges), sorted(actual_edges))

    def test_get_min_threshold(self):
        edges = [("a", "b"), ("c", "d"), ("c", "e"), ("d", "e"), ("f", "g")]
        weights = [0.15, 0.15, 0.15, 0.9, 0.15]
        source_nodes = ["a", "c"]
        graph = nx.Graph(edges)
        depth = 1

        helper = AdaptiveInteractomeHelper(None, graph, weights, source_nodes,
                                           depth)
        actual_min_threshold = helper.get_min_threshold()

        self.assertTrue(actual_min_threshold >= 0.15
                        and actual_min_threshold <= 0.2)

    def test_get_max_threshold(self):
        edges = [("a", "b"), ("c", "d"), ("c", "e"), ("d", "e"), ("c", "g"),
                 ("g", "f")]
        weights = [0.4, 0.4, 0.4, 0.4, 0.7, 0.4]
        source_nodes = ["a", "c"]
        graph = nx.Graph(edges)
        depth = 3
        num_edges = 5

        helper = AdaptiveInteractomeHelper(None, graph, weights, source_nodes,
                                           depth, num_edges)
        actual_max_threshold = helper.get_max_threshold()

        self.assertTrue(actual_max_threshold >= 0.6
                        and actual_max_threshold <= 0.7)

    def test_get_adaptive_threshold(self):
        edges = [("a", "b"), ("c", "d"), ("c", "e"), ("d", "e"), ("c", "g"),
                 ("g", "f")]
        weights = [0.15, 0.4, 0.4, 0.4, 0.7, 0.4]
        source_nodes = ["a", "c"]
        graph = nx.Graph(edges)
        depth = 3
        num_edges = 5
        threshold = 0.5

        helper = AdaptiveInteractomeHelper(threshold, graph, weights,
                                           source_nodes, depth, num_edges)
        actual_adaptive_threshold = helper.get_adaptive_threshold()

        self.assertTrue(actual_adaptive_threshold >= 0.4
                        and actual_adaptive_threshold <= 0.5)
