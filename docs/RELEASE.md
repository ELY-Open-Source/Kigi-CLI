# Release checklist (PRD F8)

Kigi ships as a single-file binary for five targets, published on this
repo's GitHub Releases
(<https://github.com/ELY-Open-Source/Kigi-CLI/releases>) by
`.github/workflows/release.yml`. Users install via `install.sh` /
`install.ps1` and stay current through the in-app self-updater
(`kigi-update`), which resolves the same Releases API.

## Cutting a release

1. Bump `[workspace.package] version` in `Cargo.toml`; land the change on
   `main` with green CI.
2. Regenerate the third-party notices (not enforced by CI — this is the
   step that keeps `THIRD-PARTY-NOTICES.md` fresh):

   ```sh
   cargo install cargo-about --locked   # once
   cargo about generate about.hbs -o THIRD-PARTY-NOTICES.md
   ```

   Commit the result if it changed.
3. Tag and push:

   ```sh
   git tag vX.Y.Z && git push origin vX.Y.Z
   ```

   The tag must equal the workspace version (`vX.Y.Z` ↔ `X.Y.Z`); the
   workflow fails fast on a mismatch.
4. The `Release` workflow builds all five targets with the hardened
   `release-dist` profile, packages
   `kigi-<version>-<target-triple>.{tar.gz|zip}` archives (binary +
   LICENSE + NOTICE + THIRD-PARTY-NOTICES), generates `SHA256SUMS`, and
   publishes the GitHub Release. Tags containing `-` (e.g.
   `v0.2.0-alpha.1`) publish as pre-releases, which only the `alpha`
   update channel picks up.

   The release is created as a **draft** and only flipped public once
   `SHA256SUMS` is attached, so `releases/latest` never hands the installer
   a release whose checksum manifest is still missing. A failed run leaves
   the draft in place; re-running the workflow reuses it rather than
   erroring on a duplicate `tag_name`.
5. Smoke-test an installed artifact:

   ```sh
   curl -fsSL https://kigicli.dev/install.sh | sh
   ~/.kigi/bin/kigi --version
   ```

## Build runners

Every leg runs on a GitHub-hosted runner; none needs local state, so no
self-hosted runner is involved. The repo is public, so keep it that way: a
self-hosted runner must never be reachable from a `pull_request` event, and
this workflow only triggers on tag pushes.

| Runner             | Builds                                                  |
| ------------------ | ------------------------------------------------------- |
| `ubuntu-latest`    | `x86_64-unknown-linux-gnu`                              |
| `ubuntu-24.04-arm` | `aarch64-unknown-linux-gnu` (native, no cross toolchain) |
| `macos-latest`     | `aarch64-apple-darwin`, `x86_64-apple-darwin`           |
| `windows-latest`   | `x86_64-pc-windows-msvc`                                |

`macos-latest` is Apple Silicon; `x86_64-apple-darwin` is a cross-compile
against the same SDK. The Darwin targets need the real Apple linker
(`.cargo/config.toml` passes `-ObjC` and `-undefined dynamic_lookup`), so they
cannot move to a Linux runner.

`windows-latest` ships the VS Build Tools the static MSVC CRT link needs
(`ring`, `mimalloc`, `zstd-sys` and `libz-sys` build with
`-C target-feature=+crt-static`). Every job installs protoc
(`PROTOC_VERSION`, matching the `bin/protoc` dotslash pin) and runs
`rustup show` to materialise the `rust-toolchain.toml` pin; the arm64 Linux
leg installs rustup first if the image lacks it.

The release steps use the preinstalled `gh` CLI with `secrets.GITHUB_TOKEN`
(`permissions: contents: write`): `gh release create --draft`, then
`gh release upload` per target, then `SHA256SUMS` and
`gh release edit --draft=false`. Only the five checksum lines travel through
`actions/upload-artifact@v4`; the archives go straight to the release.

Build caches come from `Swatinem/rust-cache`. GitHub only lets a tag run
restore caches made on its own ref or the default branch, and nothing builds
on `main`, so a tag build starts cold; the cache helps re-runs of the same tag.

## Invariants to keep in lockstep

- Asset naming `kigi-<version>-<target-triple>.{tar.gz|zip}` and the
  `SHA256SUMS` manifest are consumed by three clients: `install.sh`,
  `install.ps1`, and `auto_update::release_asset_name()` in
  `crates/codegen/kigi-update`. Change one, change all (the kigi-update
  test `test_release_asset_name_matches_release_workflow_naming` pins the
  Rust side).
- Never publish two builds of the same semver version differing only in
  build metadata (`+…`) — the `semver` crate orders build metadata, so
  auto-update would bounce users between them.
- Rollbacks: deleting the bad release (or re-pointing "latest") is enough —
  the internal installer treats the Releases API as authoritative and
  downgrades clients on its own.
- No PyPI/npm packages, ever; in particular never squat the `kimi-cli`
  package name (PRD F8).
