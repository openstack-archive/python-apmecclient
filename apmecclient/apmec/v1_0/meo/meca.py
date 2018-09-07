# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITION OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import yaml

from apmecclient.common import exceptions
from apmecclient.i18n import _
from apmecclient.apmec import v1_0 as apmecV10


_MECA = 'meca'
_RESOURCE = 'resource'


class ListMECA(apmecV10.ListCommand):
    """List MECA that belong to a given tenant."""

    resource = _MECA
    list_columns = ['id', 'name', 'mecad_id', 'mgmt_urls', 'status']


class ShowMECA(apmecV10.ShowCommand):
    """Show information of a given MECA."""

    resource = _MECA


class CreateMECA(apmecV10.CreateCommand):
    """Create a MECA."""

    resource = _MECA
    remove_output_fields = ["attributes"]

    def add_known_arguments(self, parser):
        parser.add_argument(
            'name', metavar='NAME',
            help=_('Set a name for the MECA'))
        parser.add_argument(
            '--description',
            help=_('Set description for the MECA'))
        mecad_group = parser.add_mutually_exclusive_group(required=True)
        mecad_group.add_argument(
            '--mecad-id',
            help=_('MECAD ID to use as template to create MECA'))
        mecad_group.add_argument(
            '--mecad-template',
            help=_('MECAD file to create MECA'))
        mecad_group.add_argument(
            '--mecad-name',
            help=_('MECAD name to use as template to create MECA'))
        vim_group = parser.add_mutually_exclusive_group()
        vim_group.add_argument(
            '--vim-id',
            help=_('VIM ID to use to create MECA on the specified VIM'))
        vim_group.add_argument(
            '--vim-name',
            help=_('VIM name to use to create MECA on the specified VIM'))
        parser.add_argument(
            '--vim-region-name',
            help=_('VIM Region to use to create MECA on the specified VIM'))
        parser.add_argument(
            '--param-file',
            help=_('Specify parameter yaml file'))

    def args2body(self, parsed_args):
        args = {'attributes': {}}
        body = {self.resource: args}
        if parsed_args.vim_region_name:
            args.setdefault('placement_attr', {})['region_name'] = \
                parsed_args.vim_region_name

        apmec_client = self.get_client()
        apmec_client.format = parsed_args.request_format
        if parsed_args.vim_name:
                _id = apmecV10.find_resourceid_by_name_or_id(apmec_client,
                                                              'vim',
                                                              parsed_args.
                                                              vim_name)
                parsed_args.vim_id = _id
        if parsed_args.mecad_name:
                _id = apmecV10.find_resourceid_by_name_or_id(apmec_client,
                                                              'mecad',
                                                              parsed_args.
                                                              mecad_name)
                parsed_args.mecad_id = _id
        elif parsed_args.mecad_template:
            with open(parsed_args.mecad_template) as f:
                template = f.read()
            try:
                args['mecad_template'] = yaml.load(
                    template, Loader=yaml.SafeLoader)
            except yaml.YAMLError as e:
                raise exceptions.InvalidInput(e)
            if not args['mecad_template']:
                raise exceptions.InvalidInput('The mecad file is empty')

        if parsed_args.param_file:
            with open(parsed_args.param_file) as f:
                param_yaml = f.read()
            try:
                args['attributes']['param_values'] = yaml.load(
                    param_yaml, Loader=yaml.SafeLoader)
            except yaml.YAMLError as e:
                raise exceptions.InvalidInput(e)
        apmecV10.update_dict(parsed_args, body[self.resource],
                              ['tenant_id', 'name', 'description',
                               'mecad_id', 'vim_id'])
        return body


class DeleteMECA(apmecV10.DeleteCommand):
    """Delete given MECA(s)."""

    resource = _MECA
    deleted_msg = {'meca': 'delete initiated'}


class UpdateMECA(apmecV10.UpdateCommand):
    """Update a given MES."""

    resource = _MECA

    def add_known_arguments(self, parser):
        parser.add_argument(
            '--mecad-template',
            help=_('MECAD file to update MECA')
        )

    def args2body(self, parsed_args):
        args = {}
        body = {self.resource: args}

        apmec_client = self.get_client()
        apmec_client.format = parsed_args.request_format

        if parsed_args.mecad_template:
            with open(parsed_args.mecad_template) as f:
                template = f.read()
            try:
                args['mecad_template'] = yaml.load(
                    template, Loader=yaml.SafeLoader)
            except yaml.YAMLError as e:
                raise exceptions.InvalidInput(e)
            if not args['mecad_template']:
                raise exceptions.InvalidInput('The mecad template is empty')

        apmecV10.update_dict(parsed_args, body[self.resource],
                              ['tenant_id'])
        return body

