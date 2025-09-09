"""This module provides utility functions relating to various filesystem operations

Selectively imported from https://github.com/aodn/python-aodncore/blob/1.4.9/aodncore/util/fileops.py
"""

import errno
import gzip
import hashlib
import json
import os
import shutil
import zipfile
from functools import partial
from io import open

import magic
import netCDF4


# TemporaryDirectory = tempfile.TemporaryDirectory

def extract_gzip(gzip_path, dest_dir, dest_name=None):
    """Extract a GZ (GZIP) file's contents into a directory

    :param gzip_path: path to the source GZ file
    :param dest_dir: destination directory into which the GZ is extracted
    :param dest_name: basename for the extracted file (defaults to the original name minus the '.gz' extension)
    :return: None
    """
    if dest_name is None:
        dest_name = os.path.basename(gzip_path).rstrip('.gz')

    dest_path = os.path.join(dest_dir, dest_name)
    with open(dest_path, 'wb') as f, gzip.open(gzip_path) as g:
        shutil.copyfileobj(g, f)


def extract_zip(zip_path, dest_dir):
    """Extract a ZIP file's contents into a directory

    :param zip_path: path to the source ZIP file
    :param dest_dir: destination directory into which the ZIP is extracted
    :return: None
    """
    with zipfile.ZipFile(zip_path, mode='r') as z:
        z.extractall(dest_dir)


def get_file_checksum(filepath, block_size=65536, algorithm='sha256'):
    """Get the hash (checksum) of a file

    :param filepath: path to the input file
    :param block_size: number of bytes to hash each iteration
    :param algorithm: hash algorithm (from :py:mod:`hashlib` module)
    :return: hash of the input file
    """
    hash_function = getattr(hashlib, algorithm)
    hasher = hash_function()
    with open(filepath, 'rb') as f:
        for block in iter(partial(f.read, block_size), b''):
            hasher.update(block)
    return hasher.hexdigest()


def is_gzip_file(filepath):
    """Check whether a file path refers to a valid ZIP file

    :param filepath: path to the file being checked
    :return: True if filepath is a valid ZIP file, otherwise False
    """
    try:
        with gzip.open(filepath) as g:
            _ = g.read(1)
        return True
    except IOError:
        return False


def is_json_file(filepath):
    """Check whether a file path refers to a valid JSON file

    :param filepath: path to the file being checked
    :return: True if filepath is a valid JSON file, otherwise False
    """
    try:
        with open(filepath) as f:
            _ = json.load(f)
    except ValueError:
        return False
    else:
        return True


def is_netcdf_file(filepath):
    """Check whether a file path refers to a valid NetCDF file

    :param filepath: path to the file being checked
    :return: True if filepath is a valid NetCDF file, otherwise False
    """
    fh = None
    try:
        fh = netCDF4.Dataset(filepath, mode='r')
    except IOError:
        return False
    else:
        return True
    finally:
        if fh:
            fh.close()


def is_nonempty_file(filepath):
    """Check whether a file path refers to a file with length greater than zero

    :param filepath: path to the file being checked
    :return: True if filepath is non-zero, otherwise False
    """
    return os.path.getsize(filepath) > 0


def is_zip_file(filepath):
    """Check whether a file path refers to a valid ZIP file

    :param filepath: path to the file being checked
    :return: True if filepath is a valid ZIP file, otherwise False
    """
    return zipfile.is_zipfile(filepath)


def rm_f(path):
    """Remove a file, ignoring "file not found" errors (analogous to shell command 'rm -f')

    :param path: path to file being deleted
    :return: None
    """
    try:
        os.remove(path)
    except OSError as e:
        if e.errno != errno.ENOENT:
            raise  # pragma: no cover


def rm_r(path):
    """Remove a file or directory recursively (analogous to shell command 'rm -r')

    :param path: path to file being deleted
    :return: None
    """
    try:
        shutil.rmtree(path)
    except OSError as e:
        if e.errno == errno.ENOTDIR:
            os.remove(path)
        else:
            raise


def rm_rf(path):
    """Remove a file or directory, ignoring "file not found" errors (analogous to shell command 'rm -f')

    :param path: path to file being deleted
    :return: None
    """
    try:
        shutil.rmtree(path)
    except OSError as e:
        if e.errno == errno.ENOTDIR:
            rm_f(path)
        elif e.errno != errno.ENOENT:
            raise  # pragma: no cover


def validate_mime_type(t):
    """Closure to generate mime type validation functions

    :param t: type
    :return: function reference to a function which validates a given path is a file with the mime type of type `t`
    """

    def validate_type_func(o):
        mime_type = magic.Magic(mime=True).from_file(o)
        if mime_type != t:
            raise TypeError("filepath '{o}' must be of type '{t}'. Detected type: {m}".format(o=o, t=t, m=mime_type))

    return validate_type_func


validate_jpeg_file = validate_mime_type('image/jpeg')
validate_pdf_file = validate_mime_type('application/pdf')
validate_png_file = validate_mime_type('image/png')
validate_tiff_file = validate_mime_type('image/tiff')


def is_jpeg_file(filepath):
    try:
        validate_jpeg_file(filepath)
    except TypeError:
        return False
    else:
        return True


def is_pdf_file(filepath):
    try:
        validate_pdf_file(filepath)
    except TypeError:
        return False
    else:
        return True


def is_png_file(filepath):
    try:
        validate_png_file(filepath)
    except TypeError:
        return False
    else:
        return True


def is_tiff_file(filepath):
    try:
        validate_tiff_file(filepath)
    except TypeError:
        return False
    else:
        return True


def mkdir_p(path, mode=0o755):
    """Recursively create a directory, including parent directories (analogous to shell command 'mkdir -p')

    :param mode:
    :param path: path to new directory
    :return: None
    """
    try:
        os.makedirs(path, mode)
    except OSError as e:
        if e.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise
