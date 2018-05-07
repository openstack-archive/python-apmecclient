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

import yaml

from apmecclient.common import exceptions
from apmecclient.i18n import _
from apmecclient.apmec import v1_0 as apmecV10


_MEA = 'mea'
_RESOURCE = 'resource'


class ListMEA(apmecV10.ListCommand):
    """List MEA that belong to a given tenant."""

    resource = _MEA
    list_columns = ['id', 'name', 'mgmt_url', 'status',
                    'vim_id', 'mead_id']


class ShowMEA(apmecV10.ShowCommand):
    """Show information of a given MEA."""

    resource = _MEA


class CreateMEA(apmecV10.CreateCommand):
    """Create a MEA."""

    resource = _MEA
    remove_output_fields = ["attributes"]

    def add_known_arguments(self, parser):
        parser.add_argument(
            'name', metavar='NAME',
            help=_('Set a name for the MEA'))
        parser.add_argument(
            '--description',
            help=_('Set description for the MEA'))
        mead_group = parser.add_mutually_exclusive_group(required=True)
        mead_group.add_argument(
            '--mead-id',
            help=_('MEAD ID to use as template to create MEA'))
        mead_group.add_argument(
            '--mead-name',
            help=_('MEAD Name to use as template to create MEA'))
        mead_group.add_argument(
            '--mead-template',
            help=_("MEAD file to create MEA"))
        vim_group = parser.add_mutually_exclusive_group()
        vim_group.add_argument(
            '--vim-id',
            help=_('VIM ID to use to create MEA on the specified VIM'))
        vim_group.add_argument(
            '--vim-name',
            help=_('VIM name to use to create MEA on the specified VIM'))
        parser.add_argument(
            '--vim-region-name',
            help=_('VIM Region to use to create MEA on the specified VIM'))
        parser.add_argument(
            '--config-file',
            help=_('YAML file with MEA configuration'))
        parser.add_argument(
            '--param-file',
            help=_('Specify parameter yaml file'))

    def args2body(self, parsed_args):
        args = {'attributes': {}}
        body = {self.resource: args}
        # config arg passed as data overrides config yaml when both args passed
        config = None
        if parsed_args.config_file:
            with open(parsed_args.config_file) as f:
                config_yaml = f.read()
            try:
                config = yaml.load(
                    config_yaml, Loader=yaml.SafeLoader)
            except yaml.YAMLError as e:
                raise exceptions.InvalidInput(e)

        if config:
            args['attributes']['config'] = config
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
        if parsed_args.mead_name:
                _id = apmecV10.find_resourceid_by_name_or_id(apmec_client,
                                                              'mead',
                                                              parsed_args.
                                                              mead_name)
                parsed_args.mead_id = _id
        elif parsed_args.mead_template:
            with open(parsed_args.mead_template) as f:
                template = f.read()
            try:
                args['mead_template'] = yaml.load(
                    template, Loader=yaml.SafeLoader)
            except yaml.YAMLError as e:
                raise exceptions.InvalidInput(e)

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
                               'mead_id', 'vim_id'])
        return body


class UpdateMEA(apmecV10.UpdateCommand):
    """Update a given MEA."""

    resource = _MEA

    def add_known_arguments(self, parser):
        parser.add_argument(
            '--config-file',
            help=_('YAML file with MEA configuration'))
        parser.add_argument(
            '--config',
            help=_('Specify config yaml data'))

    def args2body(self, parsed_args):
        body = {self.resource: {}}
        # config arg passed as data overrides config yaml when both args passed
        config = None
        if parsed_args.config_file:
            with open(parsed_args.config_file) as f:
                config_yaml = f.read()
            try:
                config = yaml.load(config_yaml, Loader=yaml.SafeLoader)
            except yaml.YAMLError as e:
                raise exceptions.InvalidInput(e)
        if parsed_args.config:
            config = parsed_args.config
            if isinstance(config, str) or isinstance(config, unicode):
                config_str = parsed_args.config.decode('unicode_escape')
                try:
                    config = yaml.load(config_str, Loader=yaml.SafeLoader)
                except yaml.YAMLError as e:
                    raise exceptions.InvalidInput(e)
        if config:
            body[self.resource]['attributes'] = {'config': config}
        apmecV10.update_dict(parsed_args, body[self.resource], ['tenant_id'])
        return body


