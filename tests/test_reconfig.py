from textwrap import dedent

import pytest
from reconfig import Config, ValidationError


def test_read_example_template_valid():
    cfg = Config.from_file("src/template.yaml")
    cfg["redash_key"] = "B9i5QnKSoU20SxQquVCXlcD8eHTOjcGaFs1IrWMV"
    cfg.validate()


def test_read_example_template():
    cfg = Config.from_file("src/template.yaml")
    with pytest.raises(ValidationError, match="missing value for: redash_key"):
        cfg.validate()


def test_zero_is_valid():
    cfg = Config.from_file("src/template.yaml")
    cfg["redash_key"] = "B9i5QnKSoU20SxQquVCXlcD8eHTOjcGaFs1IrWMV"
    cfg["render_delay"] = 0.0
    cfg.validate()


def test_render_delay_out_of_bounds():
    cfg = Config.from_file("src/template.yaml")
    cfg["redash_key"] = "B9i5QnKSoU20SxQquVCXlcD8eHTOjcGaFs1IrWMV"
    cfg["render_delay"] = 11
    with pytest.raises(ValidationError, match="'render_delay' must be a value between 0 and 10"):
        cfg.validate()


def test_validate_top_level_keys():
    raw_config = dedent(
        """
        redash_url: http://localhost:5003
        redash_key: B9i5QnKSoU20SxQquVCXlcD8eHTOjcGaFs1IrWMV
        sender: admin@redash.io
        #mailhost_url: http://localhost
        message_body: |
          Message attached
        reports: []
        """
    )
    cfg = Config(raw_config)
    with pytest.raises(ValidationError, match="missing key: mailhost_url"):
        cfg.validate()
