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

from oslo_serialization import jsonutils

import yaml


from apmecclient.apmec import v1_0 as apmecV10
from apmecclient.i18n import _

_MECAD = "mecad"


class ListMECAD(apmecV10.ListCommand):
    """List MECADs that belong to a given tenant."""

    resource = _MECAD
    list_columns = ['id', 'name', 'template_source', 'description']

    def get_parser(self, prog_name):
        parser = super(ListMECAD, self).get_parser(prog_name)
        parser.add_argument(
            '--template-source',
            help=_("List MECAD with specified template source. Available \
                   options are 'onboared' (default), 'inline' or 'all'"),
            action='store',
            default='onboarded')
        return parser

    def args2search_opts(self, parsed_args):
        search_opts = super(ListMECAD, self).args2search_opts(parsed_args)
        template_source = parsed_args.template_source
        if parsed_args.template_source:
            search_opts.update({'template_source': template_source})
        return search_opts


class ShowMECAD(apmecV10.ShowCommand):
    """Show information of a given MECAD."""

    resource = _MECAD


class CreateMECAD(apmecV10.CreateCommand):
    """Create a MECAD."""
    resource = _MECAD
    remove_output_fields = ["attributes"]

    def add_known_arguments(self, parser):
        parser.add_argument('--mecad-file', help='Specify MECAD file',
                            required=True)
        parser.add_argument(
            'name', metavar='NAME',
            help='Set a name for the MECAD')
        parser.add_argument(
            '--description',
            help='Set a description for the MECAD')

    def args2body(self, parsed_args):
        body = {self.resource: {}}
        mecad = None
        with open(parsed_args.mecad_file) as f:
            mecad = yaml.safe_load(f.read())
        apmecV10.update_dict(parsed_args, body[self.resource],
                             ['tenant_id', 'name', 'description'])
        if mecad:
            body[self.resource]['attributes'] = {'mecad': mecad}

        return body


class DeleteMECAD(apmecV10.DeleteCommand):
    """Delete a given MECAD."""
    resource = _MECAD


class ShowTemplateMECAD(apmecV10.ShowCommand):
    """Show template of a given MECAD."""
    resource = _MECAD

    def run(self, parsed_args):
        self.log.debug('run(%s)', parsed_args)
        template = None
        data = self.get_data(parsed_args)
        try:
            attributes_index = data[0].index('attributes')
            attributes_json = data[1][attributes_index]
            template = jsonutils.loads(attributes_json).get('mecad', None)
        except (IndexError, TypeError, ValueError) as e:
            self.log.debug('Data handling error: %s', str(e))
        print(template or _('Unable to display MECAD template!'))
