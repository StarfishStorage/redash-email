Redash Email Infrastructure
===========================

Save Redash dashboards as a PDF and send via e-mail.

Features:

* Map a set of reports to one or more recipients
* Distracting formatting is stripped out or replaced
* Dashboards regenerated for each parameter value
* Attach complete query results as a CSV file
* Save PDF and CSV results to a timestamped directory

Supported Protocols:

    smtp      Normal SMTP session.  Default port: 25
    smtp+tls  Normal SMTP session with STARTTLS.  Default port: 25
    smtps     SMTP session with forced TLS on connection.  Default port: 465

Requirements:

* Docker 1.13.1

Build Docker Image
------------------

A local caching proxy may be used to reduce latency

    make

Site Installation
-----------------

    IMAGE=redash-report:latest
    docker run -t $IMAGE template.yaml --print > user-report.yaml

Edit the configuration file and set the token for `redash_key`

    vi user-report.yaml

Verify communication with the Redash API

    docker run -v $PWD/user-report.yaml:/home/automation/report.yaml -t $IMAGE --dry-run --verbose

Save a copy of reports by mapping a path to `/var/reports` and launching with a
specified UID/GID

    docker run \
      --user $(id -u):$(id -g) \
      -v /var/reports:/home/automation/reports \
      -v /var/reports/user-report.yaml:/home/automation/report.yaml \
      -t $IMAGE --dry-run

Running Unit Tests
------------------

To run unit tests:

    python3 -m venv ~/.venv/redash-email
    source ~/.venv/redash-email/bin/activate
    pip install -r dev.txt
    npm install
    make tests

Running Integration Tests
-------------------------

Install prerequisites:

    apt-get install docker.io docker-buildx docker-compose-v2

To run the tests:

    make
    make up
    make integration-tests

Verify email body and attachments at `http://$(hostname -i):1080/`

Clean up:

    make down

Limitations
-----------

Dashboards are rendered by enabling a share link, but Redash does not allow
dashboards with Text parameters to be shared. All parameters must be a Text
Pattern, Number, Dropdown List, or Date.
