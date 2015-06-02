# coding: utf-8
import datetime


def timesince(value):
    """Friendly time gap"""
    if not value:
        return ""

    if not isinstance(value, datetime.date):
        return value

    now = datetime.datetime.now()
    delta = now - value

    if value > now:
        return "刚刚"
    elif delta.days > 1:
        return value.strftime("%Y-%m-%d")
    elif delta.days == 1:
        return "昨天"
    elif delta.seconds > 3600:
        return '%d 小时前' % (delta.seconds / 3600)
    elif delta.seconds > 60:
        return '%d 分钟前' % (delta.seconds / 60)
    else:
        return '刚刚'
