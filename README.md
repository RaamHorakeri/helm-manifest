# Argo CD GitOps (production-ready)

This repository contains a production-oriented Argo CD deployment implemented as a Helm umbrella chart and GitOps manifests. It is safe to run on a test/staging cluster today and designed to scale to production by changing environment-specific values.

## Layout

- `bootstrap/argocd-bootstrap.yaml` - Namespace and manual bootstrap notes
- `applications/` - Argo CD `AppProject` and `Application` manifests (self-managed Application)
- `environments/` - Environment-specific Helm values (e.g. `prod`)
- `helm/argocd` - Umbrella Helm chart that depends on the official Argo CD Helm chart

## Key principles

- Uses the official Argo Helm chart as a dependency and pins chart versions.
- Charts and environment values are declarative and stored in Git.
- Self-management: after bootstrap, Argo CD manages its own Helm release.
- No secrets are committed. Use an external secret manager (Vault, ExternalSecrets, SOPS).
- No additional LoadBalancer or Ingress is created by default; use the cluster Gateway API.

## Initial installation (manual bootstrap)

1. Add the upstream repo and update:

```bash
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update
```

2. From the repository root:

```bash
helm dependency update ./helm/argocd

helm upgrade --install argocd ./helm/argocd \
  --namespace argocd \
  --create-namespace \
  --wait
```

3. Replace `REPLACE_WITH_REPO_URL` in `applications/argocd.yaml` and `applications/projects.yaml` with your repository URL, then apply:

```bash
kubectl apply -f bootstrap/argocd-bootstrap.yaml
kubectl apply -f applications/projects.yaml
kubectl apply -f applications/argocd.yaml
```

After Argo CD is bootstrapped, it will manage the `helm/argocd` release as an Application.

## Verification

```bash
kubectl get ns argocd
kubectl get pods -n argocd
kubectl get svc -n argocd
kubectl get applications -n argocd
```

## Upgrade procedure

1. Read upstream release notes for `argo-cd` chart version.
2. Update `helm/argocd/Chart.yaml` dependency `version` to the desired pinned version.
3. Run:

```bash
helm dependency update ./helm/argocd
helm lint ./helm/argocd
helm template argocd ./helm/argocd --namespace argocd
```

4. Review diffs, commit, open a PR, and let Argo CD sync the change (or trigger a sync).

## Rollback

- Use Argo CD UI or `argocd` CLI to rollback an Application to a previous revision. For Helm chart rollbacks, revert the Chart.yaml change and re-sync.

## Disaster recovery

1. Create a new cluster.
2. Apply `bootstrap/argocd-bootstrap.yaml` to create namespace.
3. Install Argo CD via Helm (manual bootstrap) using the `helm/argocd` chart from this repo.
4. Apply `applications/projects.yaml` and `applications/argocd.yaml` (ensure `repoURL` is reachable).

All subsequent applications will be reconciled from Git.

## Security and secrets

- Do not store passwords or tokens in Git. Use ExternalSecrets, Vault, or SOPS to inject secrets into the cluster.
- Set up RBAC in `applications/projects.yaml` to avoid giving everyone admin rights.

## Notes and next steps

- Replace all `REPLACE_WITH_REPO_URL` and cluster placeholders before bootstrapping.
- Validate Helm templates and Kubernetes manifests against your cluster API and admission controllers before syncing.
# Argo CD GitOps Deployment

This repository defines a production-oriented GitOps deployment of Argo CD using a Helm wrapper chart.
It is designed for a test/staging cluster today, while remaining structured for future production use.

## Architecture

```
Git Repository
      │
      ▼
 Argo CD Helm Chart
      │
      ▼
   Argo CD
      │
      ├── Applications
      ├── AppProjects
      ├── ApplicationSets
      └── Helm Applications
             │
             ▼
       Kubernetes Cluster
```

## Repository Layout

- `bootstrap/argocd-bootstrap.yaml` – initial bootstrap namespace and root application entrypoint.
- `applications/root.yaml` – root GitOps application deploys the `applications/` directory.
- `applications/projects.yaml` – Argo CD project for self-management.
- `applications/argocd.yaml` – self-managed Argo CD Helm application.
- `environments/prod/argocd-values.yaml` – production-specific Argo CD values overrides.
- `environments/prod/cluster-config.yaml` – production environment metadata.
- `helm/argocd/Chart.yaml` – local Helm wrapper chart.
- `helm/argocd/values.yaml` – common Argo CD Helm values.

## Initial Installation

1. Add the Argo Helm repository:

```bash
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update
```

2. Bootstrap the `argocd` namespace and install the local chart:

```bash
cd helm-manifest
helm dependency update ./helm/argocd
helm upgrade --install argocd ./helm/argocd \
  --namespace argocd \
  --create-namespace \
  --wait
```

3. Apply the bootstrap resources after Argo CD is installed:

```bash
kubectl apply -f bootstrap/argocd-bootstrap.yaml
```

This creates the root GitOps application that brings the rest of `applications/` under Argo CD management.

## Verification

```bash
kubectl get ns argocd
kubectl get pods -n argocd
kubectl get svc -n argocd
kubectl get applications -n argocd
```

## Upgrade Procedure

1. Review the current pinned chart version in `helm/argocd/Chart.yaml`.
2. Update `helm/argocd/Chart.yaml` to the desired pinned version.
3. Run:

```bash
helm dependency update ./helm/argocd
helm lint ./helm/argocd
helm template argocd ./helm/argocd --namespace argocd
```

4. Review the generated diff.
5. Commit the version bump and values changes.
6. Allow Argo CD to sync the updated application.

## Rollback

- Roll back the Git commit that changed `helm/argocd/Chart.yaml` or `environments/prod/argocd-values.yaml`.
- Re-sync the Argo CD `argocd` application from the UI or CLI.
- If necessary, use `kubectl rollout undo deployment/<name> -n argocd` for individual components.

## Disaster Recovery

If the cluster is lost, rebuild from Git:

1. Create the Kubernetes cluster.
2. Install Argo CD with the pinned chart from `helm/argocd`.
3. Apply `bootstrap/argocd-bootstrap.yaml`.
4. Argo CD will reconcile the `applications/` directory and restore the self-managed state.

## Security and Secrets

- This repository does not store admin passwords, GitHub tokens, SSH private keys, cloud credentials, TLS private keys, or other secrets.
- Use an external secret manager for production secrets:
  - External Secrets Operator
  - HashiCorp Vault
  - Cloud provider secret manager
  - Mozilla SOPS / Sealed Secrets
- Keep secret injection outside of Git and use references, not literal values.

## Notes

- The Argo CD installation uses the official upstream `argo-cd` Helm chart as a dependency.
- Chart versions are explicitly pinned in `helm/argocd/Chart.yaml`.
- The `argocd` service is configured as `ClusterIP` to remain compatible with a shared Gateway API architecture.
- Persistent volumes are not provisioned for Argo CD unless a future environment explicitly requires them.
