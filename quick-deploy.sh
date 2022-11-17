#!/bin/sh
# create registry container unless it already exists
reg_name='kind-registry'
reg_port='5001'
if [ "$(docker inspect -f '{{.State.Running}}' "${reg_name}" 2>/dev/null || true)" != 'true' ]; then
  docker run \
    -d --restart=always -p "127.0.0.1:${reg_port}:5000" --name "${reg_name}" \
    registry:2
fi
kind create cluster --config=k8s/kind.yaml

if [ "$(docker inspect -f='{{json .NetworkSettings.Networks.kind}}' "${reg_name}")" = 'null' ]; then
  docker network connect "kind" "${reg_name}"
fi

kubectl apply -f k8s/registry.yaml

kubectl apply -f https://raw.githubusercontent.com/kubernetes/dashboard/v2.6.1/aio/deploy/recommended.yaml
kubectl apply -f k8s/dashboard/admin.yaml
sh k8s/dashboard/generate-token.sh
# Set up MetalLB
kubectl create namespace metallb-system
helm repo add metallb https://metallb.github.io/metallb
helm install metallb metallb/metallb -n metallb-system
kubectl wait --for=condition=Ready pod --all -n metallb-system
# Duplicate as sometimes above times out just as it finishes
sleep 5
kubectl wait --for=condition=Ready pod --all -n metallb-system
kubectl apply -f k8s/metallb-config.yaml -n metallb-system

# Setup NGINX Ingress
# Note the below is Kind specific for now
# helm repo add nginx-stable https://helm.nginx.com/stable
# helm repo update
# helm install my-release nginx-stable/nginx-ingress
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml

# Set up KNative
kubectl apply -f https://github.com/knative/operator/releases/download/knative-v1.7.1/operator.yaml
kubectl create namespace knative-serving

# Load in images
kind load docker-image appstore-ai-back-end:latest
kind load docker-image appstore-ai-front-end:latest
# Set up helm charts
helm install ai-mongodb charts/mongodb/ --values charts/mongodb/values.yaml
helm install ai-backend charts/ai-be/ --values charts/ai-be/values.yaml
helm install ai-frontend charts/ai-fe/ --values charts/ai-fe/values.yaml
helm install inference-engine charts/ai-ie/ --values charts/ai-be/values.yaml  --create-namespace --namespace inference-engine
