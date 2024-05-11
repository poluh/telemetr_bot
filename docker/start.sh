#!/bin/bash

rm -rf app
cp -r ../app .

# Сборка и запуск контейнеров
docker compose up -d --build

docker logs -f telemetr-bot
