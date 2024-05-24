update-lockfile:
	uv venv && source .venv/bin/activate && \
	uv pip install -r pyproject.toml && \
	uv pip freeze | grep -v ritual_pyarweave > requirements.lock && rm -rf .venv
