import yaml, os, jinja2, fsspec
from urllib.parse import urlparse
import yaml_include
from typing import Any

def load(filename: str) -> dict[str, Any]:
    with fsspec.open(filename, "r") as f:
        pr = urlparse(filename)
        base_dir = pr.netloc + os.path.dirname(pr.path)
        yaml.add_constructor("!include", yaml_include.Constructor(base_dir=base_dir,
                                                                  fs=fsspec.core.url_to_fs(filename)[0]))
        y = yaml.load(f, Loader=yaml.FullLoader)
        s = yaml.dump(y)
        template = jinja2.Template(s)
        rendered = template.render(**dict(os.environ))
        config = yaml.load(rendered, Loader=yaml.FullLoader)
        return config

