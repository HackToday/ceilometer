#
# Copyright 2013 IBM Corp
#
# Author: Tong Li <litong01@us.ibm.com>
#
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

import mock
from oslo.config import fixture as fixture_config
from oslotest import base
import requests

from ceilometer.dispatcher import http
from ceilometer.publisher import utils


class TestDispatcherHttp(base.BaseTestCase):

    def setUp(self):
        super(TestDispatcherHttp, self).setUp()
        self.CONF = self.useFixture(fixture_config.Config()).conf
        self.msg = {'counter_name': 'test',
                    'resource_id': self.id(),
                    'counter_volume': 1,
                    }
        self.msg['message_signature'] = utils.compute_signature(
            self.msg,
            self.CONF.publisher.metering_secret,
        )

    def test_http_dispatcher_config_options(self):
        self.CONF.dispatcher_http.target = 'fake'
        self.CONF.dispatcher_http.timeout = 2
        self.CONF.dispatcher_http.cadf_only = True
        dispatcher = http.HttpDispatcher(self.CONF)

        self.assertEqual('fake', dispatcher.target)
        self.assertEqual(2, dispatcher.timeout)
        self.assertEqual(True, dispatcher.cadf_only)

    def test_http_dispatcher_with_no_target(self):
        self.CONF.dispatcher_http.target = ''
        dispatcher = http.HttpDispatcher(self.CONF)

        # The target should be None
        self.assertEqual('', dispatcher.target)

        with mock.patch.object(requests, 'post') as post:
            dispatcher.record_metering_data(self.msg)

        # Since the target is not set, no http post should occur, thus the
        # call_count should be zero.
        self.assertEqual(0, post.call_count)

    def test_http_dispatcher_with_no_metadata(self):
        self.CONF.dispatcher_http.target = 'fake'
        self.CONF.dispatcher_http.cadf_only = True
        dispatcher = http.HttpDispatcher(self.CONF)

        with mock.patch.object(requests, 'post') as post:
            dispatcher.record_metering_data(self.msg)

        self.assertEqual(0, post.call_count)

    def test_http_dispatcher_without_cadf_event(self):
        self.CONF.dispatcher_http.target = 'fake'
        self.CONF.dispatcher_http.cadf_only = True
        dispatcher = http.HttpDispatcher(self.CONF)

        self.msg['resource_metadata'] = {'request': {'NONE_CADF_EVENT': {
            'q1': 'v1', 'q2': 'v2'}, }, }
        self.msg['message_signature'] = utils.compute_signature(
            self.msg,
            self.CONF.publisher.metering_secret,
        )

        with mock.patch.object(requests, 'post') as post:
            dispatcher.record_metering_data(self.msg)

        # Since the meter does not have metadata or CADF_EVENT, the method
        # call count should be zero
        self.assertEqual(0, post.call_count)

    def test_http_dispatcher_with_cadf_event(self):
        self.CONF.dispatcher_http.target = 'fake'
        self.CONF.dispatcher_http.cadf_only = True
        dispatcher = http.HttpDispatcher(self.CONF)

        self.msg['resource_metadata'] = {'request': {'CADF_EVENT': {
            'q1': 'v1', 'q2': 'v2'}, }, }
        self.msg['message_signature'] = utils.compute_signature(
            self.msg,
            self.CONF.publisher.metering_secret,
        )

        with mock.patch.object(requests, 'post') as post:
            dispatcher.record_metering_data(self.msg)

        self.assertEqual(1, post.call_count)

    def test_http_dispatcher_with_none_cadf_event(self):
        self.CONF.dispatcher_http.target = 'fake'
        self.CONF.dispatcher_http.cadf_only = False
        dispatcher = http.HttpDispatcher(self.CONF)

        self.msg['resource_metadata'] = {'any': {'thing1': 'v1',
                                                 'thing2': 'v2', }, }
        self.msg['message_signature'] = utils.compute_signature(
            self.msg,
            self.CONF.publisher.metering_secret,
        )

        with mock.patch.object(requests, 'post') as post:
            dispatcher.record_metering_data(self.msg)

        self.assertEqual(1, post.call_count)
