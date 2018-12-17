FROM debian:stretch-slim
WORKDIR /root
COPY geth /usr/bin/geth
COPY passfile core.yaml config.yaml /root/
RUN apt-get update -qq && apt-get install -yqq --reinstall ca-certificates \
    && apt-get install -yqq --no-install-recommends build-essential flex bison subversion m4 python3 python3-dev python3-setuptools libgmp-dev libssl-dev git curl \
    && curl -SL https://crypto.stanford.edu/pbc/files/pbc-0.5.14.tar.gz | tar xzC ./ && cd pbc-0.5.14 && ./configure LDFLAGS="-lgmp" && make && make install \
    && cd .. && rm pbc-0.5.14 -rf && git clone https://github.com/facebook/rocksdb.git && cd rocksdb && git checkout 4.1.fb && make shared_lib \
    && rm .git -rf \
    && ln -sf /root/rocksdb/librocksdb.so.4.1.0 /usr/local/lib/librocksdb.so \
    && ln -sf /root/rocksdb/librocksdb.so.4.1.0 /usr/local/lib/librocksdb.so.4 \
    && ln -sf /root/rocksdb/librocksdb.so.4.1.0 /usr/local/lib/librocksdb.so.4.1 \
    && ln -sf /root/rocksdb/librocksdb.so.4.1.0 /usr/local/lib/librocksdb.so.4.1.0 \
    && cp include/rocksdb /usr/include/ -r && ldconfig \
    && rm /var/cache/apt/archives/* /var/lib/apt/lists/* -rf \
    && apt-get remove git curl -y \
    && apt-get autoremove -y \
    && mkdir /root/.geth-pbft && mv /root/config.yaml /root/.geth-pbft 
EXPOSE 8545 30303
#ENTRYPOINT [ "geth" ]
