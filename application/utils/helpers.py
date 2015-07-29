# coding: utf-8
import os
import errno
import difflib
import string
from flask import current_app, url_for


def absolute_url_for(endpoint, **values):
    """Absolute url for endpoint."""
    config = current_app.config
    site_domain = config.get('SITE_DOMAIN')
    relative_url = url_for(endpoint, **values)
    return join_url(site_domain, relative_url)


def join_url(pre_url, pro_url):
    """拼接url"""
    return "%s/%s" % (pre_url.rstrip('/'), pro_url.lstrip('/'))


def mkdir_p(path):
    """创建文件夹，存在时不报错"""
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def get_domain_from_email(email):
    """获取邮箱的登录入口"""
    email_domains = {
        'qq.com': 'http://mail.qq.com',
        'foxmail.com': 'http://mail.qq.com',
        'gmail.com': 'http://www.gmail.com',
        '126.com': 'http://www.126.com',
        '163.com': 'http://www.163.com',
        '189.cn': 'http://www.189.cn',
        '263.net': 'http://www.263.net',
        'yeah.net': 'http://www.yeah.net',
        'sohu.com': 'http://mail.sohu.com',
        'tom.com': 'http://mail.tom.com',
        'hotmail.com': 'http://www.hotmail.com',
        'yahoo.com.cn': 'http://mail.cn.yahoo.com',
        'yahoo.cn': 'http://mail.cn.yahoo.com',
        '21cn.com': 'http://mail.21cn.com',
    }

    email_domain = ""
    for key, value in email_domains.items():
        if email.count(key) >= 1:
            email_domain = value
            break

    return email_domain


def increase_count(model, attr):
    """对model实例的attr属性+1"""
    current_value = getattr(model, attr)
    if not current_value:
        setattr(model, attr, 1)
    else:
        setattr(model, attr, current_value + 1)


def decrease_count(model, attr):
    """对model实例的attr属性-1"""
    current_value = getattr(model, attr)
    if not current_value:
        setattr(model, attr, 0)
    result_value = current_value - 1
    if result_value < 0:
        setattr(model, attr, 0)
    else:
        setattr(model, attr, result_value)


def text_diff(a, b):
    """
    Takes in strings a and b and returns a human-readable HTML diff.

    See:
    https://github.com/aaronsw/htmldiff
    """

    out = []
    a, b = _html2list(a), _html2list(b)
    try:  # autojunk can cause malformed HTML, but also speeds up processing.
        s = difflib.SequenceMatcher(None, a, b, autojunk=False)
    except TypeError:
        s = difflib.SequenceMatcher(None, a, b)
    for e in s.get_opcodes():
        if e[0] == "replace":
            # @@ need to do something more complicated here
            # call textDiff but not for html, but for some html... ugh
            # gonna cop-out for now
            out.append(
                '<del class="diff modified">' + ''.join(a[e[1]:e[2]]) + '</del><ins class="diff modified">' + ''.join(
                    b[e[3]:e[4]]) + "</ins>")
        elif e[0] == "delete":
            out.append('<del class="diff">' + ''.join(a[e[1]:e[2]]) + "</del>")
        elif e[0] == "insert":
            out.append('<ins class="diff">' + ''.join(b[e[3]:e[4]]) + "</ins>")
        elif e[0] == "equal":
            out.append(''.join(b[e[3]:e[4]]))
        else:
            raise "Um, something's broken. I didn't expect a '" + `e[0]` + "'."
    return ''.join(out)


def _html2list(x, b=0):
    mode = 'char'
    cur = ''
    out = []
    for c in x:
        if mode == 'tag':
            if c == '>':
                if b:
                    cur += ']'
                else:
                    cur += c
                out.append(cur)
                cur = ''
                mode = 'char'
            else:
                cur += c
        elif mode == 'char':
            if c == '<':
                out.append(cur)
                if b:
                    cur = '['
                else:
                    cur = c
                mode = 'tag'
            elif c in string.whitespace:
                out.append(cur + c)
                cur = ''
            else:
                cur += c
    out.append(cur)
    return filter(lambda x: x is not '', out)


def _is_tag(x):
    return x[0] == "<" and x[-1] == ">"
