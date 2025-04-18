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

## Debugging configs

It is possible to trigger the config flow processing debug to standard logger.
In order to do this, the following environment variables can be used:

```shell
export MODYAML_LOG_LEVEL=DEBUG
```
 