update-lockfile:
	uv venv -p 3.11 && source .venv/bin/activate && \
	uv pip install -U -r pyproject.toml && \
	uv pip install -e ".[development]" -r pyproject.toml && \
	uv pip install -e ".[torch_inference]" -r pyproject.toml && \
	uv pip install -e ".[onnx_inference]" -r pyproject.toml && \
	uv pip install -e ".[tgi_inference]" -r pyproject.toml && \
	uv pip install -e ".[css_inference]" -r pyproject.toml && \
	uv pip install -e ".[bark_inference]" -r pyproject.toml && \
	uv pip freeze | grep -v infernet_ml > requirements.lock && rm -rf .venv
