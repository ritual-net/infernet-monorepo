update-lockfile:
	uv venv && source .venv/bin/activate && uv pip install -e ".[development]" -r pyproject.toml && \
	uv pip freeze | grep -v infernet_ml > requirements.lock && rm -rf .venv

