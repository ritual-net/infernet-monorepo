update-lockfile:
	uv venv -p 3.11 && source .venv/bin/activate && \
	uv pip install -r pyproject.toml && \
	uv pip freeze | grep -v infernet_cli > requirements.lock && rm -rf .venv
