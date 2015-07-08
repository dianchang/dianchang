from permission import Permission
from .rules import VisitorRule, UserRule, AdminRule, UserActiveRule


class VisitorPermission(Permission):
    def rule(self):
        return VisitorRule()


class UserPermission(Permission):
    def __init__(self, active=False):
        self.active = active
        super(UserPermission, self).__init__()

    def rule(self):
        if self.active:
            return UserActiveRule()
        else:
            return UserRule()


class AdminPermission(Permission):
    def rule(self):
        return AdminRule()
