from permission import Permission
from .rules import VisitorRule, UserRule, AdminRule


class VisitorPermission(Permission):
    def rule(self):
        return VisitorRule()


class UserPermission(Permission):
    def __init__(self, active=False, selected_interesting_topics=True):
        self.active = active
        super(UserPermission, self).__init__()

    def rule(self):
        return UserRule()


class AdminPermission(Permission):
    def rule(self):
        return AdminRule()
