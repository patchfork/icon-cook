# Icon Cook

Icon Cook tracks two upstream open-source icon collections, normalizes their SVGs,
commits the generated files, and uploads changed icons to every configured
S3-compatible bucket.

## Collections

| Collection | Upstream input | Repository output | Object-key prefix |
| --- | --- | --- | --- |
| Fluent UI System Icons | `assets/*/SVG/*.svg` from [`microsoft/fluentui-system-icons`](https://github.com/microsoft/fluentui-system-icons) | `icons/fli/` | `img/icons/fli/` |
| Material Symbols Rounded | `symbols/web/*/materialsymbolsrounded/<name>_24px.svg` from [`google/material-design-icons`](https://github.com/google/material-design-icons) | `icons/msr/` | `img/icons/msr/` |

The Google input is the current **Material Symbols Rounded** collection shown by
[Google Fonts](https://fonts.google.com/icons?icon.style=Rounded). The unqualified
`<name>_24px.svg` export is the default-axis variant: optical size 24, weight 400,
grade 0, and fill 0. Files with names such as `fill1`, `grad200`, or `wght700` are
deliberately ignored.

For Fluent, icons are grouped by logical name and style. Selection favors drawings
intended for typical 24–28px UI use, in this order: `24`, `28`, `20`, `32`, `16`,
then `48`. Uncommon sizes fall back to the closest size to 24, preferring the larger
candidate on a tie. Thus `ic_fluent_access_time_24_filled.svg` becomes
`access_time_filled.svg` even when a 48px version exists.

Material Symbols use a separate rule: always select the default-axis 24px optical
size. Material Symbols no longer use the classic category directory, so
`symbols/web/3d_rotation/materialsymbolsrounded/3d_rotation_24px.svg` becomes
`3d_rotation.svg`.

SVGO optimizes every generated file, removes root `width` and `height`, and keeps
the `viewBox`. Existing generated icons are never deleted automatically. If an
upstream file is removed or renamed, the old flat icon remains in this repository
and in object storage.

## GitHub setup

Copy the committed example to the gitignored configuration file:

```sh
cp config/s3-configs.example.json config/s3-configs.json
```

Edit `config/s3-configs.json`, then create one Actions repository secret
named `S3_CONFIGS`. Its value is the complete JSON array:

```json
[
  {
    "name": "local",
    "endpoint_url": "https://your-s3-compatible-endpoint.example.com",
    "region_name": "us-east-1",
    "bucket_name": "local-icons",
    "access_key_id": "access-key-id",
    "secret_access_key": "secret-access-key",
    "addressing_style": "auto",
    "signature_version": "s3v4"
  },
  {
    "name": "review",
    "endpoint_url": "https://your-s3-compatible-endpoint.example.com",
    "region_name": "us-east-1",
    "bucket_name": "review-icons",
    "access_key_id": "access-key-id",
    "secret_access_key": "secret-access-key"
  },
  {
    "name": "production",
    "endpoint_url": "https://your-s3-compatible-endpoint.example.com",
    "region_name": "us-east-1",
    "bucket_name": "production-icons",
    "access_key_id": "access-key-id",
    "secret_access_key": "secret-access-key"
  }
]
```

The required fields are `name`, `endpoint_url`, `region_name`, `bucket_name`,
`access_key_id`, and `secret_access_key`. Optional fields are `session_token`,
`addressing_style` (`auto`, `path`, or `virtual`), and `signature_version` (defaults
to `s3v4`). Use credentials scoped to object-write access for only the target
buckets.

The private `config/s3-configs.json` file is ignored by Git. Never force-add it.
The committed [`config/s3-configs.example.json`](config/s3-configs.example.json)
contains placeholders only.

Check the file size and upload it from the repository root with GitHub CLI:

```sh
wc -c config/s3-configs.json
gh secret set S3_CONFIGS < config/s3-configs.json
```

To target a repository other than the one inferred from the current checkout:

```sh
gh secret set S3_CONFIGS --repo OWNER/REPOSITORY \
  < config/s3-configs.json
```

> **GitHub secret-size warning:** an Actions secret is limited to 48 KB (49,152
> bytes). Keep `config/s3-configs.json` below that limit. GitHub also warns
> that structured secret values may not be redacted reliably. These workflows pass
> the JSON directly through an environment variable and never print it; avoid debug
> tracing or otherwise echoing `S3_CONFIGS`.

In **Settings → Actions → General → Workflow permissions**, allow GitHub Actions
to read and write repository contents so the workflows can commit generated icons.
If `main` is protected, allow the Actions bot to push or adjust the final commit
step to use your normal pull-request process.

## Automation behavior

The two independent workflows run every six hours at staggered times and can also
be started with `workflow_dispatch`. They do not run for pull requests or for
ordinary pushes to this repository, avoiding self-trigger loops after their bot
commits.

GitHub Actions cannot subscribe directly to pushes in an unrelated public
repository. Scheduled polling is therefore the default. A true immediate trigger
would require cooperation from the upstream repository (for example, an upstream
workflow or webhook sending `repository_dispatch`).

Each workflow uses a sparse, blob-filtered checkout. It stores the last relevant
upstream state under `.upstream/`, skips runs where the tracked tree or manifest is
unchanged, and on later changes regenerates only affected logical icons. It uploads
only that affected list, then commits the generated files and state. The state is
committed only after all configured bucket uploads succeed, so a failed upload is
retried on the next run.

## Local use

Install Node.js 22 and Python 3, then:

```sh
npm install
npm test
python3 scripts/sync_icons.py fluent \
  --source /path/to/fluentui-system-icons \
  --output icons/fli \
  --output-list /tmp/fluent-uploads.txt
```

Use `material-rounded` and a checkout of `google/material-design-icons` for the
other collection. Local upload requires `boto3` and defaults to the gitignored
`config/s3-configs.json` file:

```sh
python3 scripts/upload_s3.py \
  --directory icons/fli \
  --file-list /tmp/fluent-uploads.txt \
  --prefix img/icons/fli
```

Alternatively, set `S3_CONFIGS` to the JSON array or set `S3_CONFIGS_FILE` to a
different local file. The environment value takes precedence over the file.

## Licenses

- Fluent UI System Icons are licensed under the MIT License. Attribution is in
  [`icons/fli/LICENSE.md`](icons/fli/LICENSE.md).
- Google Material Symbols are licensed under the Apache License 2.0.
  Attribution is in [`icons/msr/LICENSE.md`](icons/msr/LICENSE.md).

The repository's own code is covered by the root [`LICENSE`](LICENSE).
