"""This module provides miscellaneous utility functions *not* related to filesystem or subprocess operations.
These are typically functions which query, manipulate or transform Python objects.

Selectively imported from https://github.com/aodn/python-aodncore/blob/1.4.9/aodncore/util/misc.py
"""

import os
import re
import types
from enum import EnumMeta, Enum
from typing import Mapping, Iterable
import sys
from io import StringIO


def format_exception(exception):
    """Return a pretty string representation of an Exception object containing the Exception name and message

    :param exception: :py:class:`Exception` object
    :return: string
    """
    return "{cls}: {message}".format(cls=exception.__class__.__name__, message=exception)

def get_regex_subgroups_from_string(string, regex):
    """Function to retrieve parts of a string given a compiled pattern (re.compile(pattern))
    the pattern needs to match the beginning of the string
    (see https://docs.python.org/2/library/re.html#re.RegexObject.match)

    * No need to start the pattern with "^"; and
    * To match anywhere in the string, start the pattern with ".*".

    :return: dictionary of fields matching a given pattern
    """
    compiled_regex = ensure_regex(regex)
    m = compiled_regex.match(string)
    return {} if m is None else m.groupdict()

get_pattern_subgroups_from_string = get_regex_subgroups_from_string

def iter_public_attributes(instance, ignored_attributes=None):
    """Get an iterator over an instance's public attributes, *including* properties

    :param instance: object instance
    :param ignored_attributes: set of attribute names to exclude
    :return: iterator over the instances public attributes
    """
    ignored_attributes = {} if ignored_attributes is None else set(ignored_attributes)

    def includeattr(attr):
        if attr.startswith('_') or attr in ignored_attributes:
            return False
        return True

    attribute_names = set(getattr(instance, '__slots__', getattr(instance, '__dict__', {})))
    property_names = {p for p in dir(instance.__class__) if isinstance(getattr(instance.__class__, p), property)}
    all_names = attribute_names.union(property_names)

    public_attrs = {a: getattr(instance, a) for a in all_names if includeattr(a)}

    return iter(public_attrs.items())


def validate_type(t):
    """Closure to generate type validation functions

    :param t: type
    :return: function reference to a function which validates a given input is an instance of type `t`
    """

    def validate_type_func(o):
        if not isinstance(o, t):
            raise TypeError("object '{o}' must be of type '{t}'".format(o=o, t=t))

    return validate_type_func


def validate_callable(o):
    if not callable(o):
        raise TypeError('value must be a Callable object')


def validate_relative_path_attr(path, path_attr):
    """Validate a path, raising an exception containing the name of the attribute which failed

    :param path: string containing the path to test
    :param path_attr: attribute name to include in the exceptions message if validation fails
    :return: None
    """
    try:
        validate_relative_path(path)
    except ValueError as e:
        raise ValueError("error validating '{attr}': {e}".format(attr=path_attr, e=e))


validate_bool = validate_type(bool)
validate_dict = validate_type(dict)
validate_int = validate_type(int)
validate_mapping = validate_type(Mapping)
validate_string = validate_type(str)


def validate_nonstring_iterable(o):
    if not is_nonstring_iterable(o):
        raise TypeError('value must be a non-string Iterable')


def validate_regex(o):
    if isinstance(o, Pattern):
        return
    try:
        re.compile(o)
    except re.error as e:
        raise ValueError("invalid regex '{o}'. {e}".format(o=o, e=format_exception(e)))
    except TypeError as e:
        raise TypeError("invalid regex '{o}'. {e}".format(o=o, e=format_exception(e)))


def validate_regexes(o):
    validate_nonstring_iterable(o)
    for regex in o:
        validate_regex(regex)


def validate_relative_path(o):
    if os.path.isabs(o):
        raise ValueError("path '{o}' must be a relative path".format(o=o))


def validate_absolute_path(o):
    if not os.path.isabs(o):
        raise ValueError(f"path '{o}' must be an absolute path")


Pattern = type(re.compile(''))


def validate_membership(c):
    def validate_membership_func(o):
        # Compatibility fix for Python <3.8.
        # Python 3.8 raises a TypeError when testing for non-Enum objects, so this causes this function to also raise
        # a TypeError in earlier Python 3 versions. This can be removed when Python 3.8 becomes the minimum required
        # version.
        if isinstance(c, (EnumMeta, Enum)) and not isinstance(o, (EnumMeta, Enum)):
            raise TypeError(
                "unsupported operand type(s) for 'in': '%s' and '%s'" % (
                    type(o).__qualname__, c.__class__.__qualname__))

        if o not in c:
            raise ValueError("value '{o}' must be a member of '{c}'".format(o=o, c=c))

    return validate_membership_func


def is_nonstring_iterable(sequence):
    """Check whether an object is a non-string :py:class:`Iterable`

    :param sequence: object to check
    :return: True if object is a non-string sub class of :py:class:`Iterable`
    """
    return isinstance(sequence, Iterable) and not isinstance(sequence, (str, bytes, Mapping))


