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


from reddwarf.rpc import impl_kombu


# Copied from ceilometer project
class Connection(impl_kombu.Connection):
    """A Kombu connection that does not use the AMQP Proxy class when
    creating a consumer, so we can decode the message ourself."""

    def create_consumer(self, topic, proxy, fanout=False):
        """Create a consumer without using ProxyCallback."""
        if fanout:
            self.declare_fanout_consumer(topic, proxy)
        else:
            self.declare_topic_consumer(topic, proxy)
