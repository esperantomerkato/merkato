import unittest
from mock import patch

from merkato.merkato import Merkato
from merkato.exchanges.test_exchange.exchange import TestExchange


class MerkatoTestCase(unittest.TestCase):
	@patch('merkato.merkato.merkato_exists', return_value=True)
	@patch('merkato.merkato.get_first_order', return_value=None)
	@patch('merkato.merkato.get_last_order', return_value=None)
	@patch('merkato.merkato.get_relevant_exchange', return_value=TestExchange)
	def setUp(self, *_):
		config = {"exchange": "tux", "private_api_key": "abc123", "public_api_key": "def456", "limit_only": False}
		self.merkato = Merkato(config, coin='XMR', base='BTC', spread='.1',
							   bid_reserved_balance='1', ask_reserved_balance='1')

	def test_rebalance_orders__no_new_txes(self):
		result = self.merkato.rebalance_orders([])

	def test_rebalance_orders(self):
		pass

	def test_create_bid_ladder(self):
		pass

	def test_create_ask_ladder(self):
		pass

	def test_merge_orders(self):
		pass

	def test_update_order_book(self):
		pass

	def test_cancelrange(self):
		pass
