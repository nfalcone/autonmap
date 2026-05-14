FROM alpine:3.19

RUN apk add --no-cache \
    nmap \
    nmap-scripts \
    python3 \
    nginx \
    tzdata

# Create dirs
RUN mkdir -p /data/scans /var/log/autonmap /run/nginx /opt/autonmap

# Copy scripts
COPY scripts/ /opt/autonmap/
RUN chmod +x /opt/autonmap/*.sh

# Replace default nginx site with our config
COPY nginx.conf /etc/nginx/http.d/default.conf

# nmap.xsl is included with nmap - copy to scan dir at runtime via entrypoint
# (so it's available for raw XML viewing in Firefox too)

VOLUME ["/data"]
EXPOSE 80

CMD ["/opt/autonmap/entrypoint.sh"]
