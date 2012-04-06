# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2010-2011 OpenStack LLC.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http: //www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""Model classes that form the core of instances functionality."""

import logging

from reddwarf import db

from reddwarf.common import config
from reddwarf.common import exception
from reddwarf.instance import models as base_models
from reddwarf.extensions.apache.guest import api
# from reddwarf.guestagent.db import models as guest_models
# from reddwarf.common.remote import create_guest_client

CONFIG = config.Config
LOG = logging.getLogger(__name__)


def load_and_verify(context, instance_id):
    # Load InstanceServiceStatus to verify if its running
    instance = base_models.Instance.load(context, instance_id)
    if not instance.is_sql_running:
        raise exception.UnprocessableEntity(
                    "Instance %s is not ready." % instance.id)
    else:
        return instance


class Site(object):

    _data_fields = ['name']

    def __init__(self, name):
        self.name = name

    @classmethod
    def list(self, context, instance_id):
        load_and_verify(context, instance_id)
        enabled_vhosts = api.API(context, 
                                 instance_id).list_vhosts(instance_id)
        return enabled_vhosts

    @classmethod
    def create(self, context, instance_id, fqdn):
        load_and_verify(context, instance_id)
        api.API(context, instance_id).create_vhost(fqdn)
