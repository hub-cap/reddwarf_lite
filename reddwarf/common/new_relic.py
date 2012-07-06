#    Copyright 2012 OpenStack LLC
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

import logging
import newrelic.agent

from reddwarf.common import config

LOG = logging.getLogger(__name__)


def wrap(app):
    """
    Wrap the default wsgi app with the newrelic agent wsgi application.

    Newrelic is an instrumentation engine for application monitoring.
    Refer to newrelic.com for more information.
    """
    try:
        newrelic_conf = config.Config.get('newrelic_conf', None)
        newrelic_env = config.Config.get('newrelic_env', None)
        if newrelic_conf:
            newrelic.agent.initialize(newrelic_conf, newrelic_env)
            return newrelic.agent.wsgi_application()(app)
    except Exception as e:
        LOG.error("Error loading newrelic config or agent")
        LOG.error(e)

    # Return the default if there's no newrelic conf or if loading the conf
    # or the agent fails.
    return app
