#!/bin/bash

set -e

envsubst < /etc/nginx/default.conf.tpl > /etc/nginx/conf.d/defaul.conf
nginx -g 'daemon off;'
