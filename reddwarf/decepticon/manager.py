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

import datetime
import json
import logging
import traceback
import uuid


from reddwarf.common import config
from reddwarf.common import service
from reddwarf import decepticon
from reddwarf.decepticon import models
from reddwarf.decepticon import rpc_conn


from kombu import BrokerConnection
from kombu import Exchange
from kombu import Queue
from kombu import Producer
from kombu.mixins import ConsumerMixin
from kombu.utils import kwdict, reprcall


LOG = logging.getLogger(__name__)
CONFIG = config.Config

MAX_TIME = 60*60*24 # 1 day in seconds
CUTOFF = 60*60*23 # 23 hours in seconds

time_format = CONFIG.get('time_format', '%Y-%m-%dT%H:%M:%SZ')
resource_type = CONFIG.get('resource_type', 'MYSQL')
service_code = CONFIG.get('service_code', 'CloudDatabase')
message_version = CONFIG.get('message_version', '1')
region = CONFIG.get('region', 'LOCAL_DEV')
data_center = CONFIG.get('data_center', 'DEV1')
environment =  CONFIG.get('environment', 'LOCAL')

EVENT_MESSAGE = """
<event xmlns="http://docs.rackspace.com/core/event"
       xmlns:dbaas="http://docs.rackspace.com/usage/dbaas"
       version="%(message_version)s"
       id="%(event_id)s"
       type="USAGE"
       rootAction="%(event_action)s"
       tenantId="%(tenantId)s"
       environment="%(environment)s"
       dataCenter="%(data_center)s"
       region="%(region)s"
       resourceId="%(resourceId)s"
       resourceName="%(resourceName)s"
       startTime="%(startTime)s"
       endTime="%(endTime)s">
       <dbaas:product version="%(message_version)s"
                      serviceCode="%(service_code)s"
                      resourceType="%(resource_type)s"
                      memory="%(memory_mb)s"
                      storage="%(volume_size)s"/>
</event>"""

