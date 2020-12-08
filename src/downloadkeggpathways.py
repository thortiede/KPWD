/**
 * --------------------------------------------------------------------------
 *                             KEGG Pathway Downloader
 * --------------------------------------------------------------------------
 * University of Tuebingen, 2020.
 *
 * This code is part of the SBML4j software package and subject to the terms
 * and conditions defined by its license (MIT License). For license details
 * please refer to the LICENSE file included as part of this source code
 * package.
 *
 * For a full list of authors, please refer to the file AUTHORS.
 */

#!/usr/bin/env python
# coding: utf-8

# # Import everything we need

# In[6]:


import sys
import asyncio
import aiofiles
import aiohttp
from aiohttp import ClientSession
import nest_asyncio
import json
import logging
from logging.config import fileConfig
import configparser
# # Initialize logging system

# In[7]:


fileConfig('/config/logging-config.ini')
logger = logging.getLogger()
logging.getLogger("chardet.charsetprober").disabled = True


# # Functions for querying the KEGG API for the pathways of interest

# ## retrieve a list of pathway ids for a given topic (i.e. cancer)

# In[8]:


async def get_kegg_pw(session:ClientSession, topic:str) -> list:
    list_cancer_pw_url = "http://rest.kegg.jp/find/pathway/{}".format(topic)
    async with session as session:
        async with session.get(list_cancer_pw_url) as resp:
            pw_text = await resp.text() # TODO: might switch to resp.content() here
            pw_text_items = pw_text.split(":")
            list_of_ids = []
            for pw_item in pw_text_items:
                if pw_item.startswith("map"):
                    list_of_ids.append(pw_item[3:8])
            logging.debug("The following ids are found for topic {}:{}".format(topic, list_of_ids))
            return list_of_ids


# ## Build the actual identifier needed to query the KEGG API for a kgml file (i.e. hsa05225)

# In[9]:


async def build_kegg_api_map_ids(session:ClientSession, topic:str, orgCode:str) -> list:
    list_of_map_ids = []
    list_of_ids = await get_kegg_pw(session, topic)
    for pw_id in list_of_ids:
        list_of_map_ids.append("{}{}".format(orgCode, pw_id))
    logging.debug("The map ids to fetch are {}".format(list_of_map_ids))
    return list_of_map_ids


# ## Get a single kegg pathway map in kgml format and store it in the given output folder

# In[10]:


async def get_kegg_map(session:ClientSession, map_id:str, output_folder:str):
    url = "http://rest.kegg.jp/get/{}/kgml".format(map_id)
    resp = await session.request(method="GET", url = url)
    resp.raise_for_status()
    logger.debug("Got response [{}] for getting pathway map {}".format(resp.status, map_id))
    map_text = await resp.text()
    f = open("{}{}.kgml".format(output_folder, map_id), "w")
    f.write(map_text)
    f.close()
    logger.info("Downloaded file %s.kgml", map_id)


# ## Entrypoint method to fetch all KEGG pathways in kgml format for a given organsim and topic

# In[11]:


async def bulk_get_kegg_maps(topic:str, orgCode:str, output_folder:str) -> None:
    # need a ClientSession for KEGG
    session = aiohttp.ClientSession()
    list_of_map_ids = await build_kegg_api_map_ids(session, topic, orgCode)
    # for unknown reason the session closes after this and finding out how to have persistent sessions leads to:
    # https://github.com/aio-libs/aiohttp/issues/3658
    # which is not helpful. So we just create a new session and move on
    if session.closed:
        logger.debug("Creating new Session")
        session = ClientSession()
    async with session as session:
        tasks = []
        for map_id in list_of_map_ids:
            tasks.append(
                get_kegg_map(session, map_id, output_folder)
            )
        await asyncio.gather(*tasks)


# ## Main block to start the download process

# In[13]:

if __name__ == "__main__":
    # read in config
    config = configparser.ConfigParser()
    config.read('/config/keggdownload-config.ini')
    kegg_api_conf = config['kegg_api']
    # topic or map_ids
    if kegg_api_conf['topic'] == None or kegg_api_conf['topic'].strip() == '':
        if kegg_api_conf['map_ids'] == None or kegg_api_conf['map_ids'].strip() == '':
            logger.error("Need to provide either topic or map_ids in [kegg_api] section in keggdownload-config.ini.")
            sys.exit("No topic or map_ids provided")
        else:
            logger.error("Usage of map_ids not implemented, please use topic instead")
            sys.exit("map_ids not implemented yet, use topic instead")
    else:
        topic = kegg_api_conf['topic'].strip()
    logger.debug("Using topic: {}".format(topic))
    # organsim code
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

    # need to fix asyncio nesting of eventloop
    nest_asyncio.apply()

    # get the event loop to hook in new tasks
    loop = asyncio.get_event_loop()



    # where to store the files?
    if not folder.startswith('/') and not folder.startswith("./"):
        output_folder = "/{}".format(folder)
    else:
        output_folder = folder
    # do we have a '/' in the end?
    if not output_folder.endswith('/'):
        output_folder = "{}/".format(output_folder)

    logger.debug("Using output folder {}".format(output_folder))

    # get the cancer pathways
    loop.run_until_complete(bulk_get_kegg_maps(topic, orgCode, output_folder))
