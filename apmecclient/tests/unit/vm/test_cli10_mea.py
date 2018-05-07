# Copyright 2014 Intel Corporation
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
import sys

import mock

from apmecclient import shell
from apmecclient.apmec import v1_0 as apmecV1_0
from apmecclient.apmec.v1_0 import ApmecCommand
from apmecclient.apmec.v1_0.mem import mea
from apmecclient.tests.unit import test_cli10
from apmecclient.tests.unit import test_utils

API_VERSION = "1.0"
FORMAT = 'json'
TOKEN = 'testtoken'
ENDURL = 'localurl'


class CLITestV10VmMEAJSON(test_cli10.CLITestV10Base):
    _RESOURCE = 'mea'
    _RESOURCES = 'meas'
    _MEA_RESOURCES = 'mea_resources'

    def setUp(self):
        plurals = {'meas': 'mea',
                   'resources': 'resource'}
        super(CLITestV10VmMEAJSON, self).setUp(plurals=plurals)

    @mock.patch.object(ApmecCommand, 'get_client')
    def _test_create_resource(self, resource, cmd, name, myid, args,
                              position_names, position_values, mock_get,
                              tenant_id=None, tags=None, admin_state_up=True,
                              extra_body=None, **kwargs):
        mock_get.return_value = self.client
        non_admin_status_resources = ['mead', 'mea']
        if (resource in non_admin_status_resources):
            body = {resource: {}, }
        else:
            body = {resource: {'admin_state_up': admin_state_up, }, }
        if tenant_id:
            body[resource].update({'tenant_id': tenant_id})
        if tags:
            body[resource].update({'tags': tags})
        if extra_body:
            body[resource].update(extra_body)
        body[resource].update(kwargs)

        for i in range(len(position_names)):
            body[resource].update({position_names[i]: position_values[i]})
        ress = {resource:
                {self.id_field: myid}, }
        if name:
            ress[resource].update({'name': name})
        self.client.format = self.format
        resstr = self.client.serialize(ress)
        # url method body
        resource_plural = apmecV1_0._get_resource_plural(resource,
                                                          self.client)
        path = getattr(self.client, resource_plural + "_path")
        # Work around for LP #1217791. XML deserializer called from
        # MyComparator does not decodes XML string correctly.
        if self.format == 'json':
            _body = test_cli10.MyComparator(body, self.client)
        else:
            _body = self.client.serialize(body)
        with mock.patch.object(self.client.httpclient, 'request') as mock_req:
            mock_req.return_value = (test_cli10.MyResp(200), resstr)
            args.extend(['--request-format', self.format])
            args.extend(['--mead-id', 'mead'])
            cmd_parser = cmd.get_parser('create_' + resource)
            shell.run_command(cmd, cmd_parser, args)
            mock_req.assert_called_once_with(
                test_cli10.end_url(path, format=self.format), 'POST',
                body=_body,
                headers=test_utils.ContainsKeyValue('X-Auth-Token', TOKEN))
        mock_get.assert_any_call()

    def test_create_mea_all_params(self):
        cmd = mea.CreateMEA(test_cli10.MyApp(sys.stdout), None)
        name = 'my_name'
        my_id = 'my-id'
        mead_id = 'mead'
        vim_id = 'vim_id'
        description = 'my-description'
        region_name = 'region'
        key = 'key'
        value = 'value'

        args = [
            name,
            '--mead-id', mead_id,
            '--vim-id', vim_id,
            '--description', description,
            '--vim-region-name', region_name,
            '--%s' % key, value]
        position_names = [
            'name',
            'mead_id',
            'vim_id',
            'description',
            'attributes',
        ]
        position_values = [
            name,
            mead_id,
            vim_id,
            description,
            {},
        ]
        extra_body = {key: value, 'placement_attr': {'region_name':
                                                     region_name}}
        self._test_create_resource(self._RESOURCE, cmd, name, my_id,
                                   args, position_names, position_values,
                                   extra_body=extra_body)

    def test_create_mea_with_mead_id(self):
        cmd = mea.CreateMEA(test_cli10.MyApp(sys.stdout), None)
        name = 'my_name'
        my_id = 'my-id'
        mead_id = 'mead'
        args = [
            name,
            '--mead-id', mead_id,
        ]
        position_names = ['name', 'mead_id', 'attributes']
        position_values = [name, mead_id, {}]
        self._test_create_resource(self._RESOURCE, cmd, name, my_id,
                                   args, position_names, position_values)

    def test_create_mea_with_description_param(self):
        cmd = mea.CreateMEA(test_cli10.MyApp(sys.stdout), None)
        name = 'my_name'
        my_id = 'my-id'
        mead_id = 'mead'
        description = 'my-description'
        args = [
            name,
            '--mead-id', mead_id,
            '--description', description,
        ]
        position_names = ['name', 'mead_id', 'description',
                          'attributes']
        position_values = [name, mead_id, description, {}]
        self._test_create_resource(self._RESOURCE, cmd, None, my_id,
                                   args, position_names, position_values)

    def test_list_meas(self):
        cmd = mea.ListMEA(test_cli10.MyApp(sys.stdout), None)
        self._test_list_resources(self._RESOURCES, cmd, True)

    def test_list_meas_pagenation(self):
        cmd = mea.ListMEA(test_cli10.MyApp(sys.stdout), None)
        self._test_list_resources(self._RESOURCES, cmd, True)

    def test_show_mea_id(self):
        cmd = mea.ShowMEA(test_cli10.MyApp(sys.stdout), None)
        args = ['--fields', 'id', self.test_id]
        self._test_show_resource(self._RESOURCE, cmd, self.test_id, args,
                                 ['id'])

    def test_show_mea_id_name(self):
        cmd = mea.ShowMEA(test_cli10.MyApp(sys.stdout), None)
        args = ['--fields', 'id', '--fields', 'name', self.test_id]
        self._test_show_resource(self._RESOURCE, cmd, self.test_id,
                                 args, ['id', 'name'])

    def test_update_mea(self):
        cmd = mea.UpdateMEA(test_cli10.MyApp(sys.stdout), None)
        my_id = 'my-id'
        key = 'new_key'
        value = 'new-value'
        self._test_update_resource(self._RESOURCE, cmd, my_id,
                                   [my_id, '--%s' % key, value],
                                   {key: value})

    def test_delete_mea(self):
        cmd = mea.DeleteMEA(test_cli10.MyApp(sys.stdout), None)
        my_id = 'my-id'
        args = [my_id]
        self._test_delete_resource(self._RESOURCE, cmd, my_id, args)

    def test_list_mea_resources(self):
        cmd = mea.ListMEAResources(test_cli10.MyApp(sys.stdout), None)
        base_args = [self.test_id]
        response = [{'name': 'CP11', 'id': 'id1', 'type': 'NeutronPort'},
                    {'name': 'CP12', 'id': 'id2', 'type': 'NeutronPort'}]
        val = self._test_list_sub_resources(self._MEA_RESOURCES, 'resources',
                                            cmd, self.test_id,
                                            response_contents=response,
                                            detail=True, base_args=base_args)
        self.assertIn('id1', val)
        self.assertIn('NeutronPort', val)
        self.assertIn('CP11', val)

    def test_multi_delete_mea(self):
        cmd = mea.DeleteMEA(test_cli10.MyApp(sys.stdout), None)
        mea_ids = 'mea1 mea2 mea3'
        args = [mea_ids]
        self._test_delete_resource(self._RESOURCE, cmd, mea_ids, args)
