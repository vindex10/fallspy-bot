import dataclasses
import os
import json
try:
    import yaml
except ImportError:
    pass


@dataclasses.dataclass
class Config:
    bot_token: dict

def read_cfg():
    cfg = {}
    files = ["config.json", "config.yaml", "config.yml"]
    if file_cfg := os.environ.get("CFG_FILE"):
        files.append(file_cfg)
    for fpath in files:
        if not os.path.exists(fpath):
            continue
        cfg.update(read_structured_file(fpath))
    if env_cfg := os.environ.get("CFG"):
        cfg.update(json.loads(env_cfg))
    return Config(**cfg)


def read_structured_file(fname):
    if fname.endswith(".json"):
        with open(fname, "r", encoding="utf-8") as fin:
            return json.load(fin)
    if fname.endswith(".yaml") or fname.endswith(".yml"):
        with open(fname, "r", encoding="utf-8") as fin:
            return yaml.safe_load(fin)
    raise ValueError("Unknown file format.")


CFG: Config = read_cfg()
