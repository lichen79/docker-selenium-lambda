FROM public.ecr.aws/lambda/python@sha256:e1948dc355b1d65f11ffe48d15c46b4e4aad0ea77851b63914f67bcaa678567f as build
RUN yum install -y unzip && \
    curl -Lo "/tmp/chromedriver.zip" "https://chromedriver.storage.googleapis.com/109.0.5414.74/chromedriver_linux64.zip" && \
    curl -Lo "/tmp/chrome-linux.zip" "https://www.googleapis.com/download/storage/v1/b/chromium-browser-snapshots/o/Linux_x64%2F1070081%2Fchrome-linux.zip?alt=media" && \
    unzip /tmp/chromedriver.zip -d /opt/ && \
    unzip /tmp/chrome-linux.zip -d /opt/

FROM public.ecr.aws/lambda/python@sha256:e1948dc355b1d65f11ffe48d15c46b4e4aad0ea77851b63914f67bcaa678567f
RUN yum install atk cups-libs gtk3 libXcomposite alsa-lib \
    libXcursor libXdamage libXext libXi libXrandr libXScrnSaver \
    libXtst pango at-spi2-atk libXt xorg-x11-server-Xvfb \
    xorg-x11-xauth dbus-glib dbus-glib-devel -y

 
RUN yum -y install python-requests
RUN pip install requests
#ENV LANG=zh_CN.UFT-8
ENV LANG=en_US.UFT-8 
RUN yum -y install yum-utils
RUN yum -y install https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm

RUN yum-config-manager –enable epel
RUN yum -y install kde-l10n-Chinese
RUN yum -y reinstall glibc-common
   && yum clean all



RUN pip install selenium


COPY --from=build /opt/chrome-linux /opt/chrome
COPY --from=build /opt/chromedriver /opt/
COPY main.py ./
CMD [ "main.handler" ]
