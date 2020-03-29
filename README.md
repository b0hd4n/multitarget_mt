# multitarget_mt

## Description
Discovering how the amount of target languages in one multi-target machine translation model and their relatedness/similarity affects the quality of translation.

## Technologies
[marian-nmt](https://marian-nmt.github.io/) was used for training models. Scripts expect to be run 
at computational cluster with [SGE](https://en.wikipedia.org/wiki/Oracle_Grid_Engine) grid engine; 
the presence of cpu*.q queue for CPU jobs 
and gpu*.q queue for GPU jobs is expected. [Weights and Biases](wandb.ai) is used for training process and 
results visualization.

## Visualization
For every run and experiment the metrics (todo: and test results) are collected [here](https://app.wandb.ai/b0hd4n/multitarget-mt?workspace=user-b0hd4n)

## Data
[OPUS corpus](https://elitr.eu/wp-content/uploads/2019/07/D11.FINAL_.pdf). 
Due to the later found [overlap](https://elitr.eu/wp-content/uploads/2019/11/D12.FINAL_.pdf) 
of source sentences in test and train data, the train data were filtered. As a result, 
no source sentence from any test set can be found it the training set.
