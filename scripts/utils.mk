specs:
	@python libraries/infernet_ml/src/infernet_ml/utils/spec.py

DOCKER := docker
ifeq ($(shell uname -s),Darwin)
    DOCKER := docker
    PLATFORM := linux/arm64
else
    DOCKER := docker
    PLATFORM := linux/amd64
endif

update-lockfile:
	@requirements_path=`find . -maxdepth 4 | grep "requirements.*.txt" | fzf`; \
	if [ -z "$$requirements_path" ]; then \
		echo "No requirements file selected"; \
		exit 1; \
	fi; \
	requirements_path=`echo $$requirements_path | xargs realpath`; \
	rm -rf temp_lock; \
	mkdir -p temp_lock; \
	cp $$requirements_path temp_lock/; \
	lockfile_path=`echo $$requirements_path | sed 's/.txt/.lock/'`; \
	index_url=`make get-index-url`; \
	cd temp_lock; \
	uv venv -p 3.11 && source .venv/bin/activate; \
	uv pip install -r $$requirements_path --extra-index-url $$index_url; \
	uv pip freeze | grep -v "file://" > "$$lockfile_path"; \
	rm -rf ../temp_lock; \
	echo "✅ Updated lockfile at $$lockfile_path"
