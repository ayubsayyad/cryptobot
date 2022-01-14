#set -x
export KAFKA_URL=`heroku config:get KAFKA_URL`
export KAFKA_CLIENT_CERT_KEY=`heroku config:get KAFKA_CLIENT_CERT_KEY`
export KAFKA_TRUSTED_CERT=`heroku config:get KAFKA_TRUSTED_CERT`
export KAFKA_CLIENT_CERT=`heroku config:get KAFKA_CLIENT_CERT`
export KAFKA_PREFIX=`heroku config:get KAFKA_PREFIX`


