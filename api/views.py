from django.shortcuts import render
from django.http import *
import api.models as models
from django.views.decorators.csrf import csrf_exempt
import json
import os
from api.models import Interactome
import logging
import api.biogrid_version_control as biogrid_version_control
import api.gene_words

logger = logging.getLogger('testlogger')

TYPE = 'application/json; charset=utf8'


@csrf_exempt
def interactions(request):
    '''
    /interactions: Returns graph data formatted for Cytoscape based on queries for specific proteins or for protein networks.

    POST and GET parameters:
        organism_id (int) (required): NCBI Taxonomy ID specifying the organism of interest. E.g. 3702 (Arabidopsis)
        threshold (float) (required): Minimum weight value required to filter OUT a protein. The higher the threshold, the more dense the returned graph.
        order (int) (required): Number specifying the order/depth for the query. For instance, if '3' is specified, the response may contain proteins up to 3 interactions away from the queried protein(s).
        scale (float) (required): Scale from 0 to 1 determining how much experiment types (0) versus strength of mutual interactions (1) influences interaction weight.
        weight_map (dict) (optional): Maps experiment types to weights. Each key/value pair replaces the corresponding default key/value pair.

    POST-exclusive parameters:
        elements (dict) (required): Dict containing protein interactions. Each row of the dict must contain source and target IDs with consistent labels.
        source_label (str) (required) Key value for each source ID identifying the source proteins (e.g. 'Bait Locus')
        target_label (str) (required) Key value for each target ID identifying the target proteins (e.g. 'Prey Locus')
        source_attributes (list) (optional): List of key values for attributes associated with the source protein (e.g. 'Bait Description')
        target_attributes (list) (optional): List of key values fro attributes associated with the target protein (e.g. 'Prey Description')

    GET-exclusive parameters:
        protein_id (str) (required): String representing the ID of the queried protein
    '''

    # For uploading a CSV file and receiving a searched graph
    if request.method == 'POST':
        try:
            elements = json.load(request)['elements']
            organism_id = int(request.GET.__getitem__('organism_id'))
            order = int(request.GET.__getitem__('order'))
            threshold = float(request.GET.__getitem__('threshold'))
            scale = float(request.GET.__getitem__('scale'))
            source_label = str(request.GET.__getitem__('source_label'))
            target_label = str(request.GET.__getitem__('target_label'))
            source_attributes = list(request.GET.get('source_attributes', []))
            target_attributes = list(request.GET.get('target_attributes', []))
            assert scale >= 0 and scale <= 1, "Error: 'scale' must be between 0 and 1"
            assert threshold >= 0 and threshold <= 1, "Error: threshold must be between 0 and 1"
            assert order >= 0, "Error: 'order' must be nonnegative"
        except KeyError as e:
            return HttpResponseBadRequest('Error: missing paremeter "' +
                                          e.args[0] + '"')
        except (ValueError, AssertionError) as e:
            return HttpResponseBadRequest(e)

        interactome = Interactome(
            orgID=organism_id,
            threshold=threshold,
            scale=scale,
            weight_map={},
            input_graph=elements,
            source_label=source_label,
            target_label=target_label,
            data_source="Local",
            source_attributes=source_attributes,
            target_attributes=target_attributes,
            depth=order)
        response = interactome.graph_query(order, formatted=True)
        return HttpResponse(response, content_type=TYPE)

    elif request.method == 'GET':
        try:
            organism_id = str(request.GET.__getitem__("organism_id"))
            protein_id = str(request.GET.__getitem__("protein_id"))
            order = int(request.GET.__getitem__("order"))
            threshold = float(request.GET.__getitem__("threshold"))
            weight_map = dict(request.GET.get('weight_map', {}))
            assert threshold >= 0 and threshold <= 1, "Error: threshold must be between 0 and 1"
            assert order >= 0, "Error: 'order' must be nonnegative"
        except KeyError as e:
            return HttpResponseBadRequest('Error: missing paremeter "' +
                                          e.args[0] + '"')
        except (ValueError, AssertionError) as e:
            return HttpResponseBadRequest(e)
        scale = 1
        interactome = Interactome(organism_id, threshold, scale, protein=protein_id)

        if not interactome.get_biogrid_graph().has_node(protein_id):
            return HttpResponseNotFound('Error: no matching protein with id ' +
                                        protein_id)

        response = interactome.subgraph(protein_id, order, formatted=True)
        return HttpResponse(response, content_type=TYPE)


def gene_words(request):
    if request.method == 'GET':
        logger.info
        id_list = str(request.GET.get("id_list"))
        logger.info(id_list)
        filter_list = (request.GET.getlist("filter_list", []))
        words = api.gene_words.get_keywords(id_list, filter_list, formatted=True)
        return HttpResponse(words, content_type=TYPE)
