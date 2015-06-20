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


def cn_month(date):
    """中文月份"""
    month = date.month
    if month == 1:
        return "一月"
    elif month == 2:
        return "二月"
    elif month == 3:
        return "三月"
    elif month == 4:
        return "四月"
    elif month == 5:
        return "五月"
    elif month == 6:
        return "六月"
    elif month == 7:
        return "七月"
    elif month == 8:
        return "八月"
    elif month == 9:
        return "九月"
    elif month == 10:
        return "十月"
    elif month == 11:
        return "十一月"
    elif month == 12:
        return "十二月"
    else:
        raise ValueError()


def day(date):
    return date.strftime("%d")
