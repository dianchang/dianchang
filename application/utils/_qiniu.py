# coding: utf-8
from qiniu import Auth, put_file, put_data


class Qiniu(object):
    def init_app(self, app):
        access_key = app.config.get('QINIU_ACCESS_KEY')
        secret_key = app.config.get('QINIU_SECRET_KEY')
        self.app = app
        self.bucket = app.config.get('QINIU_BUCKET')
        self.auth = Auth(access_key, secret_key)

    def upload_file(self, filename, filepath):
        """上传本地文件"""
        token = self.auth.upload_token(self.bucket, filename)
        ret, info = put_file(token, filename, filepath)

        if info.exception is not None:
            raise UploadError(info)

    def upload_data(self, filename, data):
        """上传二进制数据"""
        token = self.auth.upload_token(self.bucket, filename)
        ret, info = put_data(token, filename, data)

        if info.exception is not None:
            raise UploadError(info)

    def generate_token(self, filename=None, policy=None):
        """生成上传凭证"""
        return self.auth.upload_token(self.bucket, filename, policy=policy)


class UploadError(Exception):
    pass


qiniu = Qiniu()
