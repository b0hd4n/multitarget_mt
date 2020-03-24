#!/usr/bin/env python3

import os
import argparse
import copy
import time

import wandb
import yaml


def main():
    args = parse_args()
    init_wandb(args)
    wandb.log({'value': 0.1, 'b': 0.04}, step=150)
    wandb.log({'value': 0.2, }, step=160)
    wandb.log({'value': 0.3, }, step=170)
    wandb.log({'value': 0.4, 'b': 0.02}, step=180)


def parse_args():
    parser = argparse.ArgumentParser(description='Weights and Biases runner')
    parser.add_argument(
        '--experiment-dir', '-d',
        type=str,
        help='Folder with experiment',
    )
    parser.add_argument(
        '--project-name',
        default='multitarget-mt',
        help='Project name to save at wandb',
    )
    parser.add_argument(
        '--run-name',
        default=None,
        help='Project name to save at wandb',
    )
    parser.add_argument(
        '--tags', '-t',
        type=lambda s: s.split(','),
        default=[],
        help='Tag of the experiment: e.g. random, mono, wals, etc.'
    )

    args = parser.parse_args()
    return args


def init_wandb(args):
    config = get_config(args.experiment_dir)
    run_id = get_run_id(args.experiment_dir)
    run_name = os.path.basename(os.path.normpath(args.experiment_dir))
    wandb.init(
        project=args.project_name,
        name=run_name,
        resume=run_id,
        dir=args.experiment_dir,
        tags=args.tags,
        config=config,
    )
    save_run_id(args.experiment_dir)


def get_run_id(experiment_dir):
    try:
        with open(os.path.join(experiment_dir, '.run_id')) as f:
            run_id = f.readline()
        return run_id
    except FileNotFoundError:
        return False


def save_run_id(experiment_dir):
    with open(os.path.join(experiment_dir, '.run_id'), 'w') as f:
        f.write(str(wandb.run.id))


def get_config(path):
    config_path = os.path.join(path, 'model.npz.yml')
    config = get_config_when_created(config_path)
    config = filter_config(config)
    config = fix_config_values(config)
    #config = set_languages(config, path)

    return config


def get_config_when_created(path):
    config = read_when_created(path, yaml.safe_load)
    return config


def filter_config(config):
    ignored_keys = {
        'log-level', 'quiet', 'quiet-translation',
        'train-sets', 'vocabs', 'overwrite', 'no-reload',
        'keep-best', 'valid-sets', 'log', 'valid-log',
        'relative-paths', 'model', 'ignore-model-config',
    }

    filtered_config = {
        key: value
        for key, value
        in config.items()
        if key not in ignored_keys
    }

    return filtered_config


def fix_config_values(config):
    # change devices enumeration to device number
    fixed_config = copy.deepcopy(config)
    fixed_config['devices'] = len(fixed_config['devices'])
    # save only version, drop hash and compile date
    fixed_config['version'] = fixed_config['version'].split()[0]

    return fixed_config


def set_languages(config, path):
    model_folder = os.path.basename(os.path.normpath(path))
    ls = model_folder.split('2')[-1]
    languages = [ls[i:i + 2] for i in range(0, len(ls), 2)]
    
    new_config = copy.deepcopy(config)

    new_config['languages'] = languages
    new_config['n_languages'] = len(languages)
    return new_config


def read_when_created(path, fn, mode='r', wait=2, stop=None):
    if stop is None:
        stop = lambda: False
    while not stop():
        try:
            with open(path, mode) as f:
                return fn(f)
        except FileNotFoundError:
            time.sleep(wait)
            continue

def follow(thefile, stop=None):
    if stop is None:
        stop = lambda: False
    thefile.seek(0, os.SEEK_END) # End-of-file
    while True:
	line = thefile.readline()
	if not line:
	    time.sleep(0.1)
            # read till the end but do not wait if stop() fired
	    if stop(): break
            else: continue
	yield line

class LogParser:
    def __init__(self, experiment_dir):
        self.experiment_dir = experiment_dir
        self._state_path = os.path.join(self.experiment_dir, '.parser_state')
        self.read_last_log_state()
        self.setup_gracefull_interruptor()

    def read_last_log_state(self):
        try:
            with open(self._state_path) as sp:
                self._state = json.load(sp)
        except FileNotFoundError:
            self._state = {
                'valid_log_line': 0,
                'train_log_line': 0,
            }
            self.save_parser_state()
                
    def save_parser_state(self):
        with open(self._state_path, 'w') as sp:
            print('saving parser state: ', selt._state)
            json.dump(self._state, self._state_path)

    def setup_gracefull_interruptor(self):
        # by https://stackoverflow.com/a/31464349
        self.should_be_stopped = False
        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGTERM, self.stop)

    def stop(self, signum, frame):
        self.should_be_stopped = True

    def main_loop(self):
        while not self.should_be_stopped:
            read_when_created(
                self.train_log_path,
                fn=lambda f: self._process_train_log_file(f),
                stop=lambda: self.should_be_stopped,
            )

    def _process_train_log_file(self, train_log_file):
        def extract_time(log_line):
            '''[dtime] remaining log line'''
            dtime = datetime.strptime(log_line[1:20], "%Y-%m-%d %H:%M:%s")
            return dtime, log_line[22:]

        def extract_is_validation(log_line):
            '''
            [valid] remaining_line -> True, remaining_line
            log_line -> False, log_line
            '''
            validation = '[valid]'
            if log_line[:len(validation)] == validation:
                return True, log_line[len(validation)+2]
            else return False, log_line

        for line in follow(train_log_file):
            dtime, line = extract_time(line)
            is_validation, line = extract_is_validation(line)
            
            # parse train
            # if validation - parse validation
            # if trainslation - pass generator into the function to extract more log lines at once
            # and return wandb.Table (or dict?)

    


if __name__=='__main__':
    main()
