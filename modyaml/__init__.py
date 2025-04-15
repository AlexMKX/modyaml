import logging
import os
from typing import Any, Dict, Union
from urllib.parse import urlparse
from pprint import pformat

try:
    import yaml
    import jinja2
    import yaml_include
    import fsspec
except ImportError:
    raise ImportError("Required packages not found. Please install: pyyaml jinja2 yaml-include fsspec")


class RawString:
    """Class for storing raw strings that should not be interpolated."""
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return str(self.value)


def raw_constructor(loader, node):
    """Constructor for the !raw tag."""
    return RawString(loader.construct_scalar(node))


def process_templates(obj: Union[Dict, list, str, RawString, Any], env: jinja2.Environment, context: dict) -> Union[Dict, list, str, Any]:
    """Recursively process templates in the data structure, skipping RawString instances.
    
    Args:
        obj: The object to process (can be dict, list, str, RawString, or any other type)
        env: Jinja2 environment for template processing
        context: Dictionary with variables for template rendering
        
    Returns:
        Processed object with templates rendered (except for RawString values)
    """
    if isinstance(obj, dict):
        return {key: process_templates(value, env, context) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [process_templates(item, env, context) for item in obj]
    elif isinstance(obj, str):
        template = env.from_string(obj)
        return template.render(**context)
    elif isinstance(obj, RawString):
        return str(obj)
    return obj


def load(filename: str) -> Dict[str, Any]:
    """
    Load a YAML file with support for !raw tag and {% raw %} {% endraw %} blocks.
    
    This function handles:
    - Regular variable interpolation using Jinja2
    - Raw values marked with !raw tag (no interpolation)
    - File includes with !include tag
    - Raw blocks using {% raw %} {% endraw %}
    
    Args:
        filename: Path to the YAML file
        
    Returns:
        Dict[str, Any]: Processed dictionary with YAML contents
        
    Raises:
        ValueError: If the YAML root is not a dictionary
    """
    logger = logging.getLogger(__name__)
    log_level = os.environ.get('MODYAML_LOG_LEVEL')
    if log_level:
        logger.setLevel(log_level)
    
    # Step 1: Configure YAML for file includes and raw tags
    pr = urlparse(filename)
    base_dir = pr.netloc + os.path.dirname(pr.path)
    yaml.add_constructor("!include", yaml_include.Constructor(base_dir=base_dir,
                                                            fs=fsspec.core.url_to_fs(filename)[0]))
    yaml.add_constructor("!raw", raw_constructor)
    
    # Step 2: Open and read the file
    with fsspec.open(filename, "r") as f:
        content = f.read()
    
    # Step 3: Load YAML (before template processing)
    config = yaml.full_load(content)
    if not isinstance(config, dict):
        raise ValueError("YAML file must contain a dictionary at the root level")
    
    # Step 4: Configure Jinja2
    env = jinja2.Environment(
        keep_trailing_newline=True,
        autoescape=False
    )
    
    # Step 5: Process templates, skipping raw values
    config = process_templates(config, env, dict(os.environ))
    if not isinstance(config, dict):
        raise ValueError("After processing templates, the result must be a dictionary")
    
    formatted_config = pformat(config, compact=True)
    logger.debug(f"Stage 2: Parsed YAML:\n{formatted_config}")
    return config
