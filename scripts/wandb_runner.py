#!/usr/bin/env python3

import os
import argparse
import copy
import time
import json
import signal
import types
from datetime import datetime
from contextlib import contextmanager

import wandb
import yaml


def main():
    args = parse_args()
    init_wandb(args)
    log_parser = LogParser(args.experiment_dir, wait_for_new_lines=args.wait_for_logs)
    for step, log_data in log_parser.main_loop():
        wandb.log(log_data, step=step)

    print('Parser stopped')
    save_best_models(args.experiment_dir)


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
    parser.add_argument(
        '--infer-language-tags', '-l',
        action='store_const',
        const=True,
        default=False,
        help='Infer languages from model name, save as tags'
    )
    parser.add_argument(
        '--wait-for-logs', '-w',
        action='store_const',
        const=True,
        default=False,
        help='Wait for new lines in logs (use during the training)'
    )

    args = parser.parse_args()
    return args


def init_wandb(args):
    config = get_config(args.experiment_dir)
    run_id = get_run_id(args.experiment_dir)
    run_name = os.path.basename(os.path.normpath(args.experiment_dir))
    language_tags = get_language_tags(args)
    tags = args.tags + language_tags
    config = add_language_info(config, language_tags)
    wandb.init(
        project=args.project_name,
        name=run_name,
        resume=run_id,
        dir=args.experiment_dir,
        tags=tags,
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


def get_language_tags(args):
    if args.infer_language_tags:
        return extract_langs(args.experiment_dir)
    else:
        return []


def extract_langs(experiment_dir):
    """ model_en2fres -> source:en, target:fr, target:es """
    useful_part = os.path.basename(os.path.normpath(experiment_dir)).split('_')[-1]
    source, target = useful_part.split('2')
    get_langs = lambda ls: [ls[i:i + 2] for i in range(0, len(ls), 2)]
    source_tags = ['source:'+tag for tag in get_langs(source)]
    target_tags = ['target:'+tag for tag in get_langs(target)]
    n_tags = [
        'n_sources:'+str(len(source_tags)),
        'n_targets:'+str(len(target_tags)),
    ]

    return source_tags + target_tags + n_tags


def add_language_info(config, language_tags):
    new_config = copy.deepcopy(config)
    n_targets = sum('target:' in tag for tag in language_tags)
    new_config['n_targets'] = n_targets if n_targets else None

    return new_config


def get_config(path):
    config_path = os.path.join(path, 'model.npz.yml')
    config = get_config_when_created(config_path)
    config = filter_config(config)
    config = fix_config_values(config)
    #config = set_languages(config, path)

    return config


def get_config_when_created(path):
    def safe_load(f):
        time.sleep(2)
        return yaml.safe_load(f)

    config = read_when_created(path, safe_load, wait=10)
    print(config)
    return config


def filter_config(config):
    ignored_keys = {
        'log-level', 'quiet', 'quiet-translation',
        'train-sets', 'vocabs', 'overwrite', 'no-reload',
        'keep-best', 'valid-sets', 'log', 'valid-log',
        'relative-paths', 'model', 'ignore-model-config',
        'valid-script-path', 'tempdir',
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
    if 'version' in fixed_config:
        # sometimes the last line with the version is not
        # in the config immediately, but it is not an important
        # value to be stored
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
            break
        except FileNotFoundError:
            time.sleep(wait)
            continue

def follow(thefile, stop=None):
    if stop is None:
        stop = lambda: False
    while True:
        line = thefile.readline()
        if not line:
            time.sleep(0.1)
            # read till the end but do not wait if stop() fired
            if stop(): break
            else: continue
        yield line



def save_best_models(experiment_dir):
    print('Saving models... ', end='')
    wandb.save(os.path.join(experiment_dir, 'model.npz.best-*'))
    wandb.save(os.path.join(experiment_dir, '*.log'))
    wandb.save(os.path.join(experiment_dir, 'model.npz.yml'))
    print('Done.')


class LogParser:
    def __init__(self, experiment_dir, wait_for_new_lines=False):
        self.experiment_dir = experiment_dir
        self.train_log_path = os.path.join(self.experiment_dir, 'train.log')
        self.wait_for_new_lines = wait_for_new_lines
        self.should_be_stopped = False

    def stop(self, signum, frame):
        print('Stopping log parser...')
        self.should_be_stopped = True

    def main_loop(self):
        """yields (step, log_dict)"""
        with signal_handler(signal.SIGINT, self.stop),\
             signal_handler(signal.SIGTERM, self.stop):
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
            if 'lang/' not in metric_name:
                metric_name = 'valid/' + metric_name
            log_data[metric_name] = metric_value

            metric_stalled = line[4].strip()
            if 'no effect' not in metric_stalled:
                if 'stalled' in metric_stalled:
                    metric_stalled = int(metric_stalled.split()[1])
                else:
                    metric_stalled = 0
                log_data[metric_name+'_stalled'] = metric_stalled

            return step, log_data

        def parse_translation(lines):
            data = []
            log_data = {}
            for line in lines:
                if translation_ends(line):
                    log_data['valid/translation_time'] = float(line.strip().split(' ')[-1][:-1])
                    break
                if not 'Best translation' in line:
                    return None
                # cut time
                line = line[line.find(']')+1:]
                colon = line.find(':')
                n = line[:colon]
                translation = line[colon+1:]
                n = int(n.strip().split(' ')[-1])
                translation = translation.strip()
                data.append([n, translation])
            log_data['valid/translation_example'] = wandb.Table(
                    data=data, columns=["N","Translation"]
            )

            return log_data

        def training_finished(line):
            return "Training finished" in line

        def translation_begins(line):
            return "Translating" in line

        def translation_ends(line):
            return "Total translation time" in line

        last_step=0
        lines = follow(
            train_log_file,
            stop=lambda: self.should_be_stopped or not self.wait_for_new_lines
        )
        for line in lines:

            try:
                dtime, line = extract_time(line)
            except:
                continue

            if training_finished(line):
                break

            is_validation, line = extract_is_validation(line)
            
            if is_validation:
                step, log_data = parse_val_log(line)
            elif is_training_log(line):
                step, log_data = parse_train_log(line)
            elif translation_begins(line):
                # pass generator here to consume all lines with translations
                log_data = parse_translation(lines)
                # translation does not have 'step', that is why there is this 'last_step' thing
                step = last_step
            else:
                continue

            last_step = step

            yield step, log_data


@contextmanager
def signal_handler(handled_signal, new_handler):
    old_handler = signal.getsignal(handled_signal)
    try:
        signal.signal(handled_signal, new_handler)
        yield
    finally:
        signal.signal(handled_signal, old_handler)

    
if __name__=='__main__':
    main()
