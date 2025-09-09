"""Selective import from https://github.com/aodn/python-aodncore/blob/1.4.9/aodncore/util/__init__.py"""

from .fileops import (extract_gzip, extract_zip, get_file_checksum,
                      is_gzip_file, is_jpeg_file, is_json_file, is_netcdf_file, is_nonempty_file,
                      is_pdf_file, is_png_file, is_tiff_file, is_zip_file, mkdir_p, rm_f, rm_r, rm_rf, rm_rf)
from .misc import (CaptureStdIO, Pattern, format_exception, is_nonstring_iterable, iter_public_attributes, validate_bool,
                   validate_callable, validate_dict, validate_int, validate_mapping,
                   validate_membership, validate_nonstring_iterable, validate_regex, validate_regexes,
                   validate_relative_path, validate_relative_path_attr, validate_string, validate_type,
                   validate_absolute_path, ensure_regex, ensure_regex_list, matches_regexes, slice_sequence,
                   is_function, get_pattern_subgroups_from_string)
from .boltons.setutils import IndexedSet, complement


__all__ = [
    # 'TemporaryDirectory', -- import directly from tempfile
    'CaptureStdIO',
    'ensure_regex',
    'ensure_regex_list',
    'extract_gzip',
    'extract_zip',
    'format_exception',
    'get_file_checksum',
    'get_pattern_subgroups_from_string',
    'IndexedSet',
    'is_function',
    'is_gzip_file',
    'is_jpeg_file',
    'is_json_file',
    'is_netcdf_file',
    'is_nonempty_file',
    'is_pdf_file',
    'is_png_file',
    'is_tiff_file',
    'is_zip_file',
    'is_nonstring_iterable',
    'iter_public_attributes',
    'matches_regexes',
    'mkdir_p',
    'Pattern',
    'rm_f',
    'rm_r',
    'rm_rf',
    'slice_sequence',
    'validate_bool',
    'validate_callable',
    'validate_dict',
    'validate_int',
    'validate_mapping',
    'validate_membership',
    'validate_nonstring_iterable',
    'validate_regex',
    'validate_regexes',
    'validate_relative_path',
    'validate_relative_path_attr',
    'validate_absolute_path',
    'validate_string',
    'validate_type'
]
