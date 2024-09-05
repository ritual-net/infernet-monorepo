update-lockfile:
	uv venv -p 3.11 && source .venv/bin/activate && \
	uv pip install -e ".[development]" -r pyproject.toml && \
	uv pip freeze | grep -v infernet_client > requirements.lock && rm -rf .venv
