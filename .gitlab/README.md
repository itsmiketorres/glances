# GitLab CI/CD Configuration

This directory contains GitLab-specific configuration for the Glances project.

## Pipeline Overview

The CI/CD pipeline is defined in `.gitlab-ci.yml` at the repository root and uses
[uv](https://github.com/astral-sh/uv) for fast Python dependency management.

### Pipeline Stages

| Stage | Description |
|-------|-------------|
| `quality` | Code quality checks (formatting, linting, security) |
| `test` | Unit tests across Python 3.10, 3.11, 3.12, and 3.13 |
| `build` | Build Python packages using `uv build` |
| `docker` | Build Docker images for Alpine and Ubuntu |
| `publish` | Publish to PyPI/TestPyPI (manual trigger) |

### Jobs

#### Quality Stage
- **format** - Check code formatting with Ruff
- **lint** - Lint code with Ruff
- **security** - Security scan with Bandit (allowed to fail)

#### Test Stage
- **test:python3.10** - Run tests on Python 3.10
- **test:python3.11** - Run tests on Python 3.11
- **test:python3.12** - Run tests on Python 3.12
- **test:python3.13** - Run tests on Python 3.13

#### Build Stage
- **build:package** - Build wheel and source distribution

#### Docker Stage
- **docker:alpine-minimal** - Minimal Alpine image
- **docker:alpine-full** - Full Alpine image with all dependencies
- **docker:ubuntu-minimal** - Minimal Ubuntu image
- **docker:ubuntu-full** - Full Ubuntu image with all dependencies
- **docker:tag-release** - Tag images on release

#### Publish Stage
- **publish:testpypi** - Publish to TestPyPI (manual, develop branch)
- **publish:pypi** - Publish to PyPI (manual, tags only)

## Required CI/CD Variables

Configure these variables in GitLab CI/CD Settings > Variables:

| Variable | Description | Protected | Masked |
|----------|-------------|-----------|--------|
| `PYPI_TOKEN` | PyPI API token for publishing releases | Yes | Yes |
| `TESTPYPI_TOKEN` | TestPyPI API token for testing | Yes | Yes |

The following variables are automatically provided by GitLab:
- `CI_REGISTRY_USER` - GitLab Container Registry username
- `CI_REGISTRY_PASSWORD` - GitLab Container Registry password
- `CI_REGISTRY` - GitLab Container Registry URL
- `CI_REGISTRY_IMAGE` - Full path to the container image

## Pipeline Triggers

The pipeline runs on:
- **Merge requests** to `develop` branch
- **Push** to `develop` or `master` branches
- **Tags** matching `v*` pattern

## Using uv

The pipeline uses [uv](https://github.com/astral-sh/uv) instead of pip/venv for:
- Faster dependency resolution and installation
- Consistent lockfile-based builds
- Built-in virtual environment management

### Key Commands Used

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Sync dependencies
uv sync --dev

# Run tests
uv run pytest tests/test_core.py -v

# Build package
uv build

# Publish to PyPI
uv publish --token $PYPI_TOKEN
```

## Local Testing

To validate the GitLab CI configuration locally:

```bash
# Run the GitLab CI test suite
make test-gitlab-ci

# Or directly with pytest
uv run pytest tests/test_gitlab_ci.py -v
```

## Docker Images

Docker images use uv for dependency installation. See `docker-files/` for:
- `alpine.Dockerfile` - Alpine-based images
- `ubuntu.Dockerfile` - Ubuntu-based images

Both Dockerfiles copy uv from the official image:
```dockerfile
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
```
