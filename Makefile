run:
	python -m bar.main --config ./example-stylix-dev.yaml

debug-run:
	GTK_DEBUG=interactive python -m bar.main --config ./example-stylix-dev.yaml
