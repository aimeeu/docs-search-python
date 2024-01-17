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

class Properties:
    """
    Populated from data in properties.json
    """

    def __init__(self, sn_api_url, sn_fetch_limit, sn_article_url_base,
                 eas_api_url, eas_api_key, eas_post_limit, eas_engine_list, sn_public_kb_sys_id,
                           sn_customer_kb_sys_id, sn_auth_username, sn_auth_password):
        self.sn_api_url = sn_api_url
        self.sn_fetch_limit = sn_fetch_limit
        self.sn_article_url_base = sn_article_url_base
        self.eas_api_url = eas_api_url
        self.eas_api_key = eas_api_key
        self.eas_post_limit = eas_post_limit
        self.eas_engine_list = eas_engine_list
        self.sn_public_kb_sys_id = sn_public_kb_sys_id
        self.sn_customer_kb_sys_id = sn_customer_kb_sys_id
        self.sn_auth_username = sn_auth_username
        self.sn_auth_password = sn_auth_password

    def __str__(self):
        return "sn_api_url: {}; sn_fetch_limit: {}; sn_article_url_base: {}; eas_api_url: {}; eas_api_key: {}; " \
               "eas_post_limit: {}; eas_engine_list: {}, sn_public_kb_sys_id: {}, sn_customer_kb_sys_id: {}, " \
               "sn_auth_username: {}".format(
                self.sn_api_url, self.sn_fetch_limit, self.sn_article_url_base,
                self.eas_api_url, self.eas_api_key, self.eas_post_limit, self.eas_engine_list,
                self.sn_public_kb_sys_id, self.sn_customer_kb_sys_id, self.sn_auth_username)

