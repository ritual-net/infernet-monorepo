# rust development
CHDIR := cd libraries/$$library

rdev:
	@eval "$$get_library"; \
	if [ -n "$(fresh)" ]; then flag="-r"; else flag="-r --skip-install"; fi; \
	$(CHDIR) && eval "maturin develop --uv $$flag"

rust-binding-prereqs:
	# on ubuntu, libssl-dev is required for maturin
	if which apt-get; then \
		sudo apt-get install -y libssl-dev; \
	fi
