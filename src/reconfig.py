import yaml


class ValidationError(Exception):
    pass


class Config(dict):
    def __init__(self, yaml_src):
        super().__init__(self)
        self.yaml_src = yaml_src
        self.update(yaml.safe_load(yaml_src))

        if "render_delay" not in self:
            self["render_delay"] = 0.5

    @classmethod
    def from_file(cls, fn):
        return cls(open(fn, "r", encoding="utf-8").read())

    def __repr__(self):
        return self.yaml_src

    def validate(self):
        # required top-level keys
        for key in [
            "mailhost_url",
            "message_body",
            "redash_key",
            "redash_url",
            "render_delay",
            "reports",
            "sender",
        ]:
            if key not in self:
                raise ValidationError(f"missing key: {key}")
            if self[key] is None or self[key] == "":
                raise ValidationError(f"missing value for: {key}")

        if not isinstance(self["reports"], list):
            raise ValidationError("'reports' key must be a list")

        if self["render_delay"] < 0 or self["render_delay"] > 10:
            raise ValidationError("'render_delay' must be a value between 0 and 10")
