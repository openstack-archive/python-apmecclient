#
# Copyright 2013 Intel Corporation
# All Rights Reserved.
#
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

from __future__ import print_function

from oslo_serialization import jsonutils
import yaml

from apmecclient.common import exceptions
from apmecclient.i18n import _
from apmecclient.apmec import v1_0 as apmecV10


_MEAD = "mead"


class ListMEAD(apmecV10.ListCommand):
    """List MEAD that belong to a given tenant."""

    resource = _MEAD
    list_columns = ['id', 'name', 'template_source', 'description']

    def get_parser(self, prog_name):
        parser = super(ListMEAD, self).get_parser(prog_name)
        parser.add_argument(
            '--template-source',
            help=_("List MEAD with specified template source. Available \
                   options are 'onboarded' (default), 'inline' or 'all'"),
            action='store',
            default='onboarded')
        return parser

    def args2search_opts(self, parsed_args):
        search_opts = super(ListMEAD, self).args2search_opts(parsed_args)
        template_source = parsed_args.template_source
        if parsed_args.template_source:
            search_opts.update({'template_source': template_source})
        return search_opts


class ShowMEAD(apmecV10.ShowCommand):
    """Show information of a given MEAD."""

    resource = _MEAD


class CreateMEAD(apmecV10.CreateCommand):
    """Create a MEAD."""

    resource = _MEAD
    remove_output_fields = ["attributes"]

    def add_known_arguments(self, parser):
        parser.add_argument('--mead-file', help=_('Specify MEAD file'))
        parser.add_argument(
            'name', metavar='NAME',
            help=_('Set a name for the MEAD'))
        parser.add_argument(
            '--description',
            help=_('Set a description for the MEAD'))

    def args2body(self, parsed_args):
        body = {self.resource: {}}
        mead = None
        if not parsed_args.mead_file:
            raise exceptions.InvalidInput("Invalid input for mead file")
        with open(parsed_args.mead_file) as f:
            mead = f.read()
            try:
                mead = yaml.load(mead, Loader=yaml.SafeLoader)
            except yaml.YAMLError as e:
                raise exceptions.InvalidInput(e)
            if not mead:
                raise exceptions.InvalidInput("mead file is empty")
            body[self.resource]['attributes'] = {'mead': mead}
        apmecV10.update_dict(parsed_args, body[self.resource],
                              ['tenant_id', 'name', 'description'])
        return body


class DeleteMEAD(apmecV10.DeleteCommand):
    """Delete given MEAD(s)."""
    resource = _MEAD


class ShowTemplateMEAD(apmecV10.ShowCommand):
    """Show template of a given MEAD."""

    resource = _MEAD

    def run(self, parsed_args):
        self.log.debug('run(%s)', parsed_args)
        template = None
        data = self.get_data(parsed_args)
        try:
            attributes_index = data[0].index('attributes')
            attributes_json = data[1][attributes_index]
            template = jsonutils.loads(attributes_json).get('mead', None)
        except (IndexError, TypeError, ValueError) as e:
            self.log.debug('Data handling error: %s', str(e))
        print(template or _('Unable to display MEAD template!'))
