# coding: utf-8
from .suite import BaseSuite


class TestTopic(BaseSuite):
    def test_action(self):
        rv = self.client.get('/topic/action')
        assert rv.status_code == 200