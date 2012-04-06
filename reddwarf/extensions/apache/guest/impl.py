import logging
import os
import re
import sys
import uuid

from reddwarf.common.exception import ProcessExecutionError
from reddwarf.common import config
from reddwarf.common import utils
from reddwarf.instance import models as rd_models

LOG = logging.getLogger(__name__)


class Apache(object):
    def list_vhosts(self):
        info, err = utils.execute("ls", "/etc/apache2/sites-enabled/",
                                  run_as_root=True)
        enabled = info.split()
        info, err = utils.execute("ls", "/etc/apache2/sites-available/",
                                  run_as_root=True)
        available = info.split()

        return {"enabled": enabled, "available": available}

    def _create_index(self, fqdn):
        # Put a dummy index.html in the /www/fqdn directory
        fqdndir = "/www/%s" % fqdn
        info, err = utils.execute("mkdir", fqdndir,
                                  run_as_root=True, root_helper="sudo")
        if err:
            LOG.error(err)
        tmpfile = "/tmp/index.html"
        indexhtml = """Congrats, Youve landed here %s""" % fqdn
        with open(tmpfile, 'w') as f:
            f.write(indexhtml)
        info, err = utils.execute("mv", tmpfile, fqdndir,
                                  run_as_root=True, root_helper="sudo")

    def create_vhost(self, fqdn):
        self._create_index(fqdn)
        tmpfile = "/tmp/%s" % fqdn
        vhost = ("<VirtualHost *:80>\nDocumentRoot /www/%s"
                "\nServerName %s\n\n</VirtualHost>" % (fqdn, fqdn))
        with open(tmpfile, 'w') as f:
            f.write(vhost)
        info, err = utils.execute("mv", tmpfile,
                                  "/etc/apache2/sites-available/",
                                  run_as_root=True, root_helper="sudo")
        if err:
            LOG.error(err)
        info, err = utils.execute("a2ensite", fqdn,
                                  run_as_root=True, root_helper="sudo")
        if err:
            LOG.error(err)
        info, err = utils.execute("service", "apache2", "reload",
                                 run_as_root=True, root_helper="sudo")
        if err:
            LOG.error(err)

    def prepare(self, databases, memory_mb):
        """Prepare calls update_status to get the job done faster!"""
        self.update_status()

    def update_status(self):
        id = config.Config.get('guest_id')
        status = rd_models.InstanceServiceStatus.find_by(instance_id=id)

        try:
            out, err = utils.execute("/etc/init.d/apache2", "status",
                                     run_as_root=True)
            if "running" in out:
                status.set_status(rd_models.ServiceStatuses.RUNNING)
            else:
                status.set_status(rd_models.ServiceStatuses.SHUTDOWN)
            status.save()
        except ProcessExecutionError as e:
            status.set_status(rd_models.ServiceStatuses.SHUTDOWN)
            status.save()
