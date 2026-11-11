FROM --platform=linux/amd64 ubuntu@sha256:fe81560990fae86dc4743202b2cb4d3df98d0bcf949173cecef15ce1127ef852
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends build-essential cmake ninja-build ca-certificates git python3 && rm -rf /var/lib/apt/lists/*
COPY .cache/embree-4.4.0.x86_64.linux.tar.gz /tmp/embree.tgz
COPY .cache/oneapi-tbb-2021.11.0-lin.tgz /tmp/tbb.tgz
RUN echo 'cb3d4402537fc9165c76c3316b8953dcfea523cd1eaf588e2de7639864ee3c57  /tmp/embree.tgz' | sha256sum -c - && echo '95659f4d7b1711c41ffa190561d4e5b6841efc8091549661c7a2e6207e0fa79b  /tmp/tbb.tgz' | sha256sum -c - && mkdir -p /opt/embree /opt/tbb && tar -xzf /tmp/embree.tgz -C /opt/embree && tar -xzf /tmp/tbb.tgz -C /opt/tbb --strip-components=1 && rm /tmp/*.tgz
COPY .cache/ericw-tools /opt/ericw-tools
RUN test "$(git -C /opt/ericw-tools rev-parse HEAD)" = c243aa348c9e5a1838bb69cf6c3ff20bebd94a8a && cmake -S /opt/ericw-tools -B /opt/build -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_PREFIX_PATH='/opt/embree;/opt/tbb' -DDISABLE_TESTS=ON -DDISABLE_DOCS=ON -DENABLE_LIGHTPREVIEW=OFF && cmake --build /opt/build --target qbsp vis light bsputil -j 6
ENV LD_LIBRARY_PATH=/opt/embree/lib:/opt/tbb/lib
RUN dpkg-query -W > /opt/build-packages.txt && sha256sum /opt/build/qbsp/qbsp /opt/build/vis/vis /opt/build/light/light /opt/build/bsputil/bsputil > /opt/compiler-checksums.txt
WORKDIR /work
