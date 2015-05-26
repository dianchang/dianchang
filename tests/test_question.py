# coding: utf-8
from .suite import BaseSuite


class TestQuestion(BaseSuite):
    def test_action(self):
        rv = self.client.get('/question/action')
        assert rv.status_code == 200