class DeleteMEA(apmecV10.DeleteCommand):
    """Delete given MEA(s)."""

    resource = _MEA
    deleted_msg = {'mea': 'delete initiated'}


class ListMEAResources(apmecV10.ListCommand):
    """List resources of a MEA like VDU, CP, etc."""

    list_columns = ['name', 'id', 'type']
    allow_names = True
    resource = _MEA

    def get_id(self):
        if self.resource:
            return self.resource.upper()

    def get_parser(self, prog_name):
        parser = super(ListMEAResources, self).get_parser(prog_name)
        if self.allow_names:
            help_str = _('ID or name of %s to look up')
        else:
            help_str = _('ID of %s to look up')
        parser.add_argument(
            'id', metavar=self.get_id(),
            help=help_str % self.resource)
        return parser

    def get_data(self, parsed_args):
        self.log.debug('get_data(%s)', parsed_args)
        apmec_client = self.get_client()
        apmec_client.format = parsed_args.request_format
        if self.allow_names:
            _id = apmecV10.find_resourceid_by_name_or_id(apmec_client,
                                                          self.resource,
                                                          parsed_args.id)
        else:
            _id = parsed_args.id

        data = self.retrieve_list_by_id(_id, parsed_args)
        self.extend_list(data, parsed_args)
        return self.setup_columns(data, parsed_args)

    def retrieve_list_by_id(self, id, parsed_args):
        """Retrieve a list of sub resources from Apmec server"""
        apmec_client = self.get_client()
        apmec_client.format = parsed_args.request_format
        _extra_values = apmecV10.parse_args_to_dict(self.values_specs)
        apmecV10._merge_args(self, parsed_args, _extra_values,
                              self.values_specs)
        search_opts = self.args2search_opts(parsed_args)
        search_opts.update(_extra_values)
        if self.pagination_support:
            page_size = parsed_args.page_size
            if page_size:
                search_opts.update({'limit': page_size})
        if self.sorting_support:
            keys = parsed_args.sort_key
            if keys:
                search_opts.update({'sort_key': keys})
            dirs = parsed_args.sort_dir
            len_diff = len(keys) - len(dirs)
            if len_diff > 0:
                dirs += ['asc'] * len_diff
            elif len_diff < 0:
                dirs = dirs[:len(keys)]
            if dirs:
                search_opts.update({'sort_dir': dirs})
        obj_lister = getattr(apmec_client, "list_mea_resources")
        data = obj_lister(id, **search_opts)
        return data.get('resources', [])


class ScaleMEA(apmecV10.ApmecCommand):
    """Scale a MEA."""

    api = 'mec-orchestration'
    resource = None
    log = None

    def get_parser(self, prog_name):
        parser = super(ScaleMEA, self).get_parser(prog_name)
        self.add_known_arguments(parser)
        return parser

    def run(self, parsed_args):
        apmec_client = self.get_client()
        apmec_client.format = parsed_args.request_format
        body = self.args2body(parsed_args)
        obj_creator = getattr(apmec_client,
                              "scale_mea")
        obj_creator(body["scale"].pop('mea_id'), body)

    def add_known_arguments(self, parser):
        mea_group = parser.add_mutually_exclusive_group(required=True)
        mea_group.add_argument(
            '--mea-id',
            help=_('MEA ID'))
        mea_group.add_argument(
            '--mea-name',
            help=_('MEA name'))
        parser.add_argument(
            '--scaling-policy-name',
            help=_('MEA policy name used to scale'))
        parser.add_argument(
            '--scaling-type',
            help=_('MEA scaling type, it could be either "out" or "in"'))

    def args2body(self, parsed_args):
        args = {}
        body = {"scale": args}

        if parsed_args.mea_name:
            apmec_client = self.get_client()
            apmec_client.format = parsed_args.request_format
            _id = apmecV10.find_resourceid_by_name_or_id(apmec_client,
                                                          'mea',
                                                          parsed_args.
                                                          mea_name)
            parsed_args.mea_id = _id

        args['mea_id'] = parsed_args.mea_id
        args['type'] = parsed_args.scaling_type
        args['policy'] = parsed_args.scaling_policy_name

        return body
