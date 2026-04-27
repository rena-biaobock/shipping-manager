# OpenEdge PASOE back-end image
# Replace 'your-registry/openedge:12.7' with your actual licensed base image.
FROM your-registry/openedge:12.7

WORKDIR /shipping_manager

COPY src/                    ./src/
COPY schema/                 ./schema/
COPY conf/                   ./conf/
COPY WEB-INF/                ./WEB-INF/
COPY build.xml               ./build.xml
COPY docker-entrypoint.sh    /docker-entrypoint.sh

RUN chmod +x /docker-entrypoint.sh \
    && ant compile \
    && mkdir -p /data /reports

EXPOSE 8080

ENTRYPOINT ["/docker-entrypoint.sh"]
