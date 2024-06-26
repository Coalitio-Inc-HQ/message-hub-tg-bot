#!/bin/bash

cat <<EOF > /app/src/config/.env
WEB_SERVER_HOST=${WEB_SERVER_HOST}
WEB_SERVER_PORT=${WEB_SERVER_PORT}
SERVER_WEBHOOK_URL=${SERVER_WEBHOOK_URL}
TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
MONGODB_URI=${MONGODB_URI}
WEBHOOK_URL=${WEBHOOK_URL}
WEBHOOK_USER_REGISTRATION_PATH=${WEBHOOK_USER_REGISTRATION_PATH}
WEBHOOK_SEND_MESSAGE_PATH=${WEBHOOK_SEND_MESSAGE_PATH}
WEBHOOK_PLATFORM_REGISTRATION_PATH=${WEBHOOK_PLATFORM_REGISTRATION_PATH}
EOF
