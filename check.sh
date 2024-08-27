set -e  # Exit immediately if a command exits with a non-zero status.

if [ "$1" == "--no-fix" ]; then
    poetry run ruff format --check
    poetry run ruff check --select I
    poetry run ruff check
else
    poetry run ruff format
    poetry run ruff check --fix --select I
    poetry run ruff check --fix
fi

poetry check
poetry run pip check
