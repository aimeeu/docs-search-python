#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ===============LICENSE_START================================================
# Armory Apache-2.0
# ============================================================================
# Copyright (C) 2021 Armory. All rights reserved.
# ============================================================================
# This software file is distributed
# under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# This file is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============LICENSE_END==================================================
import os
import sys
import requests
import json
import logging
from logging.handlers import RotatingFileHandler
from logging import StreamHandler
from requests.auth import HTTPBasicAuth
from models import Properties


from elastic_enterprise_search import EnterpriseSearch
from elastic_enterprise_search import AppSearch, UnauthorizedError
from elastic_transport import PayloadTooLargeError

logger = logging.getLogger(__name__)


def main():
    """
    Calls functions to configure logger, read in properties.json, fetch KB articles,
    format KB data, and post to Elastic.
    """
    logger.info("***** job start *****")
    try:
        configure_logger()
        props = read_properties()
        public_articles = fetch_public_kb_articles(props)
        customer_articles = fetch_customer_only_kb_articles(props)
        public_formatted_list = format_kb_data(public_articles, props, locked="false")
        customer_formatted_list = format_kb_data(customer_articles, props, locked="true")

        push_kb_to_elastic(public_formatted_list, props)
        push_kb_to_elastic(customer_formatted_list, props)
        logger.info("***** job finish *****")
    except Exception as e:
        logger.error(e)
        sys.exit(1)
        # email on success or failure


def configure_logger():
    """
    Configure the logger with a RotatingFileHandler and a StreamHandler.
    File name is kb-job.log, maxBytes is 102400 (100KB), backupCount=10
    """
    # eventually move this to the logging-config.ini file
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.setLevel(logging.INFO)
    # create file handler which logs even debug messages
    file_handler = RotatingFileHandler('kb-job.log', maxBytes=102400, backupCount=10)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # write to standard out so it ends up in container logs
    stream_handler = StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)


def read_properties():
    """
    Reads file properties.json into Properties class.
    Exit(0) on error

    :return: props
    """
    try:
        # the App Search API key is stored in a Kubernetes secret
        eas_api_key = os.environ.get("API_PRIVATE_KEY")
        # the Service Now password is stored in a Kubernetes secret
        sn_auth_password = os.environ.get("SERVICENOW_PASSWORD")

        props_file = open('properties.json', "r")
        props_data = json.loads(props_file.read())
        # props is a dict of dicts
        sn_api_url = props_data["serviceNow"]["apiUrl"]
        sn_fetch_limit = int(props_data["serviceNow"]["fetchLimit"])
        sn_article_url_base = props_data["serviceNow"]["articleUrlBase"]
        sn_public_kb_sys_id = props_data["serviceNow"]["publicKbSysId"]
        sn_customer_kb_sys_id = props_data["serviceNow"]["customerKbSysId"]
        sn_auth_username = props_data["serviceNow"]["username"]

        eas_api_url = props_data["elasticAppSearch"]["apiUrl"]
        eas_post_limit = int(props_data["elasticAppSearch"]["postSizeLimit"])
        eas_engine_list = props_data["elasticAppSearch"]["engines"]
        logger.debug("eas_engine_list size: " + str(len(eas_engine_list)))
        props = Properties(sn_api_url, sn_fetch_limit, sn_article_url_base, eas_api_url,
                           eas_api_key, eas_post_limit, eas_engine_list, sn_public_kb_sys_id,
                           sn_customer_kb_sys_id, sn_auth_username, sn_auth_password)
        return props
    except Exception as e:
        logger.error(e)
        # email error using SMTP logger
        raise e
    finally:
        props_file.close()


def fetch_public_kb_articles(props):
    """
    GET list of public articles from ServiceNow API.
    :param props: models.Properties
    :return: article_list
    """
    logger.info("fetch_public_kb_articles")
    try:
        q_params = {"limit": props.sn_fetch_limit,
                    "kb": props.sn_public_kb_sys_id}
        resp = requests.get(props.sn_api_url, params=q_params)
        status_code = resp.status_code
        if status_code != 200:
            logger.error(" ERROR fetch_public_kb_articles: " + status_code)
            raise Exception(" ERROR fetch_public_kb_articles: " + status_code)

        # resp.json() returns a dict with one entry: result
        json_data = resp.json()
        logger.debug("***** resp.json *****")
        logger.debug(json_data)
        # result is a dictionary with two entries: meta (dict) and articles (list)
        result_dict = json_data.get("result")
        logger.debug('***** json_data.get(result) *****')
        logger.debug(result_dict)
        num_records = result_dict.get("meta").get("count")
        logger.info("***** public KB articles fetched: " + str(num_records))
        # articles is a list of dicts
        article_list = result_dict.get("articles")
        logger.info("*****  public_list size" + str(len(article_list)))
        logger.debug(article_list)
        return article_list
    except Exception as e:
        logger.error(e)
        # email error using SMTP logger
        raise e
    return None


