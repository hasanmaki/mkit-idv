================================================
FILE: README.md
================================================

# Loguru-config

Loguru-config is a simple configurator for the [Loguru](https://github.com/Delgan/loguru) logging library. It extends
the functionality of Loguru by allowing the user to configure the logger from a configuration file. This package
provides a much-needed feature to Loguru, which is the ability to configure the logger from a configuration file (for
example, using loguru alone, one can't automatically configure the logger to write to `sys.stdout` or `sys.stderr`
from within a configuration file).

The configuration can have syntax similar to the one used by the native `logging` library in Python (i.e. support
`cfg://`, `ext://`, etc.), but extends it to support even more features. It can also be easily extended to support even
more features quite easily (see [Extending the configurator](#extending-the-configurator) for more details).

The configurator supports parsing of JSON, JSON5, YAML, and TOML files (out of the box) and can be extended to support
other formats (again, see [Extending the configurator](#extending-the-configurator) below).

## Installation

```bash
pip install loguru-config
```

## Features

- Supports parsing of JSON, YAML, and TOML files (out of the box) with a simple `Configurator.load` call.
- Supports loading a member of a module from a string (e.g. `ext://sys.stdout`).
- Support referencing another member of the configuration file (e.g. `cfg://loggers.default.handlers.0`).
- Support calling a user-defined function from within the configuration file (e.g. `{ '()': 'datetime.datetime.now' }`).
- Support referencing an environment variable (e.g. `env://HOME`).
- Support referencing (and parsing) referencing another file (e.g. `file://./path/to/file.json`).
- Support parsing literal python (strings, integers, lists, etc.) from within string values in a configuration (e.g.
  `literal://[1, 2, 3]`).
- Support string formatting (e.g. `fmt://{cfg://loggers.default.handlers.0} - {{ESCAPED}}`).
- Also, almost all of these parsings are recursively parsed (except user-defined functions).
- Both the special-case parsing and configuration loading can be easily extended to support more features (see
  [Extending the configurator](#extending-the-configurator) below).

## Examples

The following YAML configuration file

```yaml
handlers:
  - sink: ext://sys.stderr
    format: '[{time}] {message}'
  - sink: file.log
    enqueue: true
    serialize: true
levels:
  - name: NEW
    'no': 13
    icon: ¤
    color: ""
extra:
  common_to_all: default
activation:
  - [ "my_module.secret", false ]
  - [ "another_library.module", true ]
```

will be parsed to

```python
from loguru import logger
import sys

logger.configure(
    handlers=[
        dict(sink=sys.stderr, format="[{time}] {message}"),
        dict(sink="file.log", enqueue=True, serialize=True),
    ],
    levels=[dict(name="NEW", no=13, icon="¤", color="")],
    extra={"common_to_all": "default"},
    activation=[("my_module.secret", False), ("another_library.module", True)],
)
```

## Special-case parsing

There are multiple special cases that are applicable. Some are recursive (i.e. after parsing, their contents will be
reparsed), and some aren't. The recursive cases will be marked as such in their header.

### String fields

1. `ext://` (recursive) - Load the member according to the reference after the prefix. This can be used, for example to
   refer to the application's out-streams (`ext://sys.stdout` or `ext://sys.stderr`), or to any loaded/loadable member
   in your own code (e.g. set the level of verbosity according to a predefined
   member `ext://my_package.utils.log_level`).
2. `cfg://` (recursive) - load a member from elsewhere in the configuration. This is similar to `ext://`, only within
   the configuration. For example, `cfg://handlers.0.level` will refer to the log-level in the first handler. The
   referencing supports both item-getting in dictionaries (`dict.key`), tuples and lists (`list.index`), and
   attribute-getting in other classes (uses the class' `__dict__` attribute).
3. `env://` (recursive) - load the field's value from an environmental variable. Since environmental-variables are only
   strings, `env://` fields can be combined (i.e. contain) `literal://` tags (more on these below). As an example use
   case, one can set an `extra` field to be the Windows username:

   ```yaml
   ...
   extra:
      username: env://USERNAME
   ...
   ```

4. `literal://` - python-evaluate the contents of string following the prefix as literal python. For security reasons,
   the evaluation supports only simple built-in types (i.e. `int`, `float`, `str`, `bool`, `None` and lists,
   dictionaries, sets and tuples of these) without conditionals, assignments, lambda-expressions, etc. These are
   especially useful from loading string-only configurations (like `.ini` files), or mixed with `env://` for loading
   non-string values. Example: `"literal://True"` will evaluate to `True`
5. `fmt://` (recursive) - formats a string in an f-string-like way. This is useful to chain multiple variables. For
   example: `fmt://{env://APPDATA/}/{cfg://extra.name}/logs` evaluates to sub-folder of the application-data directory
   with the name given as the key `name` in the `extra` part.
   Some notes on this tag:
    - To escape curly braces, use double-curly braces (`{{` evaluates to `"{"`).
    - For now, specifying the individual formats of the formatted placeholders is not supported (e.g. one can not
      specify `"{number:.3f}")` because `:` is used in the tag prefixes. This might be resolved in the future.
6. `file://` (recursive) - for cases when you wish parts of the configuration to be shared among different
   configurations, one can do it using this tag. This tag loads the contents of the file (the same way the original file
   is loaded), and parses them to be inplace of the given tag. As an example, consider the case where multiple
   configurations have different `extra` section but similar handlers, the configuration might look like:

   ```yaml
   handlers: 'file://handlers.yaml'
   extra:
      ...
   ...
   ```

### Dictionary fields

1. The user-defined field, or `()`  (NON-RECURSIVE) - when declaring a user-defined field, one should have the contents
   of the field parse as a dictionary with the following keys:
    - `()`: parses as an `ext://` field above, but must refer to a callable.
    - `*` _(optional)_: this key's value, if such key is given, must be a list/tuple of positional arguments to pass to
      the function.
    - `<key>` _(optional)_: keyword-arguments to give the function.

   For example, one might wish to configure a `logging` handler as a sink:

   ```yaml
   handlers:
      - sink:
          "()": logging.handlers.DatagramHandler
          "host": '127.0.0.1'
          "port": 3871
        level: ...
        ...
   ...
   ```

## Extending the configurator

Aside from inheriting the `LoguruConfig` class, there are two ways to extend the existing configurator class:

1. **Add a custom loading function** - by modifying the `LoguruConfig.supported_loaders` field. This field contains a
   list
   of callables that take a string (file name) as an argument and return a parsable object (i.e. a dictionary that can
   be passed as keyword-arguments to the `LoguruConfig` class' constructor). Note that the order of this list matters
   because the loaders will be attempted according to their order in the list.
2. **Add a custom string-field parser** - similarly, one can extend the class' parsing capabilities by
   extending `LoguruConfig.supported_protocol_parsers`. This field contains a list of tuples, where each tuple contains
   two elements:
    - Condition: can be either a callable taking a string and returning a boolean, or a regular expression. If the
      latter is given, then if the expression contains any groups, the first group will be passed to the parsing
      function.
    - Parsing function: a function that takes a string field and parses it.

As an example to the latter, consider the case where a special `eval` field can be given. In this case, one should
extend the configurator as follows:

```python
import re
from loguru_config import LoguruConfig

eval_protocol = re.compile(r'^eval://(.+)$')
LoguruConfig.supported_protocol_parsers = list(LoguruConfig.supported_protocol_parsers) + [
    (eval_protocol, eval)
]

LoguruConfig.load(...)
```

In contrast, one might not want affect all configurators - just one of them. In this case:

```python
import re
from loguru_config import LoguruConfig

eval_protocol = re.compile(r'^eval://(.+)$')
config = LoguruConfig.load(..., configure=False)

config.supported_protocol_parsers = list(LoguruConfig.supported_protocol_parsers) + [
    (eval_protocol, eval)
]

config.parse().configure()
```

================================================
FILE: LICENSE
================================================

MIT License

Copyright (c) 2023 EZinman

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

================================================
FILE: setup.py
================================================

from setuptools import setup, find_namespace_packages

setup(
    name='loguru-config',
    version='0.1.0',
    author='Erez Zinman',
    description='Loguru configuration from configuration files.',
    license='MIT',
    url='<https://github.com/erezinman/loguru-config>',
    long_description=open('README.md').read(),
    packages=find_namespace_packages(include=['loguru_config*']),
    python_requires='>=3.7',
    keywords=['loguru', 'configuration', 'config', 'logging', 'log'],
    install_requires=[
        'loguru>=0.7.0'
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Logging',
    ]
)

================================================
FILE: tox.ini
================================================

# tox.ini

[tox]
envlist = py37,py38,py39,py310,py311

[testenv]
deps = pytest
    loguru
commands = pytest tests

================================================
FILE: loguru_config/**init**.py
================================================

from .loguru_config import LoguruConfig

================================================
FILE: loguru_config/loguru_config.py
================================================

from typing import TYPE_CHECKING, Union, Optional, List, Dict, Any, \
    Sequence, Callable
from typing import Tuple

from loguru_config.parsable_config import ParsableConfiguration, PathLikeStr

if TYPE_CHECKING:
    from loguru import LevelConfig, Record

class LoguruConfig(ParsableConfiguration):
    """
    A configuration for the loguru logger. This class is used to load a configuration from a file or a dictionary,
    and then apply it to the logger. The structure of the configuration is taken from `loguru`'s `logger.configure`
    method.

    See [1] for more information on the structure of the configuration.

    References
    ----------
    [1] https://loguru.readthedocs.io/en/stable/api/logger.html#loguru._logger.Logger.configure

    Parameters
    ----------
    handlers : Sequence[Dict[str, Any]]
        The handlers to use. The keys are the names of the handlers, and the values are the handler configurations.
        The handler configurations are passed to `logger.add` as keyword arguments.

    levels : Sequence[LevelConfig]] optional
        The levels to use. This is a sequence of dictionaries, where each dictionary is passed to `logger.level` as
        keyword arguments. The dictionaries contain the keys `name`, `no` (number), `color`, `icon`.

    extra : dict, optional
        The default contents of the `extra` dictionary (without calling `logger.bind`).

    patcher : Callable[[Record], None], optional
        The record-patcher function to be passed to `logger.patch`.

    activation : Sequence[Tuple[Optional[str], bool]], optional
        The activation configuration to be passed to `logger.add`. The sequence contains tuples of the form
        `(logger_name, active)`, where `logger_name` is the name of the logger to activate, and `active` is a boolean
        indicating whether the logger should be active or not.

    """

    __parsables__ = ['handlers', 'levels', 'extra', 'patcher', 'activation']

    def __init__(self, *, handlers: 'Sequence[Dict[str, Any]]' = None,
                 levels: 'Optional[Sequence[LevelConfig]]' = None,
                 extra: 'Optional[dict]' = None,
                 patcher: 'Optional[Callable[[Record], None]]' = None,
                 activation: 'Optional[Sequence[Tuple[Optional[str], bool]]]' = None):
        self.handlers = handlers
        self.levels = levels
        self.extra = extra
        self.patcher = patcher
        self.activation = activation
        super().__init__()

    @classmethod
    def load(cls, config_or_file: Union[str, PathLikeStr, dict], *, inplace: bool = False,
             configure: bool = True) -> Optional['LoguruConfig']:
        """
        Load a configuration from a file or a dictionary.

        Parameters
        ----------
        config_or_file : Union[PathLikeStr, dict]
            The configuration to load. If a string, it is interpreted as a path to a file.
            If a dictionary, it is interpreted as a configuration dictionary.

        inplace : bool, default False
            Whether modifications to the configuration should be made in-place. If False, a copy of the configuration
            is made before modifications are made.

        configure : bool, optional
            Whether to configure the logger after loading the configuration. If False, the configuration is loaded but
            not applied to the logger. This is useful if you want to load the configuration and then modify it before
            applying it to the logger.

        Returns
        -------
        config: Optional[LoguruConfig]
            The loaded configuration. If `configure` is True, returns None.

        """

        config = super().load(config_or_file, inplace=inplace)
        if configure:
            config.parse().configure()
            return None

        return config

    def configure(self) -> List[int]:
        """
        Configure the logger with the loaded configuration.

        Returns
        -------
        List[int]
            The IDs of the handlers that were added to the logger.
        """
        from loguru import logger

        return logger.configure(
            handlers=self.handlers,
            levels=self.levels,
            extra=self.extra,
            patcher=self.patcher,
            activation=self.activation
        )

================================================
FILE: loguru_config/parsable_config.py
================================================

import copy
import pathlib
import re
import traceback
from typing import TYPE_CHECKING, Union, Optional, Callable, Pattern, Tuple, Collection, Type

from loguru_config.utils import parsers
import os
from loguru_config.utils.loaders import load_toml_config, load_json_config, load_yaml_config, load_json5_config

if TYPE_CHECKING:
    from typing_extensions import Self

try:
    PathLikeStr = os.PathLike[str]
except TypeError:
    PathLikeStr = os.PathLike

cfg_protocol = re.compile(r'^cfg://(._)$')
word_regex = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]_')

file_protocol = re.compile(r'^file://(._)$')
literal_protocol = re.compile(r'^literal://(.*)$')
ext_protocol = re.compile(r'^ext://(._)$')
env_var_protocol = re.compile(r'^env://(.*)$')

fmt_protocol = re.compile(r'^fmt://(.*)$')
format_value_regex = re.compile(r'(\{[^{}]+\}|[^{}]+)')

class ParsableConfiguration:
    """
    A configuration that can be parsed by the configuration loader. This class is used to load a configuration from a
    file or a dictionary, and then apply it to the logger.
    """

    __parsables__: Collection[str]
    """
    The names of the attributes that can be parsed by the configuration loader.
    """

    supported_protocol_parsers: Collection[Tuple[
        Union[Callable[[str], bool], Pattern],
        Callable[['ParsableConfiguration', str], str]
    ]]
    """
    The parsers that are supported by the configuration loader. The keys are the protocol parsers (either a callable
    that takes a string and returns a boolean, or a compiled regular expression); the values are the protocol parsers
    (callables that take a string and return a string).

    In case when a regex is used as a key, and the regex has a group, the group is used as the value to be passed to
    the protocol parser. Otherwise (a callable or no group in the regex), the entire string is passed to the protocol
    parser.
    """

    supported_loaders: Collection[Callable[[str], dict]] = [
        load_json_config,
        load_yaml_config,
        load_json5_config,
        load_toml_config
    ]

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        self.supported_loaders = list(self.supported_loaders)
        self.supported_protocol_parsers = list(self.supported_protocol_parsers)

    @classmethod
    def load(cls: Type['Self'], config_or_file: Union[PathLikeStr, dict], *, inplace: bool = False) -> Optional['Self']:
        """
        Load a configuration from a file or a dictionary.

        Parameters
        ----------
        config_or_file : Union[PathLikeStr, dict]
            The configuration to load. If a string, it is interpreted as a path to a file.
            If a dictionary, it is interpreted as a configuration dictionary.

        inplace : bool, default False
            Whether modifications to the configuration should be made in-place. If False, a copy of the configuration
            is made before modifications are made.

        Returns
        -------
        parsed: ParsableConfiguration
            The loaded Parsable

        """

        if isinstance(config_or_file, dict):
            if not inplace:
                config_or_file = copy.deepcopy(config_or_file)
        else:
            config_or_file = cls._load_from_file(config_or_file)
            if not isinstance(config_or_file, dict):
                raise TypeError(f'Config must be a dict, not {type(config_or_file)!r}.')

        return cls(**config_or_file)

    def parse(self) -> 'Self':
        """
        Parse the configuration. The parsed configuration is stored in the same object.
        """

        for key in self.__parsables__:
            value = getattr(self, key)
            if value is None:
                continue
            setattr(self, key, self._recursive_parse(value))

        return self

    @classmethod
    def _load_from_file(cls, file_path: PathLikeStr):

        with pathlib.Path(file_path).open('r') as f:
            file_contents = f.read()

        received_exceptions = {}
        for loader in cls.supported_loaders:
            try:
                return loader(file_contents)
            except ImportError:
                continue
            except Exception as e:
                received_exceptions[loader.__name__] = e
        else:
            # Arrived here without breaking, so no loader succeeded.
            formatted_exceptions = '\n'.join(
                f'  - {loader_name}: {"".join(traceback.format_exception(type(e), e, e.__traceback__))}'
                for loader_name, e in received_exceptions.items())
            raise SyntaxError(f'Could not load config file "{file_contents}" '
                              f'with any of the following loaders:\n{formatted_exceptions}')

    def _recursive_parse(self, element: Union[dict, list, tuple, str]):
        if isinstance(element, dict):
            if '()' in element:
                return parsers.parse_user_defined(element)
            return {k: self._recursive_parse(v) for k, v in element.items()}
        elif isinstance(element, (list, tuple)):
            tp = type(element)
            return tp(self._recursive_parse(v) for v in element)
        elif isinstance(element, str):
            return self._parse_string(element)
        else:
            return element

    def _parse_string(self, config_str: str):
        result = None
        for cond, handler in self.supported_protocol_parsers:
            if isinstance(cond, str):
                cond = re.compile(cond)
            if isinstance(cond, Pattern):
                match = cond.match(config_str)
                if match:
                    # Check if it has groups, then take the first. Otherwise, pass the original string.
                    if match.groups():
                        result = handler(self, match.group(1))
                    else:
                        result = handler(self, config_str)
            elif callable(cond):
                if cond(config_str):
                    result = handler(self, config_str)
            else:
                raise TypeError(f'Condition must be a regex, or callable, not {type(cond)!r}.')

            if result is not None:
                # Even though we just loaded it, we allow it to be parsed further (as a string).
                return self._recursive_parse(result)

        return config_str

    def _parse_log_part(self, file_path: PathLikeStr):
        loaded = self._load_from_file(file_path)
        return self._recursive_parse(loaded)

    def _parse_format(self, format_str: str):
        # Split by { and } to get the parts that are not inside curly braces.
        parts = format_value_regex.split(format_str)
        for i, part in enumerate(parts):
            if part.startswith('{') and part.endswith('}'):
                part = parts[i] = part[1:-1]
                if part.startswith('{') and part.endswith('}'):
                    # This is an escaped curly brace part, so we skip it.
                    parts[i] = part[1:-1]
                else:
                    # This is a curly brace part, so we need to parse it.
                    parts[i] = str(self._parse_string(parts[i]))

        return ''.join(parts)

ParsableConfiguration.supported_protocol_parsers = [
    (literal_protocol, lambda self, name: parsers.parse_literal(name)),
    (ext_protocol, lambda self, ref: parsers.parse_external(ref)),
    (env_var_protocol, lambda self, name: os.environ[name]),
    (file_protocol, ParsableConfiguration._parse_log_part),
    (cfg_protocol, parsers.parse_reference),
    (fmt_protocol, ParsableConfiguration._parse_format)
]

================================================
FILE: loguru_config/py.typed
================================================

[Empty file]

================================================
FILE: loguru_config/utils/**init**.py
================================================

[Empty file]

================================================
FILE: loguru_config/utils/loaders.py
================================================

def load_toml_config(config_str: str) -> dict:
    import toml
    return toml.loads(config_str)

def load_json_config(config_str: str) -> dict:
    import json
    return json.loads(config_str)

def load_yaml_config(config_str: str) -> dict:
    import yaml
    return yaml.safe_load(config_str)

def load_json5_config(config_str: str) -> dict:
    import pyjson5
    return pyjson5.loads(config_str)

================================================
FILE: loguru_config/utils/parsers.py
================================================

import ast
import importlib
import sys
from typing import Any, Mapping, Union, Sequence, Callable, Optional
import os
import inspect

def parse_literal(literal: str) -> Any:
    """
    Parses a builtin value. The builtin value can be a string, an integer, a float, or a boolean. It can also be
    ``'stderr'`` or ``'stdout'`` to refer to the standard error and standard output streams, respectively. This
    function is useful for parsing string-only values (such as in environment variables).

    Examples
    --------
    >>> parse_literal('1')
    1

    >>> parse_literal('1.0')
    1.0

    >>> os.environ['TEST'] = 'True'
    >>> parse_literal(os.environ['TEST'])
    True

    Parameters
    ----------
    literal : str
         Either a python literal (such as an integer, float, boolean, `None`), or the builtins `stderr` & `stdout` (that
         refer to `sys.stderr` & `sys.stdout` respectively).

    Returns
    -------
    parsed: Any
        The parsed literal.
    """
    if literal == 'stderr':
        return sys.stderr
    if literal == 'stdout':
        return sys.stdout

    return ast.literal_eval(literal)

def parse_reference(reference_object: Union[Mapping, Sequence, Any], ref: str) -> Any:
    """
    References a part of an object using a string. The string is split on ``'.'`` and each part is used to index into
    the object.

    This function is similar to `cpython's ``logging.config.BaseConfigurator.cfg_convert``.

    Examples
    --------
    It is possible to reference a nested dictionary:
    >>> parse_reference({'a': {'b': {'c': 1}}}, 'a.b.c')
    1

    It is possible to reference a nested list:
    >>> parse_reference({'a': [{'b': 1}, {'b': 2}]}, 'a.1.b')
    2

    Also, in case of an integer, it can be parsed as an integer:
    >>> parse_reference({'a': {1: 1}}, 'a.1')
    1

    However, strings take precedence over integers:
    >>> parse_reference({'a': {1: 1, '1': '1'}}, 'a.1')
    '1'

    Also works with `__dict__`s of classes:
    >>> class A: a={'b': {'c': 1}}
    >>> parse_reference(A, 'a.b.c')
    1

    Note that in this example, `A` is used instead of `A()` because `a` is in the class's `__dict__`, not in the
    instance's `__dict__`.


    Parameters
    ----------
    reference_object: Union[Mapping, Sequence]
        The object to reference.

    ref: str
        The reference string. It is split on ``'.'`` and each part is used to index into the object.

    Returns
    -------
    parsed: Any
        The parsed reference.
    """

    current = reference_object
    rest = ref.split('.')

    while len(rest) > 0:
        ref, *rest = rest

        if isinstance(current, (list, tuple)):
            try:
                current = current[int(ref)]
            except ValueError:
                raise KeyError(f'Invalid reference: {ref!r}.')
        else:
            if not isinstance(current, Mapping):
                current = current.__dict__

            try:
                current = current[ref]
            except KeyError:
                if ref.isdigit():
                    current = current[int(ref)]
                else:
                    raise KeyError(f'Invalid reference: {ref!r}.')
    return current

def parse_external(external_ref: str) -> Any:
    """
    This function was copied shamelessly from cpython's ``logging.config.BaseConfigurator.ext_convert``.

    Resolve strings to objects using standard import and attribute syntax.

    Examples
    --------
    >>> parse_external('logging.handlers.RotatingFileHandler')
    <class 'logging.handlers.RotatingFileHandler'>

    >>> parse_external('sys.stdout')   # doctest: +SKIP
    <_io.TextIOWrapper name='<stderr>' mode='w' encoding='utf-8'>
    """
    name = external_ref.split('.')
    used = name.pop(0)
    try:
        found = importlib.import_module(used)
        for frag in name:
            used += '.' + frag
            try:
                found = getattr(found, frag)
            except AttributeError:
                importlib.import_module(used)
                found = getattr(found, frag)
        return found
    except ImportError as e:
        v = ValueError('Cannot resolve %r: %s' % (external_ref, e))
        raise v from e

_missing = object()

def parse_user_defined(user_defined_dict: dict,
                       further_parsing_function: Optional[Callable[[Any], Any]] = None) -> Any:
    """
    Parses a user defined function and calls it with the given arguments. The function is given as a dictionary with
    the following keys:
    - ``'()'``: The path (e.g. "package.subpackage.module") to call. This key is required.
    - ``'*'``: A list of positional arguments to pass to the function. This key is optional.
    - <key-word arguments>: The keys are the name of the arguments, and the values are the value of the argument. These
        keys are optional.

    This function is similar to the configuration syntax used by ``logging``, but extends it to allow for positional
    arguments.

    Examples
    --------
    >>> parse_user_defined({'()': 'sys.exc_info'})
    (None, None, None)

    >>> parse_user_defined({'()': 'datetime.date', 'year': 2020, 'month': 1, 'day': 1})
    datetime.date(2020, 1, 1)

    >>> parse_user_defined({'()': 'builtins.int', '*': ['123']})
    123

    >>> parse_user_defined({'()': 'builtins.str.format', '*': ['{} {world}', 'Hello'], 'world': 'World'})
    'Hello World'

    The ``further_parsing_function`` is called on each argument before calling the user-defined function:
    >>> parse_user_defined({'()': 'builtins.repr', '*': ["1"],})
    "'1'"
    >>> parse_user_defined({'()': 'builtins.repr', '*': ["1"],}, further_parsing_function=int)
    '1'

    Parameters
    ----------
    user_defined_dict: dict
        The dictionary to parse. See the description and the examples for the format.

    further_parsing_function: Optional[Callable[[Any], Any]]
        A function to apply to each value in the dictionary before calling the user-defined function. This is useful
        for parsing references and external references inside arguments.

    Returns
    -------
    parsed: Any
        The parsed user-defined function.
    """
    calling_function = user_defined_dict.pop('()', _missing)
    if calling_function is _missing:
        raise ValueError('User-defined handler must have a "()" key with the function to call.')

    calling_function = parse_external(calling_function)

    if not callable(calling_function):
        raise TypeError(f'User-defined handler must be callable, not {type(calling_function)!r}.')

    args = user_defined_dict.pop('*', ())
    if further_parsing_function is not None:
        user_defined_dict = {k: further_parsing_function(v) for k, v in user_defined_dict.items()}
        args = [further_parsing_function(arg) for arg in args]

    return calling_function(*args, **user_defined_dict)

================================================
FILE: tests/**init**.py
================================================

[Empty file]

================================================
FILE: tests/test_parse_loguru_config.py
================================================

import json
import os
import sys
import io

import pytest
from loguru import logger
from loguru_config import LoguruConfig
from contextlib import redirect_stdout

@pytest.fixture(scope='function')
def temp_file():
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        yield f.name

    if os.path.exists(f.name):
        os.remove(f.name)

def test_normal_config():
    stream = io.StringIO()
    with redirect_stdout(stream) as f:
        logger.configure(
            handlers=[
                {
                    'sink': sys.stdout,
                    'format': '{level} - {message}',
                    'level': 'WARNING',
                },
            ])

        logger.info('Hello, world!')
        logger.critical('Hello, world!')

    assert stream.getvalue() == 'CRITICAL - Hello, world!\n'

def test_simple_config():
    stream = io.StringIO()
    with redirect_stdout(stream) as f:
        config = LoguruConfig(
            handlers=[
                {
                    'sink': 'ext://sys.stdout',
                    'format': '{level} - {message}',
                    'level': 'WARNING',
                },
            ])

        config.parse().configure()

        logger.info('Hello, world!')
        logger.critical('Hello, world!')

    assert stream.getvalue() == 'CRITICAL - Hello, world!\n'

def test_nested_config():
    stream = io.StringIO()
    with redirect_stdout(stream) as f:
        config = LoguruConfig(
            handlers=[
                {
                    'sink': 'ext://sys.stdout',
                    'format': '{level} - {message}',
                    'level': 'env://LOG_LEVEL',
                },
            ])

        os.environ['LOG_LEVEL'] = 'WARNING'

        config.parse().configure()

        logger.info('Hello, world!')
        logger.critical('Hello, world!')

    assert stream.getvalue() == 'CRITICAL - Hello, world!\n'

def test_nested_config_format_with_env():
    stream = io.StringIO()
    with redirect_stdout(stream) as f:
        config = LoguruConfig(
            handlers=[
                {
                    'sink': 'ext://sys.stdout',
                    'format': 'fmt://{{level}} - {env://NAME} - {{message}}',
                },
            ])

        os.environ['NAME'] = '[name]'

        config.parse().configure()

        logger.info('Hello, world!')

    assert stream.getvalue() == 'INFO - [name] - Hello, world!\n'

def test_user_defined_extra_format():
    stream = io.StringIO()
    with redirect_stdout(stream) as f:
        config = LoguruConfig(
            handlers=[
                {
                    'sink': 'ext://sys.stdout',
                    'format': '{level} - [start={extra[start_time]:%Y-%m-%d %H:%M:%S}] - {message}',
                },
            ],
            extra={
                'start_time': {
                    '()': 'datetime.datetime',
                    'year': 2020,
                    'month': 1,
                    'day': 1,
                }
            }
        )

        config.parse().configure()

        logger.info('Hello, world!')

    assert stream.getvalue() == 'INFO - [start=2020-01-01 00:00:00] - Hello, world!\n'

def test_user_defined_extra_repr():
    stream = io.StringIO()
    with redirect_stdout(stream) as f:
        config = LoguruConfig(
            handlers=[
                {
                    'sink': 'ext://sys.stdout',
                    'format': '{level} - [start={extra[start_time]!r}] - {message}',
                },
            ],
            extra={
                'start_time': {
                    '()': 'datetime.datetime',
                    'year': 2020,
                    'month': 1,
                    'day': 1,
                }
            }
        )

        config.parse().configure()

        logger.info('Hello, world!')

    assert stream.getvalue() == 'INFO - [start=datetime.datetime(2020, 1, 1, 0, 0)] - Hello, world!\n'

def test_user_defined_cfg():
    stream = io.StringIO()
    with redirect_stdout(stream) as f:
        config = LoguruConfig(
            extra={
                'start_time': {
                    '()': 'datetime.datetime',
                    'year': 2020,
                    'month': 1,
                    'day': 1,
                }
            },
            handlers=[
                {
                    'sink': 'ext://sys.stdout',
                    'format': 'fmt://{{level}} - [start={cfg://extra.start_time}] - {{message}}',
                },
            ],
        )

        config.parse().configure()

        logger.info('Hello, world!')

    assert stream.getvalue() == 'INFO - [start=2020-01-01 00:00:00] - Hello, world!\n'

def test_parse_level_from_environment_variable():
    stream = io.StringIO()
    with redirect_stdout(stream) as f:
        config = LoguruConfig(
            handlers=[
                {
                    'sink': 'ext://sys.stdout',
                    'format': '{level} ({level.icon}) - {message}',
                }],
            levels=[
                f'env://new_level',
            ]
        )

        os.environ['new_level'] = 'literal://{"name":"NEW", "no":13, "icon":"¤", "color":""}'

        config.parse().configure()

        logger.log('NEW', 'Hello, world!')

    assert stream.getvalue() == 'NEW (¤) - Hello, world!\n'

def test_parse_level_from_another_file(temp_file):
    stream = io.StringIO()
    with redirect_stdout(stream) as f:
        with open(temp_file, 'w') as f:
            json.dump({"name": "NEW2", "no": 14, "icon": "//¤//", "color": ""}, f)

        config = LoguruConfig(
            handlers=[
                {
                    'sink': 'ext://sys.stdout',
                    'format': '{level} ({level.icon}) - {message}',
                }],
            levels=[
                f'file://{temp_file}',
            ]
        )

        config.parse().configure()

        logger.log('NEW2', 'Hello, world!')

    assert stream.getvalue() == 'NEW2 (//¤//) - Hello, world!\n'

def test_loading_yaml_file(temp_file):
    json_contents = """
    {
  "handlers": [
    {
      "sink": "ext://sys.stderr",
      "format": "[{time}] {message}"
    },
    {
      "sink": "file.log",
      "enqueue": true,
      "serialize": true
    }
  ],
  "levels": [
    {
      "name": "NEW",
      "no": 13,
      "icon": "¤",
      "color": ""
    }
  ],
  "extra": {
    "common_to_all": "default"
  },
  "activation": [
    [
      "my_module.secret",
      false
    ],
    [
      "another_library.module",
      true
    ]
  ]
}
    """
    with open(temp_file, 'w') as f:
        f.write(json_contents)

    configurator = LoguruConfig.load(temp_file, configure=False).parse()

    expected_config = dict(
        handlers=[
            dict(sink=sys.stderr, format="[{time}] {message}"),
            dict(sink="file.log", enqueue=True, serialize=True),
        ],
        levels=[dict(name="NEW", no=13, icon="¤", color="")],
        extra={"common_to_all": "default"},
        activation=[["my_module.secret", False], ["another_library.module", True]],
    )

    assert configurator.handlers == expected_config['handlers']
    assert configurator.levels == expected_config['levels']
    assert configurator.extra == expected_config['extra']
    assert configurator.activation == expected_config['activation']

================================================
FILE: tests/test_parsers.py
================================================

import datetime
import sys
from importlib.util import find_spec

import pytest

from loguru_config import LoguruConfig
from loguru_config.parsable_config import literal_protocol, ext_protocol
from loguru_config.utils import parsers

# Most tests lie in the docs and should be called by doctest

def test_doctest():
    import doctest
    result = doctest.testmod(parsers, report=True, verbose=True)
    assert result.failed == 0, result.failed

@pytest.mark.parametrize('str_value,expected', [
    ('True', True),
    ('False', False),
    ('None', None),
    ('13', 13),
    ('3.14', 3.14),
    ('stderr', sys.stderr),
    ('stdout', sys.stdout),
    ('[1, 2, 3]', [1, 2, 3]),
    ("{'a': 1, 'b': 2}", {'a': 1, 'b': 2}),
    ("'a'", 'a'),
])
def test_literal_simple(str_value, expected):
    match = literal_protocol.match(f'literal://{str_value}')
    assert match is not None
    assert parsers.parse_literal(match.group(1)) == expected

@pytest.mark.parametrize('str_value,expected', [
    ('builtins.bool', bool),
    ('sys.stderr', sys.stderr),
    ('importlib.util.find_spec', find_spec),
    ('loguru_config.loguru_config.LoguruConfig', LoguruConfig),
])
def test_parse_external(str_value, expected):
    match = ext_protocol.match(f'ext://{str_value}')
    assert match is not None
    assert parsers.parse_external(match.group(1)) == expected
