#!/usr/bin/env python3

import os
import argparse
import copy
import time
import json
import signal
import types
from datetime import datetime

import wandb
import yaml


def main():
    args = parse_args()
    init_wandb(args)
    log_parser = LogParser(args.experiment_dir)
    for step, log_data in log_parser.main_loop():
        wandb.log(log_data, step=step)


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
    # TODO: add --infere-languages parameter
    #config = set_languages(config, path)

    return config


def get_config_when_created(path):
    config = read_when_created(path, yaml.safe_load)
    print(config)
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
            with open(path, mode, encoding='utf-8') as f:
                return fn(f)
        except FileNotFoundError:
            time.sleep(wait)
            continue

def read_when_created_gen(path, fn, mode='r', wait=5, stop=None):
    if stop is None:
        stop = lambda: False
    while not stop():
        try:
            with open(path, mode, encoding='utf-8') as f:
                yield from fn(f)
        except FileNotFoundError:
            time.sleep(wait)
            continue

def follow(thefile, stop=None):
    if stop is None:
        stop = lambda: False
    #thefile.seek(0, os.SEEK_END) # End-of-file
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
        self.train_log_path = os.path.join(self.experiment_dir, 'train.log')
        self._state_path = os.path.join(self.experiment_dir, '.parser_state')
        self.read_last_log_state()
        self.setup_gracefull_interruptor()

    def read_last_log_state(self):
        # TODO: remove
        try:
            with open(self._state_path) as sp:
                self._state = json.load(sp)
        except:
            self._state = {
                'valid_log_line': 0,
                'train_log_line': 0,
            }
            self.save_parser_state()
                
    def save_parser_state(self):
        with open(self._state_path, 'w') as sp:
            print('saving parser state: ', self._state)
            json.dump(self._state, sp)

    # TODO: wandb itself interrupts interruption handling - remove?
    def setup_gracefull_interruptor(self):
        # by https://stackoverflow.com/a/31464349
        self.should_be_stopped = False
        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGTERM, self.stop)

    def stop(self, signum, frame):
        print('Stopping log parser...')
        self.should_be_stopped = True

    def main_loop(self):
        """yields (step, log_dict)"""

        while not self.should_be_stopped:
            yield from read_when_created_gen(
                self.train_log_path,
                fn=lambda f: self._process_train_log_file(f),
                stop=lambda: self.should_be_stopped,
            )

    def _process_train_log_file(self, train_log_file):
        # TODO: refactor this monster
        def extract_time(log_line):
            '''[dtime] remaining log line'''
            dtime = datetime.strptime(log_line[1:20], "%Y-%m-%d %H:%M:%S")
            return dtime, log_line[22:]

        def extract_is_validation(log_line):
            '''
            [valid] remaining_line -> True, remaining_line
            log_line -> False, log_line
            '''
            validation = '[valid]'
            if log_line[:len(validation)] == validation:
                return True, log_line[len(validation):]
            else: return False, log_line

        def is_training_log(log_line):
            return log_line.find('Ep. ') >= 0

        def parse_train_log(line):
            """ Ep. 2 : Up. 1000 : Sen. 311,824 : Cost 4.95877838 : Time 163.05s : 33655.40 words/s : L.r. 1.0000e-04 """
            processing = {
                "Ep.": lambda s: ('train/epoch', int(s)),
                "Up.": lambda s: ('step', int(s)),
                "Sen.": lambda s: ('train/sentences', int(s.replace(',',''))),
                "Cost": lambda s: ('train/loss', float(s)),
                "Time": lambda s: ('train/time', float(s[:-1])),
                "words/s": lambda s: ('train/speed', float(s)),
                "L.r.": lambda s: ('train/learning_rate', float(s)),
            }
            def process(log_line_chunk):
                first, second = log_line_chunk.strip().split(' ')
                try:
                    return processing[first](second)
                except KeyError:
                    try:
                        return processing[second](first)
                    except KeyError:
                        return None
            log_data = dict(
                process(info_chunk)
                for info_chunk
                in line.split(':')
                if info_chunk is not None
            )
            step = log_data['step']
            del log_data['step']
            return step, log_data

        def parse_val_log(line):
            """ Ep. 26 : Up. 35000 : ce-mean-words : 1.63575 : new best """
            line = line.split(':')
            step = int(line[1].strip().split(' ')[1])
            log_data = {}
            metric_name = line[2].strip()
            metric_value = float(line[3].strip())
            log_data['valid/'+metric_name] = metric_value

            metric_stalled = line[4].strip()
            if 'no effect' not in metric_stalled:
                if 'stalled' in metric_stalled:
                    metric_stalled = metric_stalled.split()[1]
                else:
                    metric_stalled = 0
                log_data['valid/'+metric_name+'_stalled'] = metric_stalled

            return step, log_data

        for line in follow(train_log_file):
            dtime, line = extract_time(line)
            is_validation, line = extract_is_validation(line)
            
            if is_validation:
                yield parse_val_log(line)
            elif is_training_log(line):
                yield parse_train_log(line)

            # TODO
            # if trainslation - pass generator into the function to extract more log lines at once
            # and return wandb.Table (or dict?)

    


if __name__=='__main__':
    main()
