# Security pipeline of this fork

This fork of [stefanprodan/podinfo](https://github.com/stefanprodan/podinfo) adds a CI pipeline that decides, automatically, whether a change is safe to merge and whether an image is safe to publish. The full policy lives in the private `platform-gitops` repository (`docs/03-security-policy.md`); this page explains each gate in plain words.

A **gate** is a check that can say "no". A red gate means the pull request cannot be merged (a ruleset on `main` requires these checks), or, for the release workflow, that the image is never signed.

## The gates on every pull request (`ci.yml`, `codeql.yml`)

| Check name | What it does | Fails when | Why it matters |
| --- | --- | --- | --- |
| `test` | `go test ./...` | any unit test fails | Broken code is not shipped |
| `lint` | three tools, see below | any of them fails | Catches mistakes before they are built into an image |
| `sca` | Trivy scans `go.mod` for known vulnerabilities (SCA = software composition analysis: "what libraries do I use and are they known-bad?"). `govulncheck` also runs but only warns | a **fixable CRITICAL** vulnerability is found | A dependency with a published critical hole and a published fix must be updated, not ignored |
| `build` | builds the `linux/arm64` image on a native arm64 runner (nothing is pushed), starts it, calls `/healthz`, then Trivy scans the image (Alpine packages and Go modules inside the binary) | the image does not build or start, or has a **fixable CRITICAL** vulnerability | The thing that would run on the Raspberry Pi is the thing that is checked |
| `CodeQL` | static analysis (SAST: reads the source for dangerous patterns such as command injection) | a **high or critical** alert is raised (the ruleset rule "code scanning results" blocks the merge) | Finds bugs in our own code, not only in libraries |

The three tools inside `lint`:

| Tool | Checks | Fails when |
| --- | --- | --- |
| gitleaks | the commits of the pull request for secrets (keys, tokens, passwords). On `main` it scans all history | any secret is found. History inherited from upstream contains old demo keys; they are listed one by one in `.gitleaksignore` so a **new** one still fails |
| hadolint | the `Dockerfile` | a finding of level `error`. Warnings and info are shown, not blocking |
| actionlint | the workflow files in `.github/workflows` | a syntax error or unsafe shell in a workflow. A second step also fails if anyone writes `pull_request_target` (a trigger that runs untrusted code with secrets) |

"Fixable" means the vulnerability database lists a version that fixes it (`--ignore-unfixed`). We do not block on holes nobody can fix yet; they are listed in the job summary as a warning.

### Exceptions

If a vulnerability really must be accepted for a while, add it to `.trivyignore.yaml` with a `statement` (why, with a link) and `expired_at` (at most 30 days away). `.github/scripts/check-trivyignore.py` fails the build if a field is missing, the date is too far away or already past. After the date Trivy stops ignoring the entry and the gate fails again.

## The release (`release.yml`, only after a merge to `main`)

1. `build`: build the arm64 image, push it to `ghcr.io/aidantiu/podinfo:sha-<8 chars of the commit>`, and record its **digest** (a hash of the image: it cannot be changed without changing the digest).
2. `scan`: Trivy scans the *pushed digest* with the same gate. It also writes an SBOM (software bill of materials: the list of everything inside the image, SPDX format).
3. `sign`: runs only if `scan` passed. Signs the digest with cosign "keyless" (a short-lived certificate tied to this workflow on `main`; there is no private key to steal), then attaches build provenance (who built it, from which commit, on which runner) and the SBOM, then verifies its own signature.

Result: `ghcr.io/aidantiu/podinfo:sha-<8>@sha256:<digest>`. Deployments use the digest, never the tag.

Verify an image yourself:

```sh
cosign verify ghcr.io/aidantiu/podinfo@sha256:<digest> \
  --certificate-identity https://github.com/aidantiu/podinfo/.github/workflows/release.yml@refs/heads/main \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com

gh attestation verify oci://ghcr.io/aidantiu/podinfo@sha256:<digest> --repo aidantiu/podinfo \
  --signer-workflow aidantiu/podinfo/.github/workflows/release.yml --source-ref refs/heads/main --deny-self-hosted-runners
```

## How the pipeline protects itself

- Every action is pinned to a full commit SHA (the repository setting rejects anything else). A moved tag cannot change what runs (in March 2026 the Trivy action tags were hijacked).
- Workflows start with `permissions: {}`; each job lists the few permissions it needs. Only the `sign` job can request the OIDC token used for signing; the scanner job cannot write to the registry.
- Checkout does not keep the token in `.git`, user-controlled text is never placed into a shell command, and every job has a timeout.
- The default token is read-only; Actions may only use GitHub-owned actions plus a short allow-list.
- Dependabot opens weekly grouped pull requests for Go modules, the Docker base images and the actions.

## Run the gates on your laptop

```sh
brew install pre-commit hadolint yq
pre-commit install          # runs on every commit
pre-commit run --all-files  # runs everything now
```

The hooks are gitleaks, hadolint, actionlint, yamllint, `gofmt`, `go vet` and the `.trivyignore.yaml` check.
