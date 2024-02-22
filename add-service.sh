#!/bin/bash
read -p 'Please enter website name: ' fulldomain
read -p 'Please enter project name: ' project
read -p 'Please enter the App Engine service name: ' service
read -p "Are there multiple TLDs? (Y/N)" yn
    case $yn in
        [Yy]* ) domain=`echo "${fulldomain//./}"`;;
        [Nn]* ) domain=`echo "$fulldomain" | sed 's/\..*$//'`;;
        * ) echo "Please answer yes or no.";;
    esac

gcloud beta compute network-endpoint-groups create www-$domain-serverless-neg --region=northamerica-northeast1 --network-endpoint-type=SERVERLESS --app-engine-service=$service
gcloud beta compute network-endpoint-groups create api-$domain-serverless-neg --region=northamerica-northeast1 --network-endpoint-type=SERVERLESS --app-engine-service=$service-api
gcloud beta compute network-endpoint-groups create app-$domain-serverless-neg --region=northamerica-northeast1 --network-endpoint-type=SERVERLESS --app-engine-service=$service-dashboard

gcloud compute backend-services create www-$domain-backend --global
gcloud compute backend-services create api-$domain-backend --global
gcloud compute backend-services create app-$domain-backend --global
gcloud beta compute backend-services add-backend www-$domain-backend --global --network-endpoint-group=www-$domain-serverless-neg --network-endpoint-group-region=northamerica-northeast1
gcloud beta compute backend-services add-backend api-$domain-backend --global --network-endpoint-group=api-$domain-serverless-neg --network-endpoint-group-region=northamerica-northeast1
gcloud beta compute backend-services add-backend app-$domain-backend --global --network-endpoint-group=app-$domain-serverless-neg --network-endpoint-group-region=northamerica-northeast1

gcloud compute ssl-certificates create $domain-ssl-cert --domains $fulldomain
gcloud compute ssl-certificates create api-$domain-ssl-cert --domains api.$fulldomain
gcloud compute ssl-certificates create app-$domain-ssl-cert --domains app.$fulldomain
gcloud compute ssl-certificates create www-$domain-ssl-cert --domains www.$fulldomain

currentcerts=`gcloud compute target-https-proxies describe $project-https-proxy --global --format="get(sslCertificates)" | sed -r 's/[;]+/,/g'`

certs=$currentcerts,$domain-ssl-cert,api-$domain-ssl-cert,app-$domain-ssl-cert,www-$domain-ssl-cert

gcloud compute target-https-proxies update $project-https-proxy --ssl-certificates=$certs

gcloud compute url-maps add-path-matcher $project-https-url-map --default-service www-$domain-backend --path-matcher-name www-$domain-pathmatch --new-hosts=www.$fulldomain
gcloud compute url-maps add-path-matcher $project-https-url-map --default-service api-$domain-backend --path-matcher-name api-$domain-pathmatch --new-hosts=api.$fulldomain
gcloud compute url-maps add-path-matcher $project-https-url-map --default-service app-$domain-backend --path-matcher-name app-$domain-pathmatch --new-hosts=app.$fulldomain