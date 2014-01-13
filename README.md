# Generate Completions
---
A [Sublime Text](http://www.sublimetext.com) plugin by Chris Brough

![Screeenshot](https://github.com/ChrisBrough/sublime_generate_completions/blob/master/images/screenshot.png?raw=true)

## Summary
---
This plugin generates Sublime Text completions for functions in source files. Given a _regex_ pattern, the plugin will search and retrieve matching functions with paramaters and returns. The results are output to a `.sublime-completions` file with placeholders for paramaters, (e.g., `${1:string:name}` to `TestFunc([string:name])`).

### Command Palatte
---
- `Generate Complations:Clear` - clears `path/to/packages/User/generate_completions`
- `Generate Complations:Update` - updates `path/to/packages/User/generate_completions`

## Installation
---
- `cd path/to/packages`
- `git clone https://github.com/ChrisBrough/sublime_generate_completions.git GenerateCompletions`

## TODO
---
- test on Sublime Text 2
- [**package control**](https://sublime.wbond.net) support
- auto generate completions
- optimize
- enable/disable completion sets
- completion prediction
- thread update

## License
---
- MIT, see LICENSE
