# coding: utf-8
from .suite import BaseSuite


class TestUser(BaseSuite):
    def test_action(self):
        rv = self.client.get('/user/action')
        assert rv.status_code == 200
