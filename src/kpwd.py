#**
#* --------------------------------------------------------------------------
#*                             KEGG Pathway Downloader
#* --------------------------------------------------------------------------
#* University of Tuebingen, 2020.
#*
#* This code is part of the KPWD software package and subject to the terms
#* and conditions defined by its license (MIT License). For license details
#* please refer to the LICENSE file included as part of this source code
#* package.
#*
#* For a full list of authors, please refer to the file AUTHORS.
#*

import sys
import json
import logging
from logging.config import fileConfig
import configparser

from urllib3 import PoolManager
from urllib3 import Timeout
from urllib3 import Retry
from urllib.parse import urlencode

# # Initialize logging system
configFolder = "/config"
fileConfig('/config/logging-config.ini')
logger = logging.getLogger()
logging.getLogger("chardet.charsetprober").disabled = True

pm = PoolManager()
def extract_pw_ids_from_response_data(data:str, orgCode:str) -> list:
    logger.info("Type: {}, content: {}".format(type(data),data))
    result_items = data.split(":")
    list_of_ids = []
    for pw_item in result_items:
        if pw_item.startswith("map"):
            list_of_ids.append("{}{}".format(orgCode, pw_item[3:8]))
        elif pw_item.startswith(orgCode):
            list_of_ids.append(pw_item[0:8])
    return list_of_ids

def get_full_pathway_list(orgCode:str) -> list:
    url = "http://rest.kegg.jp/list/pathway/{}".format(orgCode)
    response = pm.request('GET', url) 
    if response.status > 399:
        raise Exception("Failed to fetch full pathway list for organism '{}'. Error was: {}".format(orgCode, response.status))
    result_text = response.data.decode()
    list_of_ids = extract_pw_ids_from_response_data(result_text, orgCode)
    logger.debug("Found the following pathway ids for organism '{}': {}".format(orgCode, list_of_ids))
    return list_of_ids

def get_pathway_list_for_searchterm(search_term:str, orgCode:str) -> list:
    url = "http://rest.kegg.jp/find/pathway/{}".format(search_term)
    response = pm.request('GET', url)
    if response.status > 399:
        raise Exception("Failed to fetch pathway list for search term '{}'. Error was: {}".format(search_term, response.status))
    result_text = response.data.decode()
    list_of_ids = extract_pw_ids_from_response_data(result_text, orgCode)
    logger.debug("Found the following pathway ids for searchterm '{}': {}".format(search_term, list_of_ids))
    return list_of_ids

def extract_pw_list_from_file(filename:str, orgCode:str) -> list:
    list_of_ids = []
    with open("{}/{}".format(configFolder, filename), "r") as f:
        for l in f.readlines():
            list_of_ids.append(l.strip())
    return list_of_ids

def fetch_pw(pw:str) -> str:
    url = "http://rest.kegg.jp/get/{}/kgml".format(pw)
    response = pm.request('GET', url)
    if response.status > 399:
        raise Exception("Failed to fetch pathway with id '{}'. Error was: {}".format(pw, response.status))
    logger.debug("Finished downloading kgml contents for pathway: '{}'".format(pw))
    return response.data.decode()

def save_pathway(file_prefix, file_content, output_folder) -> None:
    f = open("{}{}.xml".format(output_folder, file_prefix), "w")
    f.write(file_content)
    f.close()
    logger.debug("Saved file {}.xml in folder {}".format(file_prefix, output_folder))

def fetch_kegg_pw_maps(pw_list:list, output_folder:str, orgCode:str) -> int:
    for pw in pw_list:
        if pw[0].isdigit():
            pw = orgCode + pw
        kgml_content = fetch_pw(pw)
        save_pathway(pw, kgml_content, output_folder)
    return 0

if __name__ == "__main__":
    # read config
    config = configparser.ConfigParser()
    config.read('/config/keggdownload-config.ini')
    kegg_api_conf = config['kegg_api']
    action = kegg_api_conf['action']
    
    # organism
    orgCode = kegg_api_conf.get('orgCode', 'map')
    
    if (orgCode.strip() == ''):
        logger.debug("Provided empty orgCode, fetching reference maps")
        orgCode = "map"
    elif (orgCode == "map"):
        logger.debug("No three-letter organism code provided, fetching reference maps")
    else:
        logger.debug("Using orgCode: {}".format(orgCode))
    # download folder
    folder = config['container_env'].get('download_folder', '/data')

    # where to store the files?
    if not folder.startswith('/') and not folder.startswith("./"):
        output_folder = "/{}".format(folder)
    else:
        output_folder = folder
    # do we have a '/' in the end?
    if not output_folder.endswith('/'):
        output_folder = "{}/".format(output_folder)

    logger.debug("Using output folder {}".format(output_folder))

    if action == 'all':
        logger.debug("Beginning download of all KEGG pathway maps")
        pw_list = get_full_pathway_list(orgCode)
        
    elif action == 'search':
        kegg_search_term = sys.argv[1]
        logger.debug("Beginning download of pathways containing searchterm ' {}'".format(kegg_search_term))
        pw_list = get_pathway_list_for_searchterm(kegg_search_term, orgCode)
    elif action == 'list':
        logger.debug("Beginning download of pathways given in config parameter 'map_ids'")
        pw_list = kegg_api_conf.get('map_ids').split(',')
        if pw_list == None or pw_list == '':
            logger.error("No pathway maps configured. Cannot download pathways")
            sys.exit(1)
    elif action == 'file':
        logger.debug("Beginning download of pathways given in the input file '{}'".format(sys.argv[1]))
        pw_list = extract_pw_list_from_file(sys.argv[1], orgCode)
    elif action == 'commandline':
        logger.debug("Beginning download of {} pathway(s) given on the command line".format(len(sys.argv) - 1))
        pw_list = []
        for i in range(1,len(sys.argv)):
            pw_list.append(sys.argv[i])
    else:
        logger.error("No viable action configured. Possible values are ['all', 'search', 'list']. Value found was:'{}'".format(action))
        sys.exit("Cannot perform action '{}'".format(action))

    # Now fetch the pathways in the pathway list
    fetch_kegg_pw_maps(pw_list, output_folder, orgCode)

    sys.exit(0)

