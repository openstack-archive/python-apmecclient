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

from apmecclient.apmec.v1_0.events import events
from apmecclient.tests.unit import test_cli10

API_VERSION = "1.0"
FORMAT = 'json'
TOKEN = 'testtoken'
ENDURL = 'localurl'


class CLITestV10EventJSON(test_cli10.CLITestV10Base):
    _EVT_RESOURCE = 'event'
    _EVT_RESOURCES = _EVT_RESOURCE + 's'
    _MEA_EVT_RESOURCE = "mea_event"
    _MEA_EVT_RESOURCES = _MEA_EVT_RESOURCE + 's'
    _MEAD_EVT_RESOURCE = "mead_event"
    _MEAD_EVT_RESOURCES = _MEAD_EVT_RESOURCE + 's'
    _VIM_EVT_RESOURCE = "vim_event"
    _VIM_EVT_RESOURCES = _VIM_EVT_RESOURCE + 's'

    def setUp(self):
        plurals = {'events': 'event', 'mea_events': 'mea_event',
                   'mead_events': 'mead_event', 'vim_events': 'vim_event'}
        super(CLITestV10EventJSON, self).setUp(plurals=plurals)

    def test_list_events(self):
        cmd = events.ListResourceEvents(test_cli10.MyApp(sys.stdout), None)
        self._test_list_resources(self._EVT_RESOURCES, cmd, True)

    def test_show_event_id(self):
        cmd = events.ShowEvent(test_cli10.MyApp(sys.stdout), None)
        args = ['--fields', 'id', self.test_id]
        self._test_show_resource(self._EVT_RESOURCE, cmd, self.test_id, args,
                                 ['id'])

    def notest_list_mea_events(self):
        # TODO(vishwanathj): Need to enhance _test_list_resources()
        # for supporting filters to get this test working
        cmd = events.ListMEAEvents(test_cli10.MyApp(sys.stdout), None)
        self._test_list_resources(self._MEA_EVT_RESOURCES, cmd, True)

    def notest_list_mead_events(self):
        # TODO(vishwanathj): Need to enhance _test_list_resources()
        # for supporting filters to get this test working
        cmd = events.ListMEADEvents(test_cli10.MyApp(sys.stdout), None)
        self._test_list_resources(self._MEAD_EVT_RESOURCES, cmd, True)

    def notest_list_vim_events(self):
        # TODO(vishwanathj): Need to enhance _test_list_resources()
        # for supporting filters to get this test working
        cmd = events.ListVIMEvents(test_cli10.MyApp(sys.stdout), None)
        self._test_list_resources(self._VIM_EVT_RESOURCES, cmd, True)
