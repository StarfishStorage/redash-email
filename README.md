Redash Email Infrastructure
===========================

Save Redash dashboards as a PDF and send via e-mail.

Features:

* Map a set of reports to one or more recipients
* Distracting formatting is stripped out or replaced
* Dashboards regenerated for each parameter value
* Attach complete query results as a CSV file

Supported Protocols:

    smtp      Normal SMTP session.  Default port: 25
    smtp+tls  Normal SMTP session with STARTTLS.  Default port: 25
    smtps     SMTP session with forced TLS on connection.  Default port: 465

Requirements:

* Docker 1.13.1

Build Docker Image
------------------

A local caching proxy may be used to reduce latency

    make image

Site Installation
-----------------

    IMAGE=redash-report:latest
    docker run -t $IMAGE template.yaml --print > user-report.yaml

Edit the configuration file and set the token for `redash_key`

    vi user-report.yaml

Verify communication with the Redash API

    docker run -v $PWD/user-report.yaml:/home/automation/report.yaml -t $IMAGE --dry-run --verbose

Running Unit Tests
------------------

    python3 -m venv ~/redashvenv1
    source ~/redashvenv1/bin/activate
    pip install pytest pyyaml requests ruff
    npm install
    make check

Running System Test
-------------------

Install prerequisites:

    apt-get install pwgen docker.io docker-buildx docker-compose-v2

To run the tests:

    make image
    make up
    make test

Verify email body and attachments at `http://$(hostname -i):1080/`

Clean up:

    make down

Limitations
-----------

Dashboards are rendered by enabling a share link, but Redash does not allow
dashboards with text parameters to be shared. Hence all parameters must be a
dropdown list, number or date.
