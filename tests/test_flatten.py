#!/usr/bin/env python
"""Tests for `modyaml.flatten` and the `modyaml flatten` CLI subcommand.

The flatten path is build-time-only: it must resolve `!include` recursively
while leaving jinja-style placeholders untouched so that real env-vars are
substituted later at runtime by `modyaml.load()`.
"""
import io
import os
import sys
import unittest
from contextlib import redirect_stdout

import yaml

# Make local source importable without installation.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import modyaml
from modyaml import cli as modyaml_cli


TEST_FILE = os.path.join(os.path.dirname(__file__), 'test_raw.yaml')


class TestFlattenAPI(unittest.TestCase):
    """`modyaml.flatten(...)` returns a plain dict with !include resolved."""

    def test_returns_dict(self):
        """Flatten must return a mapping at the top level."""
        result = modyaml.flatten(TEST_FILE)
        self.assertIsInstance(result, dict)

    def test_include_is_inlined(self):
        """Content of included.yaml must appear under `included` key."""
        result = modyaml.flatten(TEST_FILE)
        self.assertIn('included', result)
        included = result['included']
        # Keys from included.yaml.
        self.assertIn('value1', included)
        self.assertIn('raw_value', included)
        # Nested include resolved too.
        self.assertIn('nested_include', included)
        self.assertIn('simple_value', included['nested_include'])

    def test_jinja_placeholders_preserved(self):
        """Jinja-style `{{ VAR }}` must survive flatten as plain strings."""
        # Set env vars that *would* be interpolated by `load()` so we can
        # prove flatten is independent of the environment.
        os.environ['TEST_VAR'] = 'this_should_not_appear'
        try:
            result = modyaml.flatten(TEST_FILE)
            self.assertEqual(result['regular_interpolation'], '{{ TEST_VAR }}')
            self.assertEqual(result['nested']['interpolated'], '{{ TEST_VAR }}')
            self.assertIn('{{ TEST_VAR }}', result['included']['value1'])
            self.assertEqual(
                result['included']['nested_include']['simple_value'],
                'Простое значение {{ TEST_VAR }}',
            )
        finally:
            os.environ.pop('TEST_VAR', None)

    def test_raw_tag_becomes_plain_string(self):
        """`!raw`-tagged scalars must end up as plain strings in the output.

        `!raw` exists to protect a string from jinja rendering. Since flatten
        does not render jinja at all, the marker is redundant and we drop it
        to keep the output cleanly round-trippable through `yaml.safe_dump`.
        """
        result = modyaml.flatten(TEST_FILE)
        self.assertIsInstance(result['raw_content'], str)
        self.assertEqual(result['raw_content'], '{{ TEST_VAR }}')

    def test_output_is_safe_dumpable(self):
        """Flatten output must round-trip through `yaml.safe_dump`.

        This is the property that lets us publish the result as a CI artifact.
        """
        result = modyaml.flatten(TEST_FILE)
        dumped = yaml.safe_dump(result, sort_keys=False, allow_unicode=True)
        reloaded = yaml.safe_load(dumped)
        self.assertEqual(reloaded, result)
        # And jinja templates must survive the round-trip.
        self.assertIn('{{ TEST_VAR }}', dumped)


class TestFlattenCLI(unittest.TestCase):
    """`modyaml flatten <input>` writes the flattened YAML to stdout or `-o`."""

    def test_cli_stdout(self):
        """Without `-o`, CLI writes flattened YAML to stdout and exits 0."""
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = modyaml_cli.main(['flatten', TEST_FILE])
        self.assertEqual(rc, 0)
        out = buf.getvalue()
        # Output is valid YAML containing inlined includes + preserved jinja.
        parsed = yaml.safe_load(out)
        self.assertIn('included', parsed)
        self.assertIn('{{ TEST_VAR }}', out)

    def test_cli_output_file(self, tmp_path=None):
        """With `-o <path>`, CLI writes the same YAML into the file."""
        import tempfile
        with tempfile.NamedTemporaryFile('w+', suffix='.yml', delete=False) as f:
            out_path = f.name
        try:
            rc = modyaml_cli.main(['flatten', TEST_FILE, '-o', out_path])
            self.assertEqual(rc, 0)
            with open(out_path) as f:
                parsed = yaml.safe_load(f)
            self.assertIn('included', parsed)
        finally:
            os.unlink(out_path)

    def test_cli_dash_means_stdout(self):
        """`-o -` is an explicit way to ask for stdout."""
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = modyaml_cli.main(['flatten', TEST_FILE, '-o', '-'])
        self.assertEqual(rc, 0)
        self.assertTrue(buf.getvalue().strip())


if __name__ == '__main__':
    unittest.main()
