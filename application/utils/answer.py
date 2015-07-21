# coding: utf-8
import qrcode
import io
from .helpers import absolute_url_for
from .uploadsets import random_filename
from ._qiniu import qiniu


def generate_qrcode_for_answer(answer):
    """为答案生成qrcode"""
    qr = qrcode.QRCode(box_size=10, border=0)
    qr.add_data(absolute_url_for('answer.mobile_view', uid=answer.id))
    qr.make(fit=True)
    img = qr.make_image()
    output = io.BytesIO()
    img.save(output)
    key = 'answer/%d/%s.png' % (answer.id, random_filename())
    answer.qrcode = key
    qiniu.upload_data(key, output.getvalue())
