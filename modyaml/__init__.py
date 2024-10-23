import yaml, os, jinja2, fsspec
from urllib.parse import urlparse
import yaml_include
from typing import Any
import logging, os

def load(filename: str) -> dict[str, Any]:
    logger = logging.getLogger(__name__)
    with fsspec.open(filename, "r") as f:
        pr = urlparse(filename)
        base_dir = pr.netloc + os.path.dirname(pr.path)
        yaml.add_constructor("!include", yaml_include.Constructor(base_dir=base_dir,
                                                                  fs=fsspec.core.url_to_fs(filename)[0]))
        y = yaml.load(f, Loader=yaml.FullLoader)
        s = yaml.dump(y)
        if os.getenv('MODYAML_DEBUG_STAGE_1'):
            logger.debug(f"Stage 1: Raw YAML:\n{s}")
        template = jinja2.Template(s)
        rendered = template.render(**dict(os.environ))
        if os.getenv('MODYAML_DEBUG_STAGE_2'):
            logger.debug(f"Stage 2: Rendered YAML:\n{rendered}")
        config = yaml.load(rendered, Loader=yaml.FullLoader)
        if os.getenv('MODYAML_DEBUG_STAGE_3'):
            logger.debug(f"Stage 3: Parsed YAML:\n{config}")
        return config

