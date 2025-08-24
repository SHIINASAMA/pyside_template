# Release and Product Version Control

This template integrates **GitLab Pipeline** for automated release. By pushing a Git tag, you can automatically trigger
the build and release process.

## Prerequisites

1. **GitLab Package Registry Access**: Ensure that the built-in GitLab Package Registry can be accessed by both the
   application and the Runner.

2. **Runner Configuration**: Verify that the GitLab Runner for the target platform is properly installed and configured.

3. **Code Preparation**: In the `fetch_latest_release_via_gitlab` method, fill in the current project's `base_url` and
   `project_name`.

> ⚠️ **Currently only Windows platform is supported.**  
> GitLab CI’s multi-platform build and release support is limited and will not be officially supported in the future.  
> For cross-platform requirements, consider using **GitHub Actions** or other CI/CD platforms with native matrix
> support.

## Release Workflow

When you push a tag to the remote repository, the CI/CD pipeline will be automatically triggered to build and publish
the release.

The **tag\_name** will serve as both the version number and the release channel.

## Tag Format Specification

The tag must follow one of the following formats:

- `x.y.z`

- `x.y.z-stable`

- `x.y.z-beta`

Where:

- **x.y.z** → Semantic Versioning, e.g., `1.2.3`

- **channel** → Release channel (optional). Currently supported values:

    - `stable` (stable release)

    - `beta` (beta release)

If additional release channels are required, the `Version` class constructor logic must be extended.

## References

- Version parsing and update logic: `app/builtin/updater.py`

- CI/CD release scripts: `.gitlab-ci.yml` and related scripts
    
