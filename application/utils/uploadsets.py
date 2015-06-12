# coding: utf-8
import os
import uuid
from PIL import Image
from flask.ext.uploads import UploadSet, IMAGES, extension, ALL

# UploadSets
images = UploadSet('images', IMAGES)
avatars = UploadSet('avatars', IMAGES)
topic_avatars = UploadSet('topicAvatars', IMAGES)


def process_site_image(file_storage):
    """处理并保存全站通用图片。

    Center clipping, resize and then save the avatar."""
    image = open_image(file_storage)
    image = resize_with_max_width(image, 1000)
    ext = extension(file_storage.filename)
    return save_image(image, images, ext)


def process_user_avatar(file_storage, border):
    """处理并保存用户头像。

    Center clipping, resize and then save the avatar."""
    image = open_image(file_storage)
    image = center_crop(image)
    image = resize_square(image, border)
    ext = extension(file_storage.filename)
    return save_image(image, avatars, ext)


def process_user_background(file_storage, border):
    """处理并保存用户首页背景。"""
    image = open_image(file_storage)
    ext = extension(file_storage.filename)
    return save_image(image, images, ext)


def process_topic_avatar(file_storage, border):
    """处理并保存话题图标。

    Center clipping, resize and then save the avatar.
    """
    image = open_image(file_storage)
    image = center_crop(image)
    image = resize_square(image, border)
    ext = extension(file_storage.filename)
    return save_image(image, topic_avatars, ext)


def open_image(file_storage):
    """Open image from FileStorage."""
    image = Image.open(file_storage.stream)
    # See: https://github.com/smileychris/easy-thumbnails/issues/95
    if image.format == 'JPEG' and image.mode != "RGB":
        image = image.convert("RGB")
    return image


def save_image(image, upload_set, ext):
    """Save image with random filename and original ext."""
    filename = '%s.%s' % (random_filename(), ext)
    dir_path = upload_set.config.destination

    if not os.path.isdir(dir_path):
        os.mkdir(dir_path)
    path = os.path.join(dir_path, filename)
    image.save(path)
    return filename


def center_crop(image):
    w, h = image.size
    if w > h:
        border = h
        avatar_crop_region = ((w - border) / 2, 0, (w + border) / 2, border)
    else:
        border = w
        avatar_crop_region = (0, (h - border) / 2, border, (h + border) / 2)
    return image.crop(avatar_crop_region)


def resize_square(image, border):
    return image.resize((border, border), Image.ANTIALIAS)


def resize_with_max_width(image, max_width):
    """等比例调整图片大小，使其宽不超过某值"""
    w, h = image.size
    if w > max_width:
        target_w = max_width
        target_h = max_width * h / w
        return image.resize((target_w, target_h), Image.ANTIALIAS)
    else:
        return image


def resize_with_max(image, max_value):
    """等比例调整图片大小，使其长与宽不超过某值"""
    w, h = image.size
    if w > h and w > max_value:
        target_w = max_value
        target_h = max_value * h / w
        return image.resize((target_w, target_h), Image.ANTIALIAS)
    elif h > w and h > max_value:
        target_h = max_value
        target_w = max_value * w / h
        return image.resize((target_w, target_h), Image.ANTIALIAS)
    else:
        return image


def random_filename():
    return str(uuid.uuid4())
