# Security Policy

This is a personal learning fork of [stefanprodan/podinfo](https://github.com/stefanprodan/podinfo),
used to practise a supply-chain-secured CI/CD pipeline. There is no SLA and no
commercial support; the points below are best effort.

## Supported versions

| Version | Supported |
| ------- | --------- |
| `main` branch | yes |
| Latest signed image on `ghcr.io/aidantiu/podinfo` (the most recent release from `main`) | yes |
| Anything older | no, update to the latest |

## Reporting a vulnerability

Please report privately; do not open a public issue.

Use GitHub private vulnerability reporting: go to the repository's
**Security** tab and choose **Report a vulnerability**
(<https://github.com/aidantiu/podinfo/security/advisories/new>).

Include what you found, how to reproduce it, and the affected commit or image digest.

## What to expect

- Acknowledgement within about 7 days.
- A first assessment within about 14 days.
- A fix, or a documented reason for not fixing, on a best-effort basis. Fixes land
  on `main` through a pull request and ship as a new signed image.
- Credit in the advisory if you want it.

## Scope

In scope:

- This fork's CI/CD workflows in `.github/workflows/` and the release pipeline.
- The container images published at `ghcr.io/aidantiu/podinfo`.
- Dependencies pinned by this fork (see `go.mod`).

Out of scope: bugs in the upstream podinfo application code that are not specific
to this fork. Report those to
[stefanprodan/podinfo](https://github.com/stefanprodan/podinfo/security).

## Verifying releases

Every image is signed keylessly with cosign and carries SLSA build provenance and
an SBOM attestation. Verify by digest (never by tag):

```sh
cosign verify ghcr.io/aidantiu/podinfo@sha256:<digest> \
  --certificate-identity https://github.com/aidantiu/podinfo/.github/workflows/release.yml@refs/heads/main \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com

gh attestation verify oci://ghcr.io/aidantiu/podinfo@sha256:<digest> --repo aidantiu/podinfo \
  --signer-workflow aidantiu/podinfo/.github/workflows/release.yml \
  --source-ref refs/heads/main --deny-self-hosted-runners
```

See [SECURITY-PIPELINE.md](SECURITY-PIPELINE.md) for how the pipeline works.
