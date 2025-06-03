# Configuration Notes

- [Configuration Notes](#configuration-notes)
  - [Configuration Priority Logic](#configuration-priority-logic)
  - [How to add a new configuration?](#how-to-add-a-new-configuration)


## Configuration Priority Logic

Each configuration follows the following priority:

1. CLI args

- if a value is given, e.g. `--udp host:port`, then it will be used
- if the value `host:port` is omitted, e.g. `--udp`, it will use the config inside the YAML file regardless whether it has `enabled: false`. If the YAML config is not set then the default value will be used (defined in the config files and also shows in `-h` option)

2. YAML configs

Depending on which configuration (i.e. udp, mqtt, rest), it follows:

- YAML config with `enabled: true`
- YAML config with `enabled: false`
- If `enabled` is not defined then it defaults to `false` (which can be enabled through CLI, e.g. `--udp` **without** specifying `host:port`)

3. None set

If neither CLI arguments nor YAML configs are set, then they are considered as "not set" or `None`.

**TL:DR; CLI args -> YAML -> None**

## How to add a new configuration?

1. Edit config.yaml to add the new config
2. Edit config/cli.py to add the new config (if wanted to have this in CLI as well):

- Modify the Args class
- Add new parser argument

3. Edit `config/app.py` to add the new config:

- Modify AppConfig
- (If needed,) create a new module named `XXXConfig`
  - Export new module in `config/__init__.py`
- Create its builder helper function and use in AppConfig's initialization