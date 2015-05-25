# coding: utf-8
from .suite import BaseSuite


class TestPeople(BaseSuite):
    def test_action(self):
        rv = self.client.get('/people/action')
        assert rv.status_code == 200