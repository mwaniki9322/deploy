import os
import uuid
from PIL import Image


def crop_img(data):
    img = Image.open(data['image_field'])
    cropped_img = img.crop((
        data['x'], data['y'], data['w'] + data['x'], data['h'] + data['y']
    ))
    return cropped_img.resize((data['width'], data['height']), Image.ANTIALIAS)


def resize_image(img_path):
    basewidth = 1600
    img = Image.open(img_path)
    wpercent = (basewidth / float(img.size[0]))
    hsize = int((float(img.size[1]) * float(wpercent)))
    img = img.resize((basewidth, hsize), Image.ANTIALIAS)
    img.save(img_path)


def rename_model_file(file, instance):
    """
    Rename a model file
    """
    initial_path = file.path

    split_path = file.name.split('/')
    ext = initial_path.split('.')[-1]
    filename = "%s.%s" % (uuid.uuid4(), ext)

    file.name = '{}/{}/{}/{}/{}'.format(
        split_path[0], split_path[1], split_path[2], split_path[3], filename
    )

    new_path = '{}/{}'.format(file.storage.location, file.name)

    # Move the file on the filesystem
    os.rename(initial_path, new_path)
    instance.save()


def uploaded_file_temp_save(f, ext):

    file_path = '/tmp/{}.{}'.format(uuid.uuid4(), ext)

    with open(file_path, 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)

    return file_path