def ensure_regex(o):
    """Ensure that the returned value is a compiled regular expression (Pattern) from a given input, or raise if the
    object is not a valid regular expression

    :param o: input object, a single regex (string or pre-compiled)
    :return: :py:class:`Pattern` instance
    """
    validate_regex(o)
    if isinstance(o, Pattern):
        return o
    return re.compile(o)


def ensure_regex_list(o):
    """Ensure that the returned value is a list of compiled regular expressions (Pattern) from a given input, or raise
    if the object is not a list of valid regular expression

    :param o: input object, either a single regex or a sequence of regexes (string or pre-compiled)
    :return: :py:class:`list` of :py:class:`Pattern` instances
    """
    if o is None:
        return []

    # if parameter is a single valid pattern, return it wrapped in a list
    try:
        return [ensure_regex(o)]
    except TypeError:
        pass

    validate_nonstring_iterable(o)
    return [ensure_regex(p) for p in o]

def ensure_string_list(input_string):
    """Ensure that the returned string is in a list, or raise
       if string is not in a list

    :param input_string: input string/s, either a single string or a sequence of strings
    :return: :py:class:`list` of :py:class:`Pattern` instances
    """
    if not isinstance(input_string, list) and input_string != None:
        return [input_string]

    if input_string == None:
        return []

    return input_string

def matches_regexes(input_string, include_regexes, exclude_regexes=None):
    """Function to filter a string (e.g. file path) according to regular expression inclusions minus exclusions

    :param input_string: string for comparing with the regular expressions
    :param include_regexes: list of regular expressions required in input_string
    :param exclude_regexes: list of regular expressions not required in input_string
    :return: True if input_string matches one of the 'include_regexes' but *not* one of the 'exclude_regexes'
    """

    # confirm that include/exclude_extensions is a list, if not convert
    includes = ensure_regex_list(include_regexes)
    excludes = ensure_regex_list(exclude_regexes)

    matches_includes = any(re.match(r, input_string) for r in includes)
    matches_excludes = any(re.match(r, input_string) for r in excludes)

    if matches_includes and not matches_excludes:
        return True
    return False

def matches_extensions(input_string, include_extensions, exclude_extensions=None):
    """Function to filter a string (e.g. file path) according to file extensions

    :param input_string: string to check whether extension accepted
    :param include_extensions: list of extensions allowed
    :param exclude_extensions: list of disallowed extensions
    :return: True if the string matches one of the 'include_extensions' but *not* one of the 'exclude_extensions'
    """

    # confirm that include/exclude_extensions is a list, if not convert
    include_extensions = ensure_string_list(include_extensions)
    exclude_extensions = ensure_string_list(exclude_extensions)

    # identify extension from input_string
    _, ext = os.path.splitext(input_string)

    # Check for extension
    matches_includes = (ext in include_extensions) if include_extensions else True
    matches_excludes = (ext in exclude_extensions) if exclude_extensions else False

    if matches_includes and not matches_excludes:
        return True
    return False


def slice_sequence(sequence, slice_size):
    """Return a :py:class:`list` containing the input :py:class:`Sequence` sliced into :py:class:`Sequence` instances
    with a length equal to or less than :py:attr:`slice_size`

    .. note:: The type of the elements should be the same type as the original sequence based on the usual Python
        slicing behaviour, but the outer sequence will always be a :py:class:`list` type.

    :param sequence: input sequence
    :param slice_size: size of each sub-Sequence
    :return: :py:class:`list` of :py:class:`Sequence` instances
    """
    return [sequence[x:x + slice_size] for x in range(0, len(sequence), slice_size)]


def is_function(o):
    """Check whether a given object is a function

    :param o: object to check
    :return: True if object is a function, otherwise False
    """
    return isinstance(o, (types.FunctionType, types.MethodType))

class CaptureStdIO(object):
    """Context manager to capture stdout and stderr emitted from the block into a list.
        Optionally merge stdout and stderr streams into stdout.
    """

    def __init__(self, merge_streams=False):
        self._merge_streams = merge_streams
        self.__stdout_lines = []
        self.__stderr_lines = []

    def __enter__(self):
        self.old_stdout, self.old_stderr = sys.stdout, sys.stderr

        sys.stdout = self._stdout_stringio = StringIO()
        self._stderr_stringio = self._stdout_stringio if self._merge_streams else StringIO()
        sys.stderr = self._stderr_stringio

        return self.__stdout_lines, self.__stderr_lines

    def __exit__(self, *args):
        self.__stdout_lines.extend(self._stdout_stringio.getvalue().splitlines())
        if not self._merge_streams:
            self.__stderr_lines.extend(self._stderr_stringio.getvalue().splitlines())
        del self._stdout_stringio, self._stderr_stringio
        sys.stdout, sys.stderr = self.old_stdout, self.old_stderr
