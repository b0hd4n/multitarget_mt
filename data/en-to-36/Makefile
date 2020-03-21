SHELL=bash
SCRIPTDIR=../../scripts
.PHONY: datasets, test, train, raw_train, vocab, dev, raw_dev, wals

.username:
	echo Username for dataset download:;\
	read USERNAME;\
	echo $${USERNAME} ;\
	echo $${USERNAME} > .username;\

.url:
	echo Dataset url:;\
	read URL;\
	echo $${URL} ;\
	echo $${URL} > .url;\

username := $(firstword $(shell cat .username))
url := $(firstword $(shell cat .url))

test_username: .username
	x=$(username); echo $$x you

datasets: train dev test

train: processed/train.src processed/train.tgt
processed/train.%: 
	mkdir -p processed
	PYTHONIOENCODING=utf-8 ${SCRIPTDIR}/ignore_lines.py \
		--lines=interim/overlap_test_in_train \
		--source=raw/train/corpus.multi.bpe.$* \
		> processed/train.$* \
	|| rm -f processed/train.$*
interim/overlap_test_in_train.1:
	mkdir -p interim
	cat $$(find ./raw/test/ -name '*.bpe.en') | ${SCRIPTDIR}/mark_known_sentences \
		--preproc=droptags,lc,digits raw/train/corpus.multi.bpe.src > interim/overlap_test_in_train.1
interim/overlap_test_in_train: interim/overlap_test_in_train.1
	tail -n +2 interim/overlap_test_in_train.1 | sort | uniq | cut -f1 | uniq | sort -n \
		> interim/overlap_test_in_train
raw_train: raw/train/corpus.multi.bpe.src, raw/train/corpus.multi.bpe.tgt
raw/train/corpus.multi.bpe.src raw/train/corpus.multi.bpe.tgt: .username
	mkdir -p raw/train && cd raw/train && wget --user=$(username) --ask-password -c \
		$(url)/uedin-models/en-to-36/exp01/corpus.multi.bpe.src
		$(url)/uedin-models/en-to-36/exp01/corpus.multi.bpe.tgt
raw/train/corpus.multi.bpe.tgt.json raw/train/corpus.multi.bpe.src.json: .username
	mkdir -p raw/train && cd raw/train && wget --user=$(username) --ask-password -c \
		$(url)/uedin-models/en-to-36/exp01/corpus.multi.bpe.tgt.json \
		$(url)/uedin-models/en-to-36/exp01/corpus.multi.bpe.src.json


dev: processed/dev.src processed/dev.tgt
processed/dev.%: raw_dev
	mkdir -p processed
	ln -fs ../raw/dev/dev.sampled-trunc.multi.bpe.$* processed/dev.$*
raw_dev: raw/dev/dev.sampled-trunc.multi.bpe.tgt raw/dev/dev.sampled-trunc.multi.bpe.src
raw/dev/dev.sampled-trunc.multi.bpe.%: .username
	mkdir -p raw/dev
	cd raw/dev && wget --user=$(username) --ask-password -c \
		$(url)/uedin-models/en-to-36/exp01/dev.sampled-trunc.multi.bpe.src \
		$(url)/uedin-models/en-to-36/exp01/dev.sampled-trunc.multi.bpe.tgt


vocab: raw/vocab/vocab.multi.yml
raw/vocab/vocab.multi.yml: .username
	mkdir -p raw/vocab && cd raw/vocab && wget --user=$(username) --ask-password \
		$(url)/uedin-models/en-to-36/exp01/vocab.multi.yml

test: raw/test/.test
	ln -fs ../raw/test processed/test
raw/test/.test: .username
	mkdir -p raw/test && cd raw/test && wget --user=$(username) --ask-password -r --no-parent -l 7 -L -nH -R '*.html*' -e robots=off \
		$(url)/uedin-models/en-to-36/data01/test/ \
		&& mv elitr/uedin-models/en-to-36/data01/test/* ./ \
		&& rm -r elitr \
		&& touch .test


wals: wals/

raw_wals: raw/wals/wals_dataset.cldf.zip raw/wals/wals_language.csv.zip

raw/wals/wals_dataset.cldf.zip:
	mkdir -p raw/wals
	cd raw/wals && wget https://cdstar.shh.mpg.de/bitstreams/EAEA0-7269-77E5-3E10-0/wals_dataset.cldf.zip

raw/wals/wals_language.csv.zip:
	mkdir -p raw/wals
	cd raw/wals && wget https://cdstar.shh.mpg.de/bitstreams/EAEA0-7269-77E5-3E10-0/wals_language.csv.zip


