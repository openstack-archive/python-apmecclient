# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from __future__ import print_function

import yaml

from oslo_serialization import jsonutils

from apmecclient.i18n import _
from apmecclient.apmec import v1_0 as apmecV10

_MESD = "mesd"


class ListMESD(apmecV10.ListCommand):
    """List MESDs that belong to a given tenant."""

    resource = _MESD
    list_columns = ['id', 'name', 'template_source', 'description']

    def get_parser(self, prog_name):
        parser = super(ListMESD, self).get_parser(prog_name)
        parser.add_argument(
            '--template-source',
            help=_("List MESD with specified template source. Available \
                   options are 'onboared' (default), 'inline' or 'all'"),
            action='store',
            default='onboarded')
        return parser

    def args2search_opts(self, parsed_args):
        search_opts = super(ListMESD, self).args2search_opts(parsed_args)
        template_source = parsed_args.template_source
        if parsed_args.template_source:
            search_opts.update({'template_source': template_source})
        return search_opts


class ShowMESD(apmecV10.ShowCommand):
    """Show information of a given MESD."""

    resource = _MESD


class CreateMESD(apmecV10.CreateCommand):
    """Create a MESD."""
    resource = _MESD
    remove_output_fields = ["attributes"]

    def add_known_arguments(self, parser):
        parser.add_argument('--mesd-file', help='Specify MESD file',
                            required=True)
        parser.add_argument(
            'name', metavar='NAME',
            help='Set a name for the MESD')
        parser.add_argument(
            '--description',
            help='Set a description for the MESD')

    def args2body(self, parsed_args):
        body = {self.resource: {}}
        mesd = None
        with open(parsed_args.mesd_file) as f:
            mesd = yaml.safe_load(f.read())
        apmecV10.update_dict(parsed_args, body[self.resource],
                              ['tenant_id', 'name', 'description'])
        if mesd:
            body[self.resource]['attributes'] = {'mesd': mesd}

        return body


class DeleteMESD(apmecV10.DeleteCommand):
    """Delete a given MESD."""
    resource = _MESD


class ShowTemplateMESD(apmecV10.ShowCommand):
    """Show template of a given MESD."""
    resource = _MESD

    def run(self, parsed_args):
        self.log.debug('run(%s)', parsed_args)
        template = None
        data = self.get_data(parsed_args)
        try:
            attributes_index = data[0].index('attributes')
            attributes_json = data[1][attributes_index]
            template = jsonutils.loads(attributes_json).get('mesd', None)
        except (IndexError, TypeError, ValueError) as e:
            self.log.debug('Data handling error: %s', str(e))
        print(template or _('Unable to display MESD template!'))
