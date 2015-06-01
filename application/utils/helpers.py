# coding: utf-8
import os
import errno
from flask import current_app, url_for
from pypinyin import lazy_pinyin


def absolute_url_for(endpoint, **values):
    """Absolute url for endpoint."""
    config = current_app.config
    site_domain = config.get('SITE_DOMAIN')
    relative_url = url_for(endpoint, **values)
    return join_url(site_domain, relative_url)


def join_url(pre_url, pro_url):
    return "%s/%s" % (pre_url.rstrip('/'), pro_url.lstrip('/'))


def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def lcs(a, b):
    if not a or not b:
        return [], []

    lena = len(a)
    lenb = len(b)
    c = [[0 for i in range(lenb + 1)] for j in range(lena + 1)]
    flag = [[0 for i in range(lenb + 1)] for j in range(lena + 1)]
    for i in range(lena):
        for j in range(lenb):
            if a[i] == b[j]:
                c[i + 1][j + 1] = c[i][j] + 1
                flag[i + 1][j + 1] = 'ok'
            elif c[i + 1][j] > c[i][j + 1]:
                c[i + 1][j + 1] = c[i + 1][j]
                flag[i + 1][j + 1] = 'left'
            else:
                c[i + 1][j + 1] = c[i][j + 1]
                flag[i + 1][j + 1] = 'up'
    return c, flag


def generate_lcs_html(src, dest):
    if not src and not dest:
        return ""
    elif not src:
        return "<ins>%s</ins>" % dest
    elif not dest:
        return "<del>%s</del>" % src

    c, flag = lcs(src, dest)

    result = []
    result_string = ""
    i = len(src)
    j = len(dest)

    while i > 0 and j > 0:
        result_item = {
            'dir': flag[i][j]
        }

        if flag[i][j] == 'ok':
            result_item['char'] = src[i - 1]
            i -= 1
            j -= 1
        elif flag[i][j] == 'left':
            result_item['char'] = dest[j - 1]
            j -= 1
        else:
            result_item['char'] = src[i - 1]
            i -= 1

        result.insert(0, result_item)

    while not (i == 0 and j == 0):
        if i != 0:
            result.insert(0, {
                'dir': 'up',
                'char': src[i - 1]
            })
            i -= 1
        elif j != 0:
            result.insert(0, {
                'dir': 'left',
                'char': dest[j - 1]
            })
            j -= 1

    pre_dir = ""
    current_dir = ""

    # ok - match
    # left - insert
    # up - delete

    for index, item in enumerate(result):
        if index == 0:
            current_dir = item['dir']
            if current_dir == 'left':
                result_string += "<ins>" + item['char']
            elif current_dir == 'up':
                result_string += "<del>" + item['char']
            else:
                result_string += item['char']
        else:
            pre_dir = current_dir
            current_dir = item['dir']

            if pre_dir != current_dir:
                if pre_dir == 'left':
                    result_string += "</ins>"
                elif pre_dir == 'up':
                    result_string += "</del>"

                if current_dir == 'left':
                    result_string += "<ins>" + item['char']
                elif current_dir == 'up':
                    result_string += "<del>" + item['char']
                else:
                    result_string += item['char']
            else:
                result_string += item['char']

    if current_dir == 'left':
        result_string += "</ins>"
    elif current_dir == 'up':
        result_string += "</del>"

    return result_string


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


def pinyin(text):
    """将文本转换为拼音"""
    return ''.join(lazy_pinyin(unicode(text)))
