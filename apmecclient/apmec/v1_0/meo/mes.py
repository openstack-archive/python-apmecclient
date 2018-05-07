# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICEMESE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIOMES OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import yaml

from apmecclient.common import exceptions
from apmecclient.i18n import _
from apmecclient.apmec import v1_0 as apmecV10


_MES = 'mes'
_RESOURCE = 'resource'


class ListMES(apmecV10.ListCommand):
    """List MES that belong to a given tenant."""

    resource = _MES
    list_columns = ['id', 'name', 'mesd_id', 'mgmt_urls', 'status']


class ShowMES(apmecV10.ShowCommand):
    """Show information of a given MES."""

    resource = _MES


class CreateMES(apmecV10.CreateCommand):
    """Create a MES."""

    resource = _MES
    remove_output_fields = ["attributes"]

    def add_known_arguments(self, parser):
        parser.add_argument(
            'name', metavar='NAME',
            help=_('Set a name for the MES'))
        parser.add_argument(
            '--description',
            help=_('Set description for the MES'))
        mesd_group = parser.add_mutually_exclusive_group(required=True)
        mesd_group.add_argument(
            '--mesd-id',
            help=_('MESD ID to use as template to create MES'))
        mesd_group.add_argument(
            '--mesd-template',
            help=_('MESD file to create MES'))
        mesd_group.add_argument(
            '--mesd-name',
            help=_('MESD name to use as template to create MES'))
        vim_group = parser.add_mutually_exclusive_group()
        vim_group.add_argument(
            '--vim-id',
            help=_('VIM ID to use to create MES on the specified VIM'))
        vim_group.add_argument(
            '--vim-name',
            help=_('VIM name to use to create MES on the specified VIM'))
        parser.add_argument(
            '--vim-region-name',
            help=_('VIM Region to use to create MES on the specified VIM'))
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
        if parsed_args.mesd_name:
                _id = apmecV10.find_resourceid_by_name_or_id(apmec_client,
                                                              'mesd',
                                                              parsed_args.
                                                              mesd_name)
                parsed_args.mesd_id = _id
        elif parsed_args.mesd_template:
            with open(parsed_args.mesd_template) as f:
                template = f.read()
            try:
                args['mesd_template'] = yaml.load(
                    template, Loader=yaml.SafeLoader)
            except yaml.YAMLError as e:
                raise exceptions.InvalidInput(e)
            if not args['mesd_template']:
                raise exceptions.InvalidInput('The mesd file is empty')

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
                               'mesd_id', 'vim_id'])
        return body


class DeleteMES(apmecV10.DeleteCommand):
    """Delete given MES(s)."""

    resource = _MES
    deleted_msg = {'mes': 'delete initiated'}
