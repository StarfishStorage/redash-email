FROM node:20-bookworm

RUN apt-get -y update
RUN apt-get -y install python3-requests python3-yaml python3-jinja2
RUN apt-get -y install chromium

RUN groupadd -r automation
RUN useradd -m -r -g automation -G audio,video automation

USER automation

WORKDIR /home/automation
ENV PUPPETEER_CACHE_DIR="/home/automation"
ENV NODE_PATH="/home/automation/node_modules"
RUN npm -d install puppeteer@24.10.2

COPY --chown=automation:automation src/* /home/automation/
RUN install -d -m 1777 -o automation -g automation /home/automation/reports

ENV XDG_CONFIG_HOME=/tmp/.chromium
ENV XDG_CACHE_HOME=/tmp/.chromium

ENTRYPOINT ["/home/automation/send-report.py"]
