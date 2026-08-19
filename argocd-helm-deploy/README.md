# argocd-helm-deploy

Argo CD, routed through the shared `prod-gateway` Gateway (see
`../envoy-gateway`) instead of its own LoadBalancer. Pinned to chart
version 9.5.4 (app v3.3.8) - bump deliberately when ready, don't assume
latest.

Includes a self-managed Argo CD `Application` (`templates/self-application.yaml`)
pointing back at this same chart in this repo, so once applied once,
future changes here sync automatically. Confirm `selfManage.targetRevision`
in `values.yaml` matches the branch your production Argo CD is meant to
track before relying on that.

Deploy (first time, before self-management takes over):
```
helm dependency update ./argocd-helm-deploy
helm upgrade --install argocd ./argocd-helm-deploy -n argocd --create-namespace
```
