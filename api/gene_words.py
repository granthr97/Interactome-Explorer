from gensim.summarization import keywords
from requests import Session
import xml.etree.ElementTree as ElementTree
import json
import logging

logger = logging.getLogger('testlogger')

HEAD = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcg'
URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=gene&id="
KEY = "498d81b898dc8a6c3415744f26c90e365708"

def get_keywords(id_list, filter_list, formatted=False):
    '''
    get_keywords:
        (1) Takes a list of Entrez Gene IDs associated with proteins in Biogrid
            (https://wiki.thebiogrid.org/doku.php/biogrid_tab_version_2.0)
        (2) Queries the NCBI Entrez site at the Gene endpont with that list of IDs
            (https://www.ncbi.nlm.nih.gov/books/NBK25500/#_chapter1_Downloading_Document_Summaries_)
        (3) Retrieves the summaries for each gene by parsing the returned XML
        (4) Uses the gensim NLP library to find keywords in each summary
            (https://radimrehurek.com/gensim/summarization/keywords.html)
        (5) Adds the score for each keyword, accross each summary (i.e. if a keywords appears multiple times,
            add up the score
        (6) And returns a list of those keywords, sorted by their cumulative scores.

        Theoretically, we can use this front-end to quickly figure out similarities between proteins in clusters.

    Arguments:
        (1) id_list (str): Concatenated list of IDs, with each ID separated by a comma ','
        (2) formatted (bool): Indicates whether we want to json-format the result
    '''
    filter_list = [str(filt) for filt in list(filter_list)]    
    session = Session()
    session.head(HEAD)
    response = session.get(url = (URL + id_list))
    words = {}
    root = ElementTree.fromstring(response.text)
    for docsummary in root.find('DocumentSummarySet').findall('DocumentSummary'):
        summary = docsummary.find('Summary').text        
        try: 
            newwords = keywords(str(summary), scores=True, lemmatize=True, deacc=True) 
            for word, score in newwords:
                if word in filter_list:
                    continue
                if not word in words.keys():
                    words[word] = 0
                words[word] += float(score)
        except IndexError:
            continue

    def score(word):
        return 0 - words[word]

    result = sorted(list(words), key=score)
    return json.dumps(result) if formatted else result 
