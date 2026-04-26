# OpenEdge PASOE back-end image
# Requires a licensed Progress OpenEdge 12.x base image.
# Replace 'your-registry/openedge:12.7' with your actual base image.
FROM your-registry/openedge:12.7

WORKDIR /shipping_manager

# Copy ABL source and supporting files
COPY src/      ./src/
COPY schema/   ./schema/
COPY conf/     ./conf/
COPY WEB-INF/  ./WEB-INF/
COPY build.xml ./build.xml

# Compile ABL sources using PCT/Ant
RUN ant compile

# Apply schema to the pre-created database.
# In production, run "ant updatedb" as part of the container entrypoint
# after the OpenEdge database is up and accepting connections.

EXPOSE 8080

# PASOE start via tcman — reads conf/openedge.properties at runtime
ENTRYPOINT ["${DLC}/bin/tcman", "start", "shipping_manager"]
CMD []
