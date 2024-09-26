import pytest
from mailutil import MailUtil


def test_mail_server_specification():
    for smtp_url in [
        "smtp://localhost:25",
        "smtp+tls://user:pass@localhost:587",
        "smtp+tls://relay.my.domain?username=user&password=pass",
        "smtps://user:pass@relay.my.domain",
    ]:
        MailUtil(
            smtp_url,
            From="noreply@redash.io",
            To="admin@redash.io",
            Subject="Report",
        )


def test_mail_server_repr():
    smtp_url = "smtp://localhost"
    sm = MailUtil(
        smtp_url,
        From="noreply@redash.io",
        To="admin@redash.io",
        Subject="Report",
    )
    assert str(sm) == "host localhost using SMTP port 25"


def test_mail_server_specification_invalid():
    with pytest.raises(ValueError, match="Mailhost url scheme must be one of"):
        MailUtil(
            "lmtp://localhost:24",
            From="noreply@redash.io",
            To="admin@redash.io",
            Subject="Report",
        )
