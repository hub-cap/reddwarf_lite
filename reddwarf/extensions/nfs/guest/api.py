# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2011 OpenStack, LLC.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""
Handles all request to the Platform or Guest VM
"""


import logging

from reddwarf import rpc
from reddwarf.common import config
from reddwarf.common import exception
from reddwarf.common import utils


LOG = logging.getLogger(__name__)


class API(object):
    """API for interacting with the guest manager."""

    def __init__(self, context, id):
        self.context = context
        self.id = id

    def _get_routing_key(self):
        """Create the routing key based on the container id"""
        return "guestagent.%s" % self.id

    def list_exports(self):
        """Make an asynchronous call to get the list of vhosts"""
        LOG.debug(_("Listing exports for Instance %s"), self.id)
        return rpc.call(self.context, self._get_routing_key(),
                 {"method": "list_exports"})

    def create_export(self, export_ip):
        """Make an asynchronous call to create a new vhost"""
        LOG.debug(_("Creating export for Instance %s"), self.id)
        rpc.cast(self.context, self._get_routing_key(),
                 {"method": "create_export",
                  "args": {"export_ip": export_ip}
                 })
