import email.utils
import os
import smtplib
import socket
from email import encoders
from email.charset import QP, Charset
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from urllib.parse import parse_qs, urlparse


class MailUtil:
    def __init__(self, mailhost, **kwargs):
        self.message = MIMEMultipart()
        self.host_url = urlparse(mailhost)
        self.headers = dict(Date=email.utils.formatdate(localtime=True))

        self.headers["Message-ID"] = email.utils.make_msgid(domain="redash.io")

        if "From" in kwargs and kwargs["From"] is not None:
            self.headers["From"] = kwargs["From"]
        else:
            user = os.getlogin()
            host = socket.getfqdn()
            self.headers["From"] = f"{user}@{host}"
        if "To" in kwargs:
            self.headers["To"] = kwargs["To"]
        if "Subject" in kwargs:
            self.headers["Subject"] = kwargs["Subject"]

        if self.host_url.scheme not in ("smtp", "smtp+tls", "smtps"):
            raise ValueError("Mailhost url scheme must be one of (smtp, smtp+tls, smtps)")

        self.port = self.host_url.port
        if not self.port:
            if self.host_url.scheme in ("smtp", "smtp+tls"):
                self.port = 25
            elif self.host_url.scheme == "smtps":
                self.port = 465

    def __repr__(self):
        return "host {} using {} port {}".format(
            self.host_url.hostname, self.host_url.scheme.upper(), self.port
        )

    def url_param(self, param, default):
        """Get a parameter from the query string"""

        params = parse_qs(self.host_url.query)
        if param in params:
            return params[param][0]
        return default

    def send_smtp(self):
        """Send mail using smtp, smtps, or smtp+tls"""

        for hdr in self.headers:
            self.message[hdr] = self.headers[hdr]

        if self.host_url.scheme == "smtps":
            server = smtplib.SMTP_SSL(self.host_url.hostname, self.port)
        else:
            server = smtplib.SMTP(self.host_url.hostname, self.port)

        if self.host_url.scheme == "smtp+tls":
            server.starttls()

        password = self.url_param("password", self.host_url.password)
        username = self.url_param("username", self.host_url.username)
        if username:
            server.login(username, password)

        server.sendmail(
            self.headers["From"],
            self.headers["To"].split(","),
            self.message.as_string(),
        )
        server.quit()

    def attach(self, filename, mimetype="application/octet-stream", stream=None):
        """Add an attachment to the email, application/octet-stream"""

        first, second = mimetype.split("/")

        if stream:
            part = MIMEBase(first, second)
            part.set_payload(stream)
        else:
            # Open file in binary mode
            with open(filename, "rb") as attachment:
                # Add file as e.g. application/octet-stream
                # Email client can usually download this automatically as attachment
                part = MIMEBase(first, second)
                part.set_payload(attachment.read())

        # Encode file in ASCII characters to send by email
        encoders.encode_base64(part)

        # Add header as key/value pair to attachment part
        part.add_header(
            "Content-Disposition",
            f'attachment; filename="{filename}"',
        )
        self.message.attach(part)

    def set_body(self, bodytext, msgtype="plain"):
        """Set the message body text"""
        # Use Quoted Printable for body (default is binhex64)
        charset = Charset("utf-8")
        charset.header_encoding = QP
        charset.body_encoding = QP

        self.message.attach(MIMEText(bodytext, msgtype, _charset=charset))

    def set_header(self, header, value):
        """set a message header property"""
        self.headers[header] = value

    def set_headers(self, **kwargs):
        """Set multiple headers at once"""
        for hkey, hvalue in kwargs.items():
            self.set_header(hkey, hvalue)
