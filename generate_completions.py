# -------------------------------------------------------------------------------- #
# ~~~> [Generate Completions] <~~~
# @author Chris Brough
# @date 2014
# @license MIT
# -------------------------------------------------------------------------------- #

import sublime
import sublime_plugin
import codecs
import glob
import json
import os
import re
import shutil

PREV_LINES = 8
VERBOSE = False

class GenerateCompletionsCommand(sublime_plugin.TextCommand):
    def run(self, edit, mode):
        self.window = self.view.window()
        self.generate_completions_path = os.path.join(sublime.packages_path(), 'User/generate_completions')

        if mode == 'update':
            self.generate_completions_update()
        elif mode == 'clear':
            self.generate_completions_clear()

    def generate_completions_update(self):
        packages_path = sublime.packages_path()
        plugin_path = os.path.join(packages_path, 'GenerateCompletions/generate_completions.json')

        with open(plugin_path, 'r') as config_fd:
            config_data = json.load(config_fd)

            for config_entry in config_data:
                name = config_entry.get('name') or 'generate_completions'
                scope = config_entry.get('scope') or 'source.cpp'
                destination = os.path.join(self.generate_completions_path, config_entry.get('destination'))
                pattern = config_entry.get('extract_regex')
                comment_regex = config_entry.get('comment_regex') or '[/\\*]*'
                single_file = config_entry.get('single_file')
                parse_func_params = config_entry.get('parse_func_params')
                file_names = []

                print(']---[[ extract completions - ' + name + ' ]]---[')

                for file_path in config_entry['files']:
                    file_names += glob.glob(file_path)

                completion_data = {}
                completion_data['scope'] = scope
                completion_data['completions'] = []

                for file_name in file_names:
                    if VERBOSE:
                        print('extracting completion from:\n\t> ' + file_name)

                    if not single_file:
                        completion_data['completions'] = []

                    with codecs.open(file_name, 'r', 'utf-8') as source_code_fp:
                        regex_pattern = re.compile(pattern)
                        completions = completion_data['completions']
                        prev_lines = [''] * PREV_LINES

                        for line in source_code_fp:
                            prev_lines.pop(0)
                            prev_lines.append(line)
                            matches = regex_pattern.findall(line)

                            if matches:
                                for match in matches:
                                    returns, params = extract_func_metadata_from_comment(comment_regex, prev_lines)

                                    if not params and parse_func_params:
                                        params = extract_func_metadata_from_func(line)

                                    entry = {}
                                    entry['trigger'] = match
                                    entry['contents'] = match + '(' + generate_params_snippets(params) + ')$0'

                                    completions.append(entry)

                        if not single_file:
                            write_completions_to_file(destination, file_name, completion_data)

                if single_file:
                    write_completions_to_file(destination, name, completion_data)

    def generate_completions_clear(self):
        def answer_callback(index):
            if index == 1:
                shutil.rmtree(self.generate_completions_path)

        items = [['Cancel', 'Keep: ' + self.generate_completions_path], ['Confirm', 'Remove: ' + self.generate_completions_path]]
        sublime.set_timeout(lambda: self.window.show_quick_panel(items, answer_callback), 0)

def extract_func_metadata_from_comment(comment_regex, comments_string):
    returns = []
    params = []

    regex_prefix = comment_regex + r'[\s]*'
    regex_postfix = r'\s*([a-zA-Z0-9:]*)'

    regex_return_pattern = re.compile(regex_prefix + r'@return{1}' + regex_postfix)
    regex_param_pattern = re.compile(regex_prefix + r'@param{1}' + regex_postfix)

    for line in comments_string:
        returns += regex_return_pattern.findall(line)
        params += regex_param_pattern.findall(line)

    return returns, params

def extract_func_metadata_from_func(function_string):
    params = []

    function_string = re.findall(r'\({1}(.*)\){1}', function_string)[0] or ''
    regex_param = r'\(?\s*([a-zA-Z0-9_]+)\s*,?'
    regex_param_pattern = re.compile(regex_param)
    params = regex_param_pattern.findall(function_string)

    return params

def generate_params_snippets(params):
    params_count = 1
    params_string = ''

    for param in params:
        params_string += '${' + str(params_count) + ':[' + param + ']}, '
        params_count += 1

    return params_string[0:-2]

def write_completions_to_file(destination, file_name, data):
    if not os.path.exists(destination):
        os.makedirs(destination)

    file_name = re.sub(r'[/\\]', '%', file_name)
    path = os.path.join(destination, file_name + '.sublime-completions')

    if VERBOSE:
        print('writing completion to:\n\t> ' + path)

    with open(path, 'w') as fp:
        json.dump(data, fp)
