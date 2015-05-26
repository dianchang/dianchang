# coding: utf-8
from .suite import BaseSuite


class TestAnswer(BaseSuite):
    def test_action(self):
        rv = self.client.get('/answer/action')
        assert rv.status_code == 200