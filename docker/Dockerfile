FROM centos:7
# Set workdir to /tmp
WORKDIR /tmp/
# Set locale
RUN localedef -i fr_FR -f UTF-8 fr_FR.UTF-8
# Activate EPL
RUN yum install -y epel-release
# Fix set locale hack
RUN sed 's/^override_install_langs/#override_install_langs/' -i /etc/yum.conf
RUN yum -y -q install glibc-common
ENV LANG=fr_FR.UTF8
# Install some base packages
RUN yum install -y \
    bash \
    htop \
    locate \
    unzip \
    vim \
    postfix cyrus-sasl-plain \
    wget \
    gcc gcc-c++ make openssl-devel cmake unzip \
    libxml2 libxml2-devel libxslt libxslt-devel \
    gettext \
    git \
    glib  glib-devel \
    glib2 glib2-devel \
    libjpeg-devel \
    libffi-devel \
    libwebp libwebp-devel \
    file-devel \
    kernel-devel \
    nodejs npm \
    openssl \
    pygobject3 \
    python python-devel \
    xz \
    zlib-devel \
    openssh-clients \
    ImageMagick \
    --enablerepo=epel ; yum clean all
# Set timezone
RUN ln -snf /usr/share/zoneinfo/Europe/Paris /etc/localtime
# Install gulp and less
RUN npm install -g gulp less
# Git config
RUN git config --global user.email "hforge@hforge.org" && \
    git config --global user.name "hforge"
# Install PIP
ADD https://bootstrap.pypa.io/get-pip.py /tmp/
RUN python2 get-pip.py && pip install --upgrade pip
# INSTALL sphinx
RUN pip install sphinx
# Install xapian
ADD http://oligarchy.co.uk/xapian/1.4.2/xapian-core-1.4.2.tar.xz /tmp/
RUN tar Jxf /tmp/xapian-core-1.4.2.tar.xz && cd /tmp/xapian-core-1.4.2 && ./configure && make && make install
# Install xapian-bindings python
ADD http://oligarchy.co.uk/xapian/1.4.2/xapian-bindings-1.4.2.tar.xz /tmp/
RUN cd /tmp/ && tar Jxf /tmp/xapian-bindings-1.4.2.tar.xz && cd /tmp/xapian-bindings-1.4.2 && ./configure --with-python && make && make install
# Install libgit2
ADD https://github.com/libgit2/libgit2/archive/v0.27.0.zip /tmp/
RUN cd /tmp/ && unzip v0.27.0.zip && cd /tmp/libgit2-0.27.0 && mkdir build && cd /tmp/libgit2-0.27.0/build \
    && cmake .. && cmake --build . --target install && ln -s /usr/local/lib/libgit2.so.27 /usr/lib/libgit2.so.27 && ldconfig
# Set ENV to compile pillow (https://github.com/python-pillow/Pillow/issues/1763)
ENV LIBRARY_PATH=/lib:/usr/lib
# INSTALL libgit2 (https://github.com/python-pillow/Pillow/issues/1763)
# Install PIL (because it's not part of itools requirements)
RUN pip install pygit2==0.27.0 pillow==3.0.0
# FontAwesome
ADD https://github.com/FortAwesome/Font-Awesome/raw/fa-4/fonts/FontAwesome.otf /usr/share/fonts/
# Install itools / ikaaro
RUN pip install lxml
RUN pip install --force-reinstall --upgrade "git+https://github.com/hforge/itools@master#itools"
RUN pip install --force-reinstall --upgrade "git+https://github.com/hforge/ikaaro@master#ikaaro"
RUN pip install --force-reinstall --upgrade "git+https://github.com/hforge/goodforms@master#goodforms"
EXPOSE 8080
COPY launch_ikaaro.sh /usr/bin/
CMD /bin/sh /usr/bin/launch_ikaaro.sh
