"""Command-line interface for modyaml.

Currently exposes the `flatten` subcommand, which resolves `!include` directives
into a single self-contained YAML document while preserving jinja-style
placeholders (`{{ VAR }}`) verbatim. The intended use case is build-time
artifact generation: a CI job flattens a multi-file schema repo into one YAML
that is later rendered at runtime by `modyaml.load()` inside the target
environment.
"""
from __future__ import annotations

import argparse
import sys
from typing import List, Optional

import yaml

from . import flatten as flatten_yaml


def _cmd_flatten(args: argparse.Namespace) -> int:
    """Implement `modyaml flatten <input> [-o <output>]`."""
    data = flatten_yaml(args.input)
    dumped = yaml.safe_dump(
        data,
        default_flow_style=False,
        sort_keys=False,
        allow_unicode=True,
    )
    if args.output == "-" or args.output is None:
        sys.stdout.write(dumped)
    else:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(dumped)
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Construct the top-level argument parser.

    Exposed as a function so tests can introspect the CLI surface without
    invoking `main()`.
    """
    parser = argparse.ArgumentParser(
        prog="modyaml",
        description="Modular YAML: includes, jinja, raw tags.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    flatten_p = subparsers.add_parser(
        "flatten",
        help="Resolve !include directives, keep jinja templates as strings.",
        description=(
            "Inline every `!include` recursively starting from <input> and emit a "
            "single YAML document. Jinja placeholders like `{{ VAR }}` are NOT "
            "rendered (they remain as-is in the output) so that the resulting "
            "artifact can be safely shipped without leaking environment-specific "
            "values. Use `modyaml.load()` at runtime to render those placeholders."
        ),
    )
    flatten_p.add_argument(
        "input",
        help="Path or fsspec URL to the root YAML file.",
    )
    flatten_p.add_argument(
        "-o", "--output",
        default=None,
        help="Output file path. Use '-' or omit for stdout.",
    )
    flatten_p.set_defaults(func=_cmd_flatten)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """CLI entry point. Returns process exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
