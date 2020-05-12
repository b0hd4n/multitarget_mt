SHELL := /bin/bash

%/model.npz.best-translation.npz: %/.run_id
	wget -P $* https://api.wandb.ai/files/b0hd4n/multitarget-mt/$$(cat $*/.run_id)/model.npz.best-translation.npz \
		&& touch $@

%/model.npz.best-ce-mean-words.npz: %/.run_id
	wget -P $* https://api.wandb.ai/files/b0hd4n/multitarget-mt/$$(cat $*/.run_id)/model.npz.best-ce-mean-words.npz \
		&& touch $@

en2%: model_en2%/model.npz.best-ce-mean-words.npz model_en2%/model.npz.best-translation.npz
	echo $@

test_env: test_env/bin/activate
test_env/bin/activate:
	python3 -m venv test_env; \
	source test_env/bin/activate; \
	pip install wheel websocket websocket_client
