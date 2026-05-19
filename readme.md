# ModYaml

ModYaml is a Python module designed for advanced YAML configuration management, offering modular, flexible, and powerful configuration capabilities.

## Purpose

The primary purpose of ModYaml is to enhance YAML configurations by providing:

1. Modular configuration through file inclusion
2. Support for various file sources (local, remote, cloud storage)
3. Environment variable interpolation
4. Jinja2 templating support
5. Ability to disable interpolation for specific values or blocks

These features allow for more dynamic, reusable, and environment-aware configurations.

## Syntax

ModYaml extends standard YAML syntax with the following directives:

### File Inclusion

```yaml
key: !include path/to/another/file.yaml
```

The path/to/another/file.yaml can be:
A local file path
A URL (http, https, ftp, etc.)
A cloud storage path (s3://, gs://, etc.)


ModYaml uses fsspec (Filesystem Specification) to handle file access, supporting a wide range of file systems and protocols.

```yaml
database:
  !include configs/database.yaml
logging:
  !include https://example.com/logging-config.yaml
cloud_settings:
  !include gs://my-bucket/cloud-config.yaml
```

### Disabling Interpolation

ModYaml provides two ways to disable interpolation when needed:

1. For single values using the `!raw` tag:

```yaml
# This value will not be interpolated
config_string: !raw "{{ VARIABLE }}"
```

2. For blocks of text using Jinja2's `{% raw %}` and `{% endraw %}` tags:

```yaml
text_block: >
  {% raw %}
  This entire block will not have {{ any }} variables 
  {{ interpolated }} even though they use the
  standard {{ SYNTAX }}.
  {% endraw %}
```

## Processing Stages
ModYaml processes your configuration in the following stages:

1. File Loading: The main YAML file is loaded, and all !include directives are resolved recursively.
1. YAML Parsing: The complete YAML structure (including included files) is parsed into a Python dictionary.
1. Jinja2 Templating: The parsed YAML is rendered as a Jinja2 template, allowing for dynamic content generation.
   * During this stage, content marked with `!raw` or inside `{% raw %}{% endraw %}` blocks will not be interpolated.
1. Environment Variable Interpolation: Environment variables are interpolated into the configuration.
1. Final Parsing: The resulting string is parsed again as YAML to produce the final configuration dictionary.

## Using Environment Variables
Environment variables can be used in your YAML files for flexible configuration and debugging. They are accessible in the Jinja2 templating stage.

Example:
```yaml
debug_mode: {{ DEBUG | default('false') }}
database_url: {{ DB_URL | default('localhost:5432') }}
# This will preserve the literal text "{{ ENV_VAR }}" without interpolation
raw_value: !raw "{{ ENV_VAR }}"
```

## Command-line interface

ModYaml ships a small CLI for use in build pipelines. The current command
is `flatten`, which resolves `!include` directives into a single
self-contained YAML document while **preserving jinja-style placeholders
(`{{ VAR }}`) as plain strings**. This is the right thing for build-time
artifact generation: the resulting file can be safely published and then
rendered at runtime by `modyaml.load()` inside the target environment,
where the real env vars live.

### Install

`modyaml` exposes a console-script entry point, so it works with `pipx`:

```shell
# Run without installing (recommended for CI):
pipx run modyaml flatten config.yml -o config.flattened.yml

# Or install once and call directly:
pipx install modyaml
modyaml flatten config.yml -o config.flattened.yml
```

Plain `pip install modyaml` also works and gives you the same `modyaml`
executable on `$PATH`.

### Usage

```shell
# Write flattened YAML to a file:
modyaml flatten config.yml -o config.flattened.yml

# Write to stdout (default when -o is omitted):
modyaml flatten config.yml > config.flattened.yml

# Or be explicit about stdout:
modyaml flatten config.yml -o -
```

`<input>` may be any path or URL that `fsspec` understands, the same as
`!include` itself (local path, `s3://`, `gs://`, `http(s)://`, ...).

### What `flatten` does (and does not) do

| Directive / construct       | `flatten` behaviour                                |
| --------------------------- | -------------------------------------------------- |
| `!include path/to/file.yml` | Inlined recursively at flatten time                |
| `{{ VAR }}`                 | **Preserved verbatim** as a string                 |
| `!raw "..."`                | Converted to a plain string (the marker is no longer needed because flatten never renders jinja) |
| `{% raw %}...{% endraw %}`  | Preserved as part of the surrounding string       |

For full processing (includes + jinja + env vars) use `modyaml.load()`
from Python, which is unchanged.

### Python API

The same behaviour is available programmatically:

```python
import modyaml
import yaml

data = modyaml.flatten('config.yml')          # !include resolved, jinja kept
with open('config.flattened.yml', 'w') as f:
    yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)
```

## Debugging configs

It is possible to trigger the config flow processing debug to standard logger.
In order to do this, the following environment variables can be used:

```shell
export MODYAML_LOG_LEVEL=DEBUG
```
 