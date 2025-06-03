# Configuration Notes

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
