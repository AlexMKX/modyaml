import logging
import os
from typing import Any
from urllib.parse import urlparse

import fsspec
import jinja2
import yaml
import yaml_include


def load(filename: str) -> dict[str, Any]:
    logger = logging.getLogger(__name__)
    log_level = os.environ.get('MODYAML_LOG_LEVEL')
    if log_level:
        logger.setLevel(log_level)
    with fsspec.open(filename, "r") as f:
        pr = urlparse(filename)
        base_dir = pr.netloc + os.path.dirname(pr.path)
        yaml.add_constructor("!include", yaml_include.Constructor(base_dir=base_dir,
                                                                  fs=fsspec.core.url_to_fs(filename)[0]))
        y = yaml.load(f, Loader=yaml.FullLoader)
        s = yaml.dump(y)
        logger.debug(f"Stage 1: Raw YAML:\n{s}")
        template = jinja2.Template(s)
        rendered = template.render(**dict(os.environ))
        logger.debug(f"Stage 2: Rendered YAML:\n{rendered}")
        config = yaml.load(rendered, Loader=yaml.FullLoader)
        logger.debug(f"Stage 3: Parsed YAML:\n{config}")
        return config
