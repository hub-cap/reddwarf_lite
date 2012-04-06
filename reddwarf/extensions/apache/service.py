# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2011 OpenStack LLC.
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

import logging
import webob.exc

from reddwarf.common import exception
from reddwarf.common import wsgi
# from reddwarf.guestagent.db import models as guest_models
from reddwarf.instance import models as instance_models
from reddwarf.extensions.apache import models
# from reddwarf.extensions.apache import views

LOG = logging.getLogger(__name__)


class BaseController(wsgi.Controller):
    """Base controller class."""

    exclude_attr = []
    exception_map = {
        webob.exc.HTTPUnprocessableEntity: [
            exception.UnprocessableEntity,
            ],
        webob.exc.HTTPBadRequest: [
            exception.BadRequest,
            ],
        webob.exc.HTTPNotFound: [
            exception.NotFound,
            instance_models.ModelNotFoundError,
            ],
        webob.exc.HTTPConflict: [
            ],
        }

    def __init__(self):
        pass

    def _extract_required_params(self, params, model_name):
        params = params or {}
        model_params = params.get(model_name, {})
        return utils.stringify_keys(utils.exclude(model_params,
                                                  *self.exclude_attr))


class SiteController(BaseController):
    """Controller for instance functionality"""

    def index(self, req, tenant_id, instance_id):
        """ Gets a list of sites-enabled/available. """
        LOG.info(_("Getting sites for instance '%s'") % instance_id)
        LOG.info(_("req : '%s'\n\n") % req)
        context = req.environ[wsgi.CONTEXT_KEY]
        sites_list = models.Site.list(context, instance_id)
        return wsgi.Result(sites_list, 200)

    def create(self, req, body, tenant_id, instance_id):
        """ Create a new vhost """
        LOG.info(_("Creating root for instance '%s'") % instance_id)
        LOG.info(_("req : '%s'\n\n") % req)
        context = req.environ[wsgi.CONTEXT_KEY]
        fqdn = body['fqdn']
        root = models.Site.create(context, instance_id, fqdn)
        return wsgi.Result(202)
