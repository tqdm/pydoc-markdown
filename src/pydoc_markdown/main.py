# -*- coding: utf8 -*-
# Copyright (c) 2019 Niklas Rosenstein
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.

"""
Implements the pydoc-markdown CLI.
"""

from pydoc_markdown import PydocMarkdown
from pydoc_markdown.contrib.loaders.python import PythonLoader
from pydoc_markdown.contrib.renderers.markdown import MarkdownRenderer
from pydoc_markdown.contrib.renderers.mkdocs import MkdocsRenderer
import click
import logging
import os
import sys
import yaml

config_filenames = [
  'pydoc-markdown.yml',
  'pydoc-markdown.yaml',
]

DEFAULT_CONFIG_NOTICE = 'Using this option will disable loading the '\
  'default configuration file.'


def error(*args):
  print('error:', *args, file=sys.stderr)
  sys.exit(1)


@click.command()
@click.argument('config', required=False)
@click.option('--verbose', '-v',
  is_flag=True,
  help='Increase log verbosity.')
@click.option('--quiet', '-q',
  is_flag=True,
  help='Decrease the log verbosity.')
@click.option('--module', '-m', 'modules', metavar='MODULE',
  multiple=True,
  help='The module to parse and generated API documentation for. Can be '
       'specified multiple times. ' + DEFAULT_CONFIG_NOTICE)
@click.option('--search-path', '-I', metavar='PATH',
  multiple=True,
  help='A directory to use in the search for Python modules. Can be '
       'specified multiple times. ' + DEFAULT_CONFIG_NOTICE)
@click.option('--py2/--py3', 'py2', default=None,
  help='Switch between parsing Python 2 and Python 3 code. The default '
       'is Python 3. Using --py2 will enable parsing code that uses the '
       '"print" statement. This is equivalent of setting the print_function '
       'option of the "python" loader to False. ' + DEFAULT_CONFIG_NOTICE)
@click.option('--render-toc/--no-render-toc',
  default=None,
  help='Enable/disable the rendering of the TOC in the "markdown" renderer.')
def cli(config, verbose, quiet, modules, search_path, render_toc, py2):
  """ Pydoc-Markdown is a renderer for Python API documentation in Markdown
  format.

  With no arguments it will load the default configuration file. If the
  *config* argument is specified, it must be the name of a configuration file
  or a YAML formatted object for the configuration. """

  load_implicit_config = not any((modules, search_path, py2 is not None))

  # Initialize logging.
  if verbose is not None:
    if verbose:
      level = logging.INFO
    elif quiet:
      level = logging.ERROR
    else:
      level = logging.WARNING
    logging.basicConfig(format='%(message)s', level=level)

  # Load the configuration.
  if config and (config.lstrip().startswith('{') or '\n' in config):
    config = yaml.safe_load(config)
  if config is None and load_implicit_config:
    try:
      config = next((x for x in config_filenames if os.path.exists(x)))
    except StopIteration:
      error('config file not found.')

  pydocmd = PydocMarkdown()
  if config:
    pydocmd.load_config(config)

  # Update configuration per command-line options.
  if modules or search_path or py2 is not None:
    loader = next(
      (l for l in pydocmd.loaders if isinstance(l, PythonLoader)), None)
    if not loader:
      error('no python loader found')
    if modules:
      loader.modules = modules
    if search_path:
      loader.search_path = search_path
    if py2 is not None:
      loader.print_function = not py2
  if render_toc is not None:
    if isinstance(pydocmd.renderer, MkdocsRenderer):
      markdown = pydocmd.renderer.markdown
    elif isinstance(pydocmd.renderer, MarkdownRenderer):
      markdown = pydocmd.renderer
    else:
      error('no markdown renderer found')
    if render_toc is not None:
      markdown.render_toc = render_toc

  pydocmd.load_modules()
  pydocmd.process()
  pydocmd.render()


if __name__ == '__main__':
  cli()  # pylint: disable=no-value-for-parameter