class DecepticonManager(service.Manager):
    """Manages the tasks within a Guest VM."""

    RPC_API_VERSION = "1.0"

    def __init__(self, *args, **kwargs):
        LOG.info("Init DecepticonManager %s %s" % (args, kwargs))
        self.routing_key = CONFIG.get('usage_routing_key', 'reddwarf.events')
        amqp_connection = self._get_connection_string()
        self.connection = BrokerConnection(amqp_connection)
        channel_pool_count = int(CONFIG.get('channel_pool_count', 10))
        self.channel_pool = self.connection.ChannelPool(channel_pool_count)
        super(DecepticonManager, self).__init__(*args, **kwargs)

    def init_host(self):
        """Method for any service initialization"""
        LOG.info("Init host...")

    def _get_connection_string(self):
        rabbit_host = CONFIG.get('rabbit_host', '127.0.0.1')
        rabbit_user = CONFIG.get('rabbit_userid', 'user')
        rabbit_password = CONFIG.get('rabbit_password', 'password')
        amqp_connection = (
            "amqp://%(rabbit_user)s:%(rabbit_password)s@%(rabbit_host)s//"
            % locals())
        return amqp_connection

    def periodic_tasks(self, raise_on_error=False):
        """Method for running any periodic tasks."""
        LOG.info(_("Launching a periodic task"))
        LOG.info("find the instances that are >23 hours old")

        # calculate the usage time (now-23 hours)
        utc_now = datetime.datetime.utcnow()
        utc_usage_time = utc_now - datetime.timedelta(hours=23)
        usage = models.UsageModel.get_usage_by_time(time=utc_usage_time)

        # iterate over the list of usages that were returned
        for instance in usage:
            self._process_end_time(instance, utc_now)

    def get_total_seconds(self, td):
        ms = (td.microseconds + (td.seconds + td.days * 24 * 3600) * 1e6)
        return ms / 1e6

    def _process_end_time(self, instance, utc_now):
        """Splits usage-instance time to multiple "exists" events with
        MAX_TIME spans if needed"""
        end_time = instance['end_time']
        delta = utc_now - end_time
        LOG.info(instance)
        LOG.info("%(delta)s = %(utc_now)s - %(end_time)s" % locals())

        # calculate if time is over the cutoff time period
        if self.get_total_seconds(delta) > CUTOFF:
            LOG.info("instance is over 23 hours old %s"
                     % self.get_total_seconds(delta))

            # is time over 24 hours? if so split it up
            if self.get_total_seconds(delta) > MAX_TIME:
                # time is over 24 hours need to split the time up
                for day in range(delta.days):
                    # add 24 hours to the current end_time
                    et2 = end_time + datetime.timedelta(days=1)
                    # make the message with the id and times
                    body = {
                        "event_type": "reddwarf.instance.exists",
                        "payload": {
                            "event_type": "reddwarf.instance.exists",
                            "instance_id": instance['id'],
                            "start_time": end_time.strftime(time_format),
                            "end_time": et2.strftime(time_format),
                            }
                    }
                    # send the event
                    self._process_event(body)
                    # update the end_time with the new end_time
                    end_time=et2
                    # continue loop
            else:
                # time is not over 24 hours but create an exists now
                body = {
                    "event_type": "reddwarf.instance.exists",
                    "payload": {
                        "event_type": "reddwarf.instance.exists",
                        "instance_id": instance['id'],
                        "start_time": end_time.strftime(time_format),
                        "end_time": utc_now.strftime(time_format),
                        }
                }
                # send the event
                self._process_event(body)

    def _event_action_time_split_up(self, instance_id, strft_end_time):
        """Split up time slices (create exists events) for an event action
        (modify flavor/volume, delete) if needed"""
        usage = models.UsageModel.find_by(id=instance_id)
        LOG.debug("Got usage model: %s", usage)
        LOG.debug("Splitting up time slices for action event.")
        end_time = datetime.datetime.strptime(strft_end_time,
                                              time_format)
        self._process_end_time(usage, end_time)

    def create_event(self, context,
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
                    event_id=None):
        """ this handles when a create event occurs """
        LOG.info(_("test_method called with context %s") % context)
        body = {
            "event_type": event_type,
            "payload": {
                "volume_size": volume_size,
                "memory_mb": instance_size,
                "tenant_id": tenant_id,
                "instance_id": instance_id,
                "instance_name": instance_name,
                "launched_at": launched_at,
                "created_at": created_at,
                "nova_instance_id": nova_instance_id,
                "nova_volume_id": nova_volume_id,
                "event_id": event_id
                }
        }
        self._process_event(body)

    def modify_event(self, context,
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
                    modify_at,
                    event_id=None):
        """ this handles when a modify event occurs """
        LOG.info(_("test_method called with context %s") % context)
        body = {
            "event_type": event_type,
            "payload": {
                "event_type": event_type,
                "volume_size": volume_size,
                "memory_mb": instance_size,
                "tenant_id": tenant_id,
                "instance_id": instance_id,
                "instance_name": instance_name,
                "launched_at": launched_at,
                "created_at": created_at,
                "nova_instance_id": nova_instance_id,
                "nova_volume_id": nova_volume_id,
                "modify_at": modify_at,
                "event_id": event_id
                }
        }
        self._process_event(body)

    def delete_event(self, context,
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
                    deleted_at,
                    event_id=None):
        """ this handles when a delete event occurs """
        LOG.info(_("test_method called with context %s") % context)
        body = {
            "event_type": event_type,
            "payload": {
                "event_type": event_type,
                "volume_size": volume_size,
                "memory_mb": instance_size,
                "tenant_id": tenant_id,
                "instance_id": instance_id,
                "instance_name": instance_name,
                "launched_at": launched_at,
                "created_at": created_at,
                "nova_instance_id": nova_instance_id,
                "nova_volume_id": nova_volume_id,
                "deleted_at": deleted_at,
                "event_id": event_id
                }
        }
        self._process_event(body)

    def _process_event(self, body):
        LOG.debug("processing task....")
        try:
            event_type = body['event_type']
            LOG.debug("Got event_type: %s", event_type)
            payload =  body['payload']
            LOG.debug("Got payload: %s", payload)
            event_mapper = {
                'reddwarf.instance.create': self._handle_create,
                'reddwarf.instance.exists': self._handle_exists,
                'reddwarf.instance.modify_flavor': self._handle_modify,
                'reddwarf.instance.modify_volume': self._handle_modify,
                'reddwarf.instance.delete': self._handle_delete,
            }
            handle = event_mapper[event_type]
            handle(payload)
        except Exception as e:
            import traceback
            print traceback.format_exc()

    def _handle_create(self, payload):
        usage = models.UsageModel.create(id=payload['instance_id'],
                          nova_instance_id=payload['nova_instance_id'],
                          instance_size=payload['memory_mb'],
                          instance_name=payload['instance_name'],
                          nova_volume_id=payload['nova_volume_id'],
                          volume_size=payload['volume_size'],
                          end_time=payload['launched_at'],
                          tenant_id=payload['tenant_id'])
        usage.save()

    def _handle_exists(self, payload):
        usage = models.UsageModel.find_by(id=payload['instance_id'])
        LOG.debug("Got usage model: %s", usage)

        resourceId = usage['id']
        memory_mb = usage['instance_size']
        volume_size = usage['volume_size']
        tenantId = usage['tenant_id']
        resourceName = usage['instance_name']

        event_action = payload['event_type']
        startTime = payload['start_time']
        endTime = payload['end_time']
        usage.end_time = endTime
        usage.save()

        #create the usage event for modify instance
        if 'event_id' in payload:
            event_id = payload['event_id']
        else:
            event_id = str(uuid.uuid4())
        event_variables = {
            'message_version': message_version,
            'event_id': event_id,
            'event_action': event_action,
            'tenantId': tenantId,
            'environment': environment,
            'data_center': data_center,
            'region': region,
            'resourceId': resourceId,
            'resourceName': resourceName,
            'startTime': startTime,
            'endTime': endTime,
            'service_code': service_code,
            'resource_type': resource_type,
            'memory_mb': memory_mb,
            'volume_size': volume_size
        }
        self._send_usage_event(EVENT_MESSAGE % event_variables)

    def _handle_modify(self, payload):
        self._event_action_time_split_up(payload['instance_id'],
                                         payload['modify_at'])

        usage = models.UsageModel.find_by(id=payload['instance_id'])
        LOG.debug("Got post-split-up usage model: %s", usage)
        resourceId = usage['id']
        startTime = usage['end_time'].strftime(time_format)
        old_memory_mb = usage['instance_size']
        old_volume_size = usage['volume_size']

        event_action = payload['event_type']
        volume_size = payload['volume_size']
        memory_mb = payload['memory_mb']
        tenantId = payload['tenant_id']
        resourceName = payload['instance_name']
        endTime = payload['modify_at']


        usage.volume_size = volume_size
        usage.instance_size = memory_mb
        usage.end_time = endTime
        usage.save()

        #create the usage event for modify instance
        event_id = str(uuid.uuid4())
        memory_mb = old_memory_mb
        volume_size = old_volume_size

        event_variables = {
            'message_version': message_version,
            'event_id': event_id,
            'event_action': event_action,
            'tenantId': tenantId,
            'environment': environment,
            'data_center': data_center,
            'region': region,
            'resourceId': resourceId,
            'resourceName': resourceName,
            'startTime': startTime,
            'endTime': endTime,
            'service_code': service_code,
            'resource_type': resource_type,
            'memory_mb': memory_mb,
            'volume_size': volume_size
        }
        self._send_usage_event(EVENT_MESSAGE % event_variables)

    def _handle_delete(self, payload):
        self._event_action_time_split_up(payload['instance_id'],
                                         payload['deleted_at'])

        usage = models.UsageModel.find_by(id=payload['instance_id'])
        LOG.debug("Got post-split-up usage model: %s", usage)
        resourceId = usage['id']
        startTime = usage['end_time'].strftime(time_format)
        memory_mb = usage['instance_size']
        volume_size = usage['volume_size']

        event_action = payload['event_type']
        tenantId = payload['tenant_id']
        resourceName = payload['instance_name']
        endTime = payload['deleted_at']

        #create the usage event for modify instance
        event_id = str(uuid.uuid4())

        event_variables = {
            'message_version': message_version,
            'event_id': event_id,
            'event_action': event_action,
            'tenantId': tenantId,
            'environment': environment,
            'data_center': data_center,
            'region': region,
            'resourceId': resourceId,
            'resourceName': resourceName,
            'startTime': startTime,
            'endTime': endTime,
            'service_code': service_code,
            'resource_type': resource_type,
            'memory_mb': memory_mb,
            'volume_size': volume_size
        }
        self._send_usage_event(EVENT_MESSAGE % event_variables)
        usage.delete()

    def _send_usage_event(self, message):
        channel = None
        try:
            LOG.debug("attempting to send message ====== %s" % message)
            channel = self.channel_pool.acquire()
            LOG.debug("create channel [%r]" % channel)
            nova_exchange = Exchange("nova", type="topic", durable=False)
            LOG.debug("create exchange [%r]" % nova_exchange)

            p = Producer(channel, nova_exchange, serializer="json")
            LOG.debug("create producer [%r]" % p)
            p.publish(message, routing_key=self.routing_key)
            LOG.debug("published to (%s) done, releaseing channel" %
                        self.routing_key)
        except Exception as e:
            LOG.exception(e)
            raise e
        finally:
            if channel:
                channel.release()


    def _convert_datetime_to_string(self, time):
        ret_time = datetime.datetime.strptime(time, time_format)
        return ret_time.strftime(time_format)
