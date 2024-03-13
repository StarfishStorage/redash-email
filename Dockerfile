FROM rockylinux:8

RUN dnf -y install python38 python38-yaml python38-jinja2 python38-requests

RUN rpm --import https://dl.google.com/linux/linux_signing_key.pub
RUN dnf install https://dl.google.com/linux/direct/google-chrome-stable_current_x86_64.rpm -y

RUN dnf -y module install nodejs:18

RUN groupadd -r automation
RUN useradd -m -r -g automation -G audio,video automation

USER automation

WORKDIR /home/automation
RUN npm -d install puppeteer@22.4.1

COPY --chown=automation:automation src/* /home/automation/

ENTRYPOINT ["/home/automation/send-report.py"]
