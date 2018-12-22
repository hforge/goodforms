#!/bin/sh
#postfix start
if [ ! -d "/databases/www.goodforms.com" ]; then
  cd /databases/
  icms-init.py -r goodforms -e contact@example.com -w password -p 8080 www.goodforms.com
  sed -i 's/127.0.0.1/*/g' www.goodforms.com/config.conf
fi
cd /databases/
# Launch app
icms-start.py www.goodforms.com --quick -d
# Tail -f on access to keep docker running
touch www.goodforms.com/log/access
tail -f www.goodforms.com/log/access
