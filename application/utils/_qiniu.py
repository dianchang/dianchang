import os
from qiniu import Auth, put_file


class Qiniu(object):
    def init_app(self, app):
        access_key = app.config.get('QINIU_ACCESS_KEY')
        secret_key = app.config.get('QINIU_SECRET_KEY')
        self.app = app
        self.bucket = app.config.get('QINIU_BUCKET')
        self.auth = Auth(access_key, secret_key)

    def upload_file(self, filename, filepath):
        token = self.auth.upload_token(self.bucket, filename)
        ret, info = put_file(token, filename, filepath)

        if info.exception is not None:
            raise UploadError(info)


class UploadError(Exception):
    pass


qiniu = Qiniu()
