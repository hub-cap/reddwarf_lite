# Copyright 2012 OpenStack LLC.
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
Routes all the requests to the decepticon manager.
"""


import logging
import traceback
import sys

from reddwarf.common import config
from reddwarf.common.manager import ManagerAPI


CONFIG = config.Config
LOG = logging.getLogger(__name__)


class API(ManagerAPI):
    """API for interacting with the decepticon manager."""

    def _fake_cast(self, method_name, **kwargs):
        import eventlet
        from reddwarf.decepticon.manager import DecepticonManager
        usage = DecepticonManager()
        method = getattr(usage, method_name)

        def func():
            try:
                method(self.context, **kwargs)
            except Exception as ex:
                type_, value, tb = sys.exc_info()
                LOG.error("Error running async task:")
                LOG.error((traceback.format_exception(type_, value, tb)))
                raise type_, value, tb
        eventlet.spawn_after(0, func)

    def _get_routing_key(self):
        """Create the routing key for the taskmanager"""
        return CONFIG.get('decepticon_queue', 'decepticon')

    def create_event(self,
                     event_type,
                     volume_size,
                     instance_size,
                     tenant_id,
                     instance_id,
                     instance_name,
                     launched_at,
                     created_at,
                     nova_instance_id,
                     nova_volume_id):
        LOG.debug("Making async call to create usage event for instance: %s"
                  % instance_id)
        #TODO(cp16net): can we pass through kwargs here?
        self._cast("create_event",
                   event_type=event_type,
                   volume_size=volume_size,
                   instance_size=instance_size,
                   tenant_id=tenant_id,
                   instance_id=instance_id,
                   instance_name=instance_name,
                   launched_at=launched_at,
                   created_at=created_at,
                   nova_instance_id=nova_instance_id,
                   nova_volume_id=nova_volume_id)

    def modify_event(self,
                     event_type,
                     volume_size,
                     instance_size,
                     tenant_id,
                     instance_id,
                     instance_name,
                     launched_at,
                     created_at,
                     nova_instance_id,
                     nova_volume_id,
                     modify_at):
        LOG.debug("Making async call for (%s) usage event for instance: (%s)"
                  % (event_type, instance_id))
        #TODO(cp16net): can we pass through kwargs here?
        self._cast("modify_event",
                   event_type=event_type,
                   volume_size=volume_size,
                   instance_size=instance_size,
                   tenant_id=tenant_id,
                   instance_id=instance_id,
                   instance_name=instance_name,
                   launched_at=launched_at,
                   created_at=created_at,
                   nova_instance_id=nova_instance_id,
                   nova_volume_id=nova_volume_id,
                   modify_at=modify_at)

    def delete_event(self,
                     event_type,
                     volume_size,
                     instance_size,
                     tenant_id,
                     instance_id,
                     instance_name,
                     launched_at,
                     created_at,
                     nova_instance_id,
                     nova_volume_id,
                     deleted_at):
        LOG.debug("Making async call for (%s) usage event for instance: (%s)"
                  % (event_type, instance_id))
        #TODO(cp16net): can we pass through kwargs here?
        self._cast("delete_event",
                   event_type=event_type,
                   volume_size=volume_size,
                   instance_size=instance_size,
                   tenant_id=tenant_id,
                   instance_id=instance_id,
                   instance_name=instance_name,
                   launched_at=launched_at,
                   created_at=created_at,
                   nova_instance_id=nova_instance_id,
                   nova_volume_id=nova_volume_id,
                   deleted_at=deleted_at)
