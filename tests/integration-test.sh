#!/bin/bash

log() {
	if [ -t 1 ]; then
		printf "\e[7m>> $*\e[27m\n"
	else
		printf ">> $*\n"
	fi
}

trap 'printf "$0: exit code $? on line $LINENO\n" >&2; exit 1' ERR
trap 'rm -f $yaml_config' EXIT

image=redash-email
yaml_config=/tmp/user-report.yaml
redash_api_key=$(docker compose exec postgres psql -At -U postgres -c "SELECT api_key FROM users WHERE email='redash@redash.io'")
mailto="${USER}@localhost"

log "Generate config"
cat <<YAML > $yaml_config
redash_url: http://server:5000
redash_key: ${redash_api_key}
sender: Redash <admin@redash.io>
mailhost_url: smtp://email:1025
render_delay: 0
message_body: |
  Attached is a PDF of the report.

  View full report:
  {{dashboard_url}}
  {{dashboard_public_url}}

reports:
  - dashboard: "Test Dashboard"
    recipients:
      - ${mailto}
    parameters:
      is_archived:
        - "true"
        - "false"
    attachments:
      - query: "Query Summary"
        extra_parameters:
          num_results: 10
YAML

log "Execute in container"
docker run --network redash-email -v $yaml_config:/home/automation/report.yaml -t $image "$@"

log "Integration test PASSED"
