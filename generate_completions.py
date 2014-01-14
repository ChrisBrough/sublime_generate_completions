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
            self.update()
        elif mode == 'clear':
            self.clear()
        elif mode == 'comment':
            self.comment(edit)

    def update(self):
        packages_path = sublime.packages_path()
        plugin_path = os.path.join(packages_path, 'GenerateCompletions/generate_completions.json')

        with open(plugin_path, 'r') as config_fd:
            config_data = json.load(config_fd)

            for config_entry in config_data:
                name = config_entry.get('name') or 'generate_completions'
                scope = config_entry.get('scope') or 'source.cpp'
                destination = os.path.join(self.generate_completions_path, config_entry.get('destination'))
                pattern = config_entry.get('extract_regex')
                comment_param_regex = config_entry.get('comment_param_regex') or ''
                comment_tparam_regex = config_entry.get('comment_tparam_regex') or ''
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
                                    returns, params = extract_func_metadata_from_comment(comment_param_regex, comment_tparam_regex, prev_lines)

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

    def clear(self):
        def answer_callback(index):
            if index == 1:
                shutil.rmtree(self.generate_completions_path)

        items = [['Cancel', 'Keep: ' + self.generate_completions_path], ['Confirm', 'Remove: ' + self.generate_completions_path]]
        sublime.set_timeout(lambda: self.window.show_quick_panel(items, answer_callback), 0)

    def comment(self, edit):
        selection = self.view.sel()
        if (len(selection) > 0):
            comment_lang = '--'
            comment_hr = comment_lang + ' ' + ('-' * 78) + ' ' + comment_lang + '\n'
            comment_brief = comment_lang + ' @brief\n' + comment_lang + '\n'
            comment_return = comment_lang + '\n' + comment_lang + ' @return\n'
            for region in selection:
                if region.empty():
                    line = self.view.line(region)
                    line_contents = self.view.substr(line)

                    params = extract_func_metadata_from_func(line_contents)

                    comment_params = ''
                    comment_params = comment_params.join([comment_lang + ' @param ' + param + '\n' for param in params])
                    print(params)
                    print(comment_params)
                    comment_block = comment_hr + comment_brief + comment_params + comment_return + comment_hr

                    self.view.insert(edit, line.begin(), comment_block)

def extract_func_metadata_from_comment(comment_param_regex, comment_tparam_regex, comments_string):
    returns = []
    params = []

    regex_param_pattern = re.compile(comment_param_regex)
    regex_tparam_pattern = re.compile(comment_tparam_regex)

    prev_name = ''
    for line in comments_string:
        for match in regex_param_pattern.findall(line):
            if len(match) == 2:
                name = match[1].split('.', 1)
                if len(name) == 2 and name[0] == prev_name:
                    params[-1] += str('(' + match[0] + ':' + name[1] + ')')
                else:
                    params += [match[0] + ':' + match[1]]
                prev_name = name[0]
        for match in regex_tparam_pattern.findall(line):
            if len(match) == 2:
                params += [match[0] + ':' + match[1]]
                prev_name = match[1]

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
