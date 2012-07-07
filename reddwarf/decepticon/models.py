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

import logging
import datetime


from reddwarf.common import models
from reddwarf.common.exception import InvalidModelError
from reddwarf.common.exception import ModelNotFoundError
from reddwarf import db


LOG = logging.getLogger(__name__)


class UsageModel(models.ModelBase):

    _data_fields = ['id',
                    'instance_name',
                    'tenant_id',
                    'nova_instance_id',
                    'instance_size',
                    'nova_volume_id',
                    'volume_size',
                    'end_time']
    _table_name = 'usage_events'

    def __init__(self, **kwargs):
        self.merge_attributes(kwargs)
        if not self.is_valid():
            raise InvalidModelError(self.errors)

    @classmethod
    def create(cls, **values):
        usage = cls(**values).save()
        return usage

    def save(self):
        self['updated'] = datetime.datetime.utcnow()
        LOG.debug(_("Saving %s: %s") %
            (self.__class__.__name__, self.__dict__))
        return db.db_api.save(self)

    def delete(self):
        LOG.debug(_("Deleting %s: %s") %
            (self.__class__.__name__, self.__dict__))
        return db.db_api.delete(self)

    def merge_attributes(self, values):
        """dict.update() behaviour."""
        for k, v in values.iteritems():
            self[k] = v

    @classmethod
    def find_by(cls, **conditions):
        model = cls.get_by(**conditions)
        if model is None:
            raise ModelNotFoundError(_("%s Not Found") % cls.__name__)
        return model

    @classmethod
    def get_by(cls, **kwargs):
        return db.db_api.find_by(cls, **cls._process_conditions(kwargs))

    @classmethod
    def find_all(cls, **kwargs):
        return db.db_query.find_all(cls, **cls._process_conditions(kwargs))

    @classmethod
    def get_usage_by_time(cls, **kwargs):
        return db.db_query.get_usage_by_time(cls, **cls._process_conditions(kwargs))

    @classmethod
    def _process_conditions(cls, raw_conditions):
        """Override in inheritors to format/modify any conditions."""
        return raw_conditions


def persisted_models():
    return {
        'usage_events': UsageModel,
        }