def fetch_customer_only_kb_articles(props):
    """
        GET list of customer-only articles from ServiceNow API.
        :param props: models.Properties
        :return: article_list
        """
    logger.info("fetch_customer_only_kb_articles")
    try:
        q_params = {"limit": props.sn_fetch_limit,
                    "kb": props.sn_customer_kb_sys_id}
        resp = requests.get(props.sn_api_url, auth=HTTPBasicAuth(props.sn_auth_username, props.sn_auth_password),
                            params=q_params)
        status_code = resp.status_code
        if status_code != 200:
            logger.error(" ERROR fetch_customer_only_kb_articles: " + status_code)
            raise Exception(" ERROR fetch_customer_only_kb_articles: " + status_code)

        # resp.json() returns a dict with one entry: result
        json_data = resp.json()
        logger.debug("***** resp.json *****")
        logger.debug(json_data)
        # result is a dictionary with two entries: meta (dict) and articles (list)
        result_dict = json_data.get("result")
        logger.debug('***** json_data.get(result) *****')
        logger.debug(result_dict)
        num_records = result_dict.get("meta").get("count")
        logger.info("***** customer KB articles fetched: " + str(num_records))
        # articles is a list of dicts
        article_list = result_dict.get("articles")
        logger.info("*****  customer_list size" + str(len(article_list)))
        logger.debug(article_list)
        return article_list
    except Exception as e:
        logger.error(e)
        # email error using SMTP logger
        raise e
    return None


def format_kb_data(articles_list, props, locked):
    """
    Formats each KB article as a dict with keys that match the Elastic AppSearch engine schema.

    Each formatted KB article dict is added to a temp_list. When the temp_list size equals the App Search max post size
    limit (properties.json), a copy of the temp_list is added to the kb_articles_list. The temp_list is then cleared and
    articles_list iteration continues.

    :param articles_list: List of Knowledge Base articles; each article_list entry is a dict
    :param props: models.Properties
    :param locked "true" or "false"
    :return: kb_articles_list; this is a list of lists; each entry is a list of dicts
    """
    logger.info("format_kb_data locked=" + locked)
    kb_articles_list = []
    try:
        # articles_list is a list of dictionaries
        # JSON keys: id, title, snippet, link, number, fields.kb_knowledge_base.value
        """
        "articles": [
          {
            "link": string,
            "id": string,
            "title": string,
            "snippet": string,
            "score": float,
            "number": string,
            "fields": {
              "kb_knowledge_base": {
                "display_value": "string,
                "name": string,
                "label": string,
                "type": string,
                "value": string
              }
            }
          },
        """
        # KBArticle: id, title, meta_description, url_path, number, locked

        counter = 1
        temp_list = []
        for kb_dict_entry in articles_list:
            url_path = "https://support.armory.io/support" + kb_dict_entry.get("link")
            new_dict = {
                "id": kb_dict_entry.get("id"),
                "title": kb_dict_entry.get("title"),
                "meta_description": kb_dict_entry.get("snippet"),
                "url_path": url_path,
                "number": kb_dict_entry.get("number"),
                "locked": locked,
                "domains": "support.armory.io"
            }
            temp_list.append(new_dict)
            if counter == props.eas_post_limit:
                logger.info(" temp_list size: " + str(len(temp_list)))
                # need to do a shallow copy so the pointers change
                temp_list_copy = temp_list.copy()
                kb_articles_list.append(temp_list_copy)
                temp_list.clear()
                counter = 1
            else:
                counter = counter + 1

        # append contents of final temp_list
        logger.info("***** size of final temp_list: " + str(len(temp_list)))
        final_list = temp_list.copy()
        kb_articles_list.append(final_list)
        temp_list.clear()
        logger.info("kb_articles_list length " + str(len(kb_articles_list)))
    except Exception as e:
        logger.error(e)
        raise e
    return kb_articles_list


def push_kb_to_elastic(formatted_kb_articles_list, props):
    """
    Uses the Elastic App Search Python client to create a connection and post data.

    Articles are posted to each engine defined in properties.json.

    :param formatted_kb_articles_list: each entry is a list of dicts
    :param props: models.Properties
    """
    # formatted_kb_articles_list is a list of dicts
    # Elastic payload max is 100 documents
    # need a list of lists
    logger.info("push_kb_to_elastic")
    app_search_client = None
    try:
        app_search_client = AppSearch(props.eas_api_url, http_auth=props.eas_api_key)
        for engine in props.eas_engine_list:
            logger.info(" posting to engine: " + engine)
            for list_entry in formatted_kb_articles_list:
                # list_entry is a list of dict entries
                logger.info(" list_entry size: " + str(len(list_entry)))
                json_string = json.dumps(list_entry)
                logger.debug(json_string)
                logger.debug("***** app_search_client.index_documents *****")
                resp = app_search_client.index_documents(engine_name=engine,
                                                         documents=json_string)
                if resp.status != 200:
                    logger.error(" Response status != 200 " + resp.status)
                    raise Exception(" Response status != 200 " + resp.status)

                logger.debug(resp)
    except UnauthorizedError as ue:
        logger.error(ue)
        raise ue
    except PayloadTooLargeError as ptle:
        logger.error(ptle)
        raise ptle
    except Exception as e:
        logger.error(e)
        raise e
    finally:
        app_search_client.close()


# Call to main function to run the program
if __name__ == "__main__":
    main()
