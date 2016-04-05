__author__ = 'eandersson'

import logging
import time

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from amqpstorm.base import Rpc
from amqpstorm.base import Stateful
from amqpstorm.base import BaseChannel
from amqpstorm.exception import AMQPChannelError

from tests.utility import FakeConnection
from tests.utility import TestPayload

logging.basicConfig(level=logging.DEBUG)


class BasicChannelTests(unittest.TestCase):
    def test_channel_id(self):
        channel = BaseChannel(1337)
        self.assertEqual(channel.channel_id, 1337)

    def test_add_consumer_tag(self):
        channel = BaseChannel(0)
        channel.add_consumer_tag('my_tag')
        self.assertEqual(channel.consumer_tags[0], 'my_tag')

    def test_remove_single_consumer_tag(self):
        channel = BaseChannel(0)
        channel.add_consumer_tag('1')
        channel.add_consumer_tag('2')
        channel.remove_consumer_tag('1')
        self.assertEqual(len(channel.consumer_tags), 1)
        self.assertEqual(channel.consumer_tags[0], '2')

    def test_remove_all_consumer_tags(self):
        channel = BaseChannel(0)
        channel.add_consumer_tag('my_tag')
        channel.add_consumer_tag('my_tag')
        channel.add_consumer_tag('my_tag')
        channel.remove_consumer_tag()
        self.assertEqual(len(channel.consumer_tags), 0)


class StatefulTests(unittest.TestCase):
    def test_default_is_closed(self):
        stateful = Stateful()
        self.assertTrue(stateful.is_closed)

    def test_set_open(self):
        stateful = Stateful()
        stateful.set_state(Stateful.OPEN)
        self.assertTrue(stateful.is_open)

    def test_set_opening(self):
        stateful = Stateful()
        stateful.set_state(Stateful.OPENING)
        self.assertTrue(stateful.is_opening)

    def test_set_closed(self):
        stateful = Stateful()
        stateful.set_state(Stateful.CLOSED)
        self.assertTrue(stateful.is_closed)

    def test_set_closing(self):
        stateful = Stateful()
        stateful.set_state(Stateful.CLOSING)
        self.assertTrue(stateful.is_closing)


class RpcTests(unittest.TestCase):
    def test_register_request(self):
        rpc = Rpc(FakeConnection())
        uuid = rpc.register_request(['Test'])
        self.assertEqual(len(rpc._request), 1)
        for key in rpc._request:
            self.assertEqual(uuid, rpc._request[key])

    def test_get_request(self):
        rpc = Rpc(FakeConnection())
        uuid = rpc.register_request(['Test'])
        self.assertTrue(rpc.on_frame(TestPayload(name='Test')))
        self.assertIsInstance(rpc.get_request(uuid=uuid, raw=True),
                              TestPayload)

    def test_remove(self):
        rpc = Rpc(FakeConnection())
        uuid = rpc.register_request(['Test'])
        self.assertEqual(len(rpc._request), 1)
        self.assertEqual(len(rpc._response), 1)
        rpc.on_frame(TestPayload(name='Test'))
        rpc.remove(uuid)
        self.assertEqual(len(rpc._request), 0)
        self.assertEqual(len(rpc._response), 0)

    def test_remove_request(self):
        rpc = Rpc(FakeConnection())
        uuid = rpc.register_request(['Test'])
        self.assertEqual(len(rpc._request), 1)
        rpc.remove_request(uuid)
        self.assertEqual(len(rpc._request), 0)

    def test_remove_response(self):
        rpc = Rpc(FakeConnection())
        uuid = rpc.register_request(['Test'])
        self.assertEqual(len(rpc._response), 1)
        rpc.remove_response(uuid)
        self.assertEqual(len(rpc._response), 0)

    def test_remove_request_none(self):
        rpc = Rpc(FakeConnection())
        self.assertIsNone(rpc.remove_request(None))

    def test_remove_response_none(self):
        rpc = Rpc(FakeConnection())
        self.assertIsNone(rpc.remove_response(None))

    def test_get_request_not_found(self):
        rpc = Rpc(FakeConnection())
        self.assertIsNone(rpc.get_request(None))

    def test_on_frame(self):
        rpc = Rpc(FakeConnection())
        uuid = rpc.register_request(['Test'])
        self.assertEqual(rpc._response[uuid], None)
        rpc.on_frame(TestPayload(name='Test'))
        self.assertIsInstance(rpc._response[uuid], TestPayload)

    def test_raises_on_timeout(self):
        rpc = Rpc(FakeConnection(), timeout=0.1)
        uuid = rpc.register_request(['Test'])
        self.assertEqual(rpc._response[uuid], None)
        time.sleep(0.25)
        self.assertRaises(AMQPChannelError, rpc.get_request, uuid)
