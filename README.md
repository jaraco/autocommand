[![PyPI version](https://badge.fury.io/py/autocommand.svg)](https://badge.fury.io/py/autocommand)
![GitHub Workflow Status (master branch)](https://img.shields.io/github/workflow/status/Lucretiel/autocommand/Python%20application/master?logo=pytest)

# autocommand

A library to automatically generate and run simple argparse parsers from function signatures.

## Installation

Autocommand is installed via pip:

```
$ pip install autocommand
```

## Usage

Autocommand turns a function into a command-line program. It converts the function's parameter signature into command-line arguments, and automatically runs the function if the module was called as `__main__`. In effect, it lets your create a smart main function.

```python
from autocommand import autocommand

# This program takes exactly one argument and echos it.
@autocommand(__name__)
def echo(thing):
    print(thing)
```

```
$ python echo.py hello
hello
$ python echo.py -h
usage: echo [-h] thing

positional arguments:
  thing

optional arguments:
  -h, --help  show this help message and exit
$ python echo.py hello world  # too many arguments
usage: echo.py [-h] thing
echo.py: error: unrecognized arguments: world
```

As you can see, autocommand converts the signature of the function into an argument spec. When you run the file as a program, autocommand collects the command-line arguments and turns them into function arguments. The function is executed with these arguments, and then the program exits with the return value of the function, via `sys.exit`. Autocommand also automatically creates a usage message, which can be invoked with `-h` or `--help`, and automatically prints an error message when provided with invalid arguments.

### Types

You can use a type annotation to give an argument a type. Any type (or in fact any callable) that returns an object when given a string argument can be used, though there are a few special cases that are described later.

```python
@autocommand(__name__)
def net_client(host, port: int):
    ...
```

Autocommand will catch `TypeErrors` raised by the type during argument parsing, so you can supply a callable and do some basic argument validation as well.

### Trailing Arguments

You can add a `*args` parameter to your function to give it trailing arguments. The command will collect 0 or more trailing arguments and supply them to `args` as a tuple. If a type annotation is supplied, the type is applied to each argument.

```python
# Write the contents of each file, one by one
@autocommand(__name__)
def cat(*files):
    for filename in files:
        with open(filename) as file:
            for line in file:
                print(line.rstrip())
```

```
$ python cat.py -h
usage: ipython [-h] [file [file ...]]

positional arguments:
  file

optional arguments:
  -h, --help  show this help message and exit
```

### Options

To create `--option` switches, just assign a default. Autocommand will automatically create `--long` and `-s`hort switches.

```python
@autocommand(__name__)
def do_with_config(argument, config='~/foo.conf'):
    pass
```

```
$ python example.py -h
usage: example.py [-h] [-c CONFIG] argument

positional arguments:
  argument

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
```

The option's type is automatically deduced from the default, unless one is explicitly given in an annotation:

```python
@autocommand(__name__)
def http_connect(host, port=80):
    print('{}:{}'.format(host, port))
```

```
$ python http.py -h
usage: http.py [-h] [-p PORT] host

positional arguments:
  host

optional arguments:
  -h, --help            show this help message and exit
  -p PORT, --port PORT
$ python http.py localhost
localhost:80
$ python http.py localhost -p 8080
localhost:8080
$ python http.py localhost -p blah
usage: http.py [-h] [-p PORT] host
http.py: error: argument -p/--port: invalid int value: 'blah'
```

#### None

If an option is given a default value of `None`, it reads in a value as normal, but supplies `None` if the option isn't provided.

#### Switches

If an argument is given a default value of `True` or `False`, or
given an explicit `bool` type, it becomes an option switch.

```python
    @autocommand(__name__)
    def example(verbose=False, quiet=False):
        pass
```

```
$ python example.py -h
usage: example.py [-h] [-v] [-q]

optional arguments:
  -h, --help     show this help message and exit
  -v, --verbose
  -q, --quiet
```

Autocommand attempts to do the "correct thing" in these cases- if the default is `True`, then supplying the switch makes the argument `False`; if the type is `bool` and the default is some other `True` value, then supplying the switch makes the argument `False`, while not supplying the switch makes the argument the default value.

Autocommand also supports the creation of switch inverters. Pass `add_nos=True` to `autocommand` to enable this.

```
    @autocommand(__name__, add_nos=True)
    def example(verbose=False):
        pass
```

```
$ python example.py -h
usage: ipython [-h] [-v] [--no-verbose]

optional arguments:
  -h, --help     show this help message and exit
  -v, --verbose
  --no-verbose
```

Using the `--no-` version of a switch will pass the opposite value in as a function argument. If multiple switches are present, the last one takes precedence.

#### Files

If the default value is a file object, such as `sys.stdout`, then autocommand just looks for a string, for a file path. It doesn't do any special checking on the string, though (such as checking if the file exists); it's better to let the client decide how to handle errors in this case. Instead, it provides a special context manager called `smart_open`, which behaves exactly like `open` if a filename or other openable type is provided, but also lets you use already open files:

```python
from autocommand import autocommand, smart_open
import sys

# Write the contents of stdin, or a file, to stdout
@autocommand(__name__)
def write_out(infile=sys.stdin):
    with smart_open(infile) as f:
        for line in f:
            print(line.rstrip())
    # If a file was opened, it is closed here. If it was just stdin, it is untouched.
```

```
$ echo "Hello World!" | python write_out.py | tee hello.txt
Hello World!
$ python write_out.py --infile hello.txt
Hello World!
```

### Descriptions and docstrings

The `autocommand` decorator accepts `description` and `epilog` kwargs, corresponding to the `description <https://docs.python.org/3/library/argparse.html#description>`_ and `epilog <https://docs.python.org/3/library/argparse.html#epilog>`_ of the `ArgumentParser`. If no description is given, but the decorated function has a docstring, then it is taken as the `description` for the `ArgumentParser`. You can also provide both the description and epilog in the docstring by splitting it into two sections with 4 or more - characters.

```python
@autocommand(__name__)
def copy(infile=sys.stdin, outfile=sys.stdout):
    '''
    Copy an the contents of a file (or stdin) to another file (or stdout)
    ----------
    Some extra documentation in the epilog
    '''
    with smart_open(infile) as istr:
        with smart_open(outfile, 'w') as ostr:
            for line in istr:
                ostr.write(line)
```

```
$ python copy.py -h
usage: copy.py [-h] [-i INFILE] [-o OUTFILE]

Copy an the contents of a file (or stdin) to another file (or stdout)

optional arguments:
  -h, --help            show this help message and exit
  -i INFILE, --infile INFILE
  -o OUTFILE, --outfile OUTFILE

Some extra documentation in the epilog
$ echo "Hello World" | python copy.py --outfile hello.txt
$ python copy.py --infile hello.txt --outfile hello2.txt
$ python copy.py --infile hello2.txt
Hello World
```

### Parameter descriptions

You can also attach description text to individual parameters in the annotation. To attach both a type and a description, supply them both in any order in a tuple

```python
@autocommand(__name__)
def copy_net(
    infile: 'The name of the file to send',
    host: 'The host to send the file to',
    port: (int, 'The port to connect to')):

    '''
    Copy a file over raw TCP to a remote destination.
    '''
    # Left as an exercise to the reader
```

### Decorators and wrappers

Autocommand automatically follows wrapper chains created by `@functools.wraps`. This means that you can apply other wrapping decorators to your main function, and autocommand will still correctly detect the signature.

```python
from functools import wraps
from autocommand import autocommand

def print_yielded(func):
    '''
    Convert a generator into a function that prints all yielded elements
    '''
    @wraps(func)
    def wrapper(*args, **kwargs):
        for thing in func(*args, **kwargs):
            print(thing)
    return wrapper

@autocommand(__name__,
    description= 'Print all the values from START to STOP, inclusive, in steps of STEP',
    epilog=      'STOP and STEP default to 1')
@print_yielded
def seq(stop, start=1, step=1):
    for i in range(start, stop + 1, step):
        yield i
```

```
$ seq.py -h
usage: seq.py [-h] [-s START] [-S STEP] stop

Print all the values from START to STOP, inclusive, in steps of STEP

positional arguments:
  stop

optional arguments:
  -h, --help            show this help message and exit
  -s START, --start START
  -S STEP, --step STEP

STOP and STEP default to 1
```

Even though autocommand is being applied to the `wrapper` returned by `print_yielded`, it still retreives the signature of the underlying `seq` function to create the argument parsing.

### Custom Parser

While autocommand's automatic parser generator is a powerful convenience, it doesn't cover all of the different features that argparse provides. If you need these features, you can provide your own parser as a kwarg to `autocommand`:

```python
from argparse import ArgumentParser
from autocommand import autocommand

parser = ArgumentParser()
# autocommand can't do optional positonal parameters
parser.add_argument('arg', nargs='?')
# or mutually exclusive options
group = parser.add_mutually_exclusive_group()
group.add_argument('-v', '--verbose', action='store_true')
group.add_argument('-q', '--quiet', action='store_true')

@autocommand(__name__, parser=parser)
def main(arg, verbose, quiet):
    print(arg, verbose, quiet)
```

```
$ python parser.py -h
usage: write_file.py [-h] [-v | -q] [arg]

positional arguments:
  arg

optional arguments:
  -h, --help     show this help message and exit
  -v, --verbose
  -q, --quiet
$ python parser.py
None False False
$ python parser.py hello
hello False False
$ python parser.py -v
None True False
$ python parser.py -q
None False True
$ python parser.py -vq
usage: parser.py [-h] [-v | -q] [arg]
parser.py: error: argument -q/--quiet: not allowed with argument -v/--verbose
```

Any parser should work fine, so long as each of the parser's arguments has a corresponding parameter in the decorated main function. The order of parameters doesn't matter, as long as they are all present. Note that when using a custom parser, autocommand doesn't modify the parser or the retrieved arguments. This means that no description/epilog will be added, and the function's type annotations and defaults (if present) will be ignored.

## Testing and Library use

The decorated function is only called and exited from if the first argument to `autocommand` is `'__main__'` or `True`. If it is neither of these values, or no argument is given, then a new main function is created by the decorator. This function has the signature `main(argv=None)`, and is intended to be called with arguments as if via `main(sys.argv[1:])`. The function has the attributes `parser` and `main`, which are the generated `ArgumentParser` and the original main function that was decorated. This is to facilitate testing and library use of your main. Calling the function triggers a `parse_args()` with the supplied arguments, and returns the result of the main function. Note that, while it returns instead of calling `sys.exit`, the `parse_args()` function will raise a `SystemExit` in the event of a parsing error or `-h/--help` argument.

```python
    @autocommand()
    def test_prog(arg1, arg2: int, quiet=False, verbose=False):
        if not quiet:
            print(arg1, arg2)
            if verbose:
                print("LOUD NOISES")

        return 0

    print(test_prog(['-v', 'hello', '80']))
```

```
$ python test_prog.py
hello 80
LOUD NOISES
0
```

If the function is called with no arguments, `sys.argv[1:]` is used. This is to allow the autocommand function to be used as a setuptools entry point.

## Exceptions and limitations

- There are a few possible exceptions that `autocommand` can raise. All of them derive from `autocommand.AutocommandError`.

  - If an invalid annotation is given (that is, it isn't a `type`, `str`, `(type, str)`, or `(str, type)`, an `AnnotationError` is raised. The `type` may be any callable, as described in the `Types`_ section.
  - If the function has a `**kwargs` parameter, a `KWargError` is raised.
  - If, somehow, the function has a positional-only parameter, a `PositionalArgError` is raised. This means that the argument doesn't have a name, which is currently not possible with a plain `def` or `lambda`, though many built-in functions have this kind of parameter.

- There are a few argparse features that are not supported by autocommand.

  - It isn't possible to have an optional positional argument (as opposed to a `--option`). POSIX thinks this is bad form anyway.
  - It isn't possible to have mutually exclusive arguments or options
  - It isn't possible to have subcommands or subparsers, though I'm working on a few solutions involving classes or nested function definitions to allow this.

## Development

Autocommand cannot be important from the project root; this is to enforce separation of concerns and prevent accidental importing of `setup.py` or tests. To develop, install the project in editable mode:

```
$ python setup.py develop
```

This will create a link to the source files in the deployment directory, so that any source changes are reflected when it is imported.
