#!/usr/bin/env bash
# Render pre-deploy command for hrms-tenant-admin (set it to `./predeploy.sh`).
#
# A script rather than an inline `migrate && ensure_operator` because Render
# runs a Docker service's pre-deploy command without a shell: `&&` is passed
# to manage.py as a literal argument and migrate fails with
# "unrecognized arguments".
set -euo pipefail

python manage.py migrate --no-input
python manage.py ensure_operator
