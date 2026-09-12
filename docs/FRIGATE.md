# Frigate patch workflow

Frigate does not use Home Assistant-style YAML includes. The generator creates
`frigate/arlo-frigate.patch.yaml` and, when `--frigate-base` is given, also
creates a deployable merged `frigate/config.yml`.

Mappings merge recursively; scalars and lists replace the base value; generated
Arlo camera IDs replace only those camera definitions. Non-Arlo cameras in the
private base config remain unchanged.

Generated Arlo cameras start with `enabled: false`, read the MediaMTX restream,
and use detect/record roles. Validate the merged config before deployment. Do
not hand-edit generated files; change inventory or the private base and rerun.
