# envoy-gateway

Envoy Gateway controller + the shared `prod-gateway` Gateway (namespace
`gateway-system`) + the `letsencrypt-prod` ClusterIssuer that every app
chart in this repo already assumes exist.

**This was written assuming Envoy Gateway / prod-gateway / letsencrypt-prod
are already running in production, created some other way. Before running
`helm upgrade --install` with this chart against that cluster:**

1. Confirm the real GatewayClass name: `kubectl get gatewayclass` - set
   `gatewayClassName` to match. Do not assume it's called `eg`.
2. Confirm the real Gateway's current listeners before enabling
   `gateway.https.enabled`: `kubectl get gateway prod-gateway -n gateway-system -o yaml`.
   The commented-out `gateway.https.certificates` list in `values.yaml`
   is only a reference built from hostnames already in the other app
   charts here - not a confirmed copy of the live listener config.
3. Confirm the release name/namespace Envoy Gateway is already
   installed under (`helm list -A`) so this chart adopts the existing
   release instead of creating a conflicting second one.

Deploy:
```
helm dependency update ./envoy-gateway
helm upgrade --install envoy-gateway ./envoy-gateway -n envoy-gateway-system --create-namespace
```
