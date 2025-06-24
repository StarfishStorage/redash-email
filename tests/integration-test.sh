#!/bin/bash

log() {
	if [ -t 1 ]; then
		printf "\e[7m>> $*\e[27m\n"
	else
		printf ">> $*\n"
	fi
}

tmpdir=$(mktemp -d /tmp/redash-email-test.XXXXX)
trap 'printf "$0: exit code $? on line $LINENO\n" >&2; exit 1' ERR
trap 'rm -rf $tmpdir' EXIT

image=redash-email
yaml_config=$tmpdir/user-report.yaml
out=$tmpdir/send-report.out
redash_api_key=$(docker compose exec postgres psql -At -U postgres -c "SELECT api_key FROM users WHERE email='redash@redash.io'")
mailto="${USER}@localhost"

log "Send PDF for two parameters and attach query"
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
docker run --network redash-email \
    --user $(id -u):$(id -g) \
    -v $yaml_config:/home/automation/report.yaml \
    -t $image --verbose | tee $out
egrep -q "node save-report.js --url http://server:5000/public/dashboards/.{40} --output 'reports/.{16}/Test Dashboard - true.pdf' --param is_archived=true" $out
egrep -q "curl -sS -k -o 'reports/.{16}/Query Summary - true.csv' 'http://server:5000/api/query_results/[0-9]+.csv\?api_key=.{40}'" $out
grep -q "Connect to host email using SMTP port 1025" $out

log "Raise error if parameter is not found"
cat <<YAML > $yaml_config
redash_url: http://server:5000
redash_key: ${redash_api_key}
sender: Redash <admin@redash.io>
mailhost_url: smtp://email:1025
message_body: |
  Attached is a PDF of the report.

reports:
  - dashboard: "Test Dashboard"
    recipients:
      - ${mailto}
    parameters:
      username:
        - "root"
YAML
docker run --network redash-email \
    --user $(id -u):$(id -g) \
    -v $yaml_config:/home/automation/report.yaml \
    -t $image | cat > $out
grep -q "no match found for parameter" $out || { cat $out; exit 1; }

log "Integration test PASSED"
