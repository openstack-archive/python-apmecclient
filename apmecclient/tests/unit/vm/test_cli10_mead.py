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

from mock import mock_open
from mock import patch
import sys

from apmecclient.common.exceptions import InvalidInput
from apmecclient.apmec.v1_0.mem import mead
from apmecclient.tests.unit import test_cli10


class CLITestV10VmMEADJSON(test_cli10.CLITestV10Base):
    _RESOURCE = 'mead'
    _RESOURCES = 'meads'

    def setUp(self):
        plurals = {'meads': 'mead'}
        super(CLITestV10VmMEADJSON, self).setUp(plurals=plurals)

    @patch("apmecclient.apmec.v1_0.mem.mead.open",
           side_effect=mock_open(read_data="mead"),
           create=True)
    def test_create_mead_all_params(self, mo):
        cmd = mead.CreateMEAD(
            test_cli10.MyApp(sys.stdout), None)
        my_id = 'my-id'
        name = 'my-name'
        attr_key = 'mead'
        attr_val = 'mead'
        args = [
            name,
            '--mead-file', 'mead-file'
        ]
        position_names = ['name']
        position_values = [name]
        extra_body = {
            'service_types': [{'service_type': 'mead'}],
            'attributes': {attr_key: attr_val},
        }
        self._test_create_resource(self._RESOURCE, cmd, None, my_id,
                                   args, position_names, position_values,
                                   extra_body=extra_body)

    @patch("apmecclient.apmec.v1_0.mem.mead.open",
           side_effect=mock_open(read_data="mead"),
           create=True)
    def test_create_mead_with_mandatory_params(self, mo):
        cmd = mead.CreateMEAD(
            test_cli10.MyApp(sys.stdout), None)
        name = 'my_name'
        my_id = 'my-id'
        args = [name, '--mead-file', 'mead-file', ]
        position_names = ['name']
        position_values = [name]
        extra_body = {
            'service_types': [{'service_type': 'mead'}],
            'attributes': {'mead': 'mead'}
        }
        self._test_create_resource(self._RESOURCE, cmd, name, my_id,
                                   args, position_names, position_values,
                                   extra_body=extra_body)

    @patch("apmecclient.apmec.v1_0.mem.mead.open",
           side_effect=mock_open(read_data=""),
           create=True)
    def test_create_mead_with_empty_file(self, mo):
        cmd = mead.CreateMEAD(
            test_cli10.MyApp(sys.stdout), None)
        name = 'my_name'
        my_id = 'my-id'
        args = [name, '--mead-file', 'mead-file', ]
        position_names = ['name']
        position_values = [name]
        extra_body = {
            'service_types': [{'service_type': 'mead'}],
            'attributes': {'mead': 'mead'}
        }
        err = None
        try:
            self._test_create_resource(self._RESOURCE, cmd, name, my_id,
                                       args, position_names, position_values,
                                       extra_body=extra_body)
        except InvalidInput:
            err = True
        self.assertEqual(True, err)

    def test_list_meads(self):
        cmd = mead.ListMEAD(test_cli10.MyApp(sys.stdout), None)
        self._test_list_resources(self._RESOURCES, cmd, True,
                                  template_source='onboarded')

    def test_list_inline_meads(self):
        cmd = mead.ListMEAD(test_cli10.MyApp(sys.stdout), None)
        self._test_list_resources(self._RESOURCES, cmd, True,
                                  template_source='inline')

    def test_list_all_meads(self):
        cmd = mead.ListMEAD(test_cli10.MyApp(sys.stdout), None)
        self._test_list_resources(self._RESOURCES, cmd, True,
                                  template_source='all')

    def test_list_meads_pagenation(self):
        cmd = mead.ListMEAD(test_cli10.MyApp(sys.stdout), None)
        print(cmd)
        self._test_list_resources(self._RESOURCES, cmd, True,
                                  template_source='onboarded')

    def test_show_mead_id(self):
        cmd = mead.ShowMEAD(test_cli10.MyApp(sys.stdout), None)
        args = ['--fields', 'id', self.test_id]
        self._test_show_resource(self._RESOURCE, cmd, self.test_id, args,
                                 ['id'])

    def test_show_mead_id_name(self):
        cmd = mead.ShowMEAD(test_cli10.MyApp(sys.stdout), None)
        args = ['--fields', 'id', '--fields', 'name', self.test_id]
        self._test_show_resource(self._RESOURCE, cmd, self.test_id,
                                 args, ['id', 'name'])

    def test_delete_mead(self):
        cmd = mead.DeleteMEAD(
            test_cli10.MyApp(sys.stdout), None)
        my_id = 'my-id'
        args = [my_id]
        self._test_delete_resource(self._RESOURCE, cmd, my_id, args)

    def test_multi_delete_mead(self):
        cmd = mead.DeleteMEAD(
            test_cli10.MyApp(sys.stdout), None)
        mead_ids = 'my-id1 my-id2 my-id3'
        args = [mead_ids]
        self._test_delete_resource(self._RESOURCE, cmd, mead_ids, args)
