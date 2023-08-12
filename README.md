# Work faster and smarter with uPlaybook.

uPlaybook automates project/snippet setup  and system configuration tasks with easy playbooks you
can run from the commandline.  Using an Ansible-inspired YAML syntax to allow you to quickly and
securely set up configuration files, run commands, and create new projects or project components
from templates.  Think shell scripting, but with an emphasis on templating and secrets management.

Key Features:

- Simple Ansible-inspired YAML syntax for quick automation
- Built-in encryption - Secure sensitive data like passwords and keys
- Cross-platform - works on Linux, MacOS, and Windows
- Templating with Jinja2 for dynamic configurations
- Flexible templating - Customize with Jinja2 templates
- Arguments and prompts customize each run
- Friendly CLI - Run playbooks easily with intuitive commands and prompting 
- Minimal dependencies - just Python 3 and a couple libraries!

uPlaybook can do cookiecutter-like tasks: populating projects or running tasks, and
has prompts for filling in missing information, and a search path so that
project-specific playbooks or user-defined playbooks and templates can be used simply
from the command-line.  `up new-release --name 2023-08-09 ---patch`

While uPlaybook provides many shell-like commands ("tasks" in uPlaybook), it has the
benefit of a rich templating language to manipulate deployed files, and can also handle
encrypted files to keep your secrets and passwords safe.

My initial use case was much like what Ansible solves: a way to deploy control and
configuration files, including passwords and ssh keys, during new machine deployment.

## Requirements

- Python 3
- Python libraries: cryptography, jinja2, pyyaml

For example, on Ubuntu: apt install python3 python3-cryptography python3-yaml python3-jinja2

## Examples

From the "examples/encryptall/up.yml" example:

    ---
    - docs:
      desc: Encrypt all the managed files.
    - args:
      options:
        - name: password
          description: Password for the encrypted files.
        - name: remove
          type: bool
          default: true
          description: Whether to remove the unencrypted files when done.
    - block:
      tasks:
        - echo:
          msg: "Encrypting {{basename}}..."
        - copy:
          src: "{{basename}}"
          dst: "{{basename}}.fernet"
          encrypt_password: "{{password}}"
        - if:
          condition: "remove"
          tasks:
            - echo:
              msg: "...Removing {{basename}}"
            - rm:
              path: "{{basename}}"
      loop:
        - vars:
            basename: file1
        - vars:
            basename: file2
        - vars:
            basename: file3

The above playbook, if put in ".uplaybooks/encryptall/up.yml" can be run as:
`up encryptall --no-remove <PASSWORD>" to encrypt the listed files, and not remove
the source files.

See "examples" directory for more examples.

## Playbook Arguments

User-supplied arguments can be specified in an "args" section of the playbook.

This can then produce both command-line arguments the user can provide on the CLI, or
the questions can be prompted from the user (via the "--up-ask" CLI argument or the
"up_ask: true" variable in a "vars" section of the playbook.

For example:

```yaml
- vars:
  up-ask: true
- args:
  options:
    #  require the name of the role to create
    - name: role_name
      description: "The name of the role directory to create."
    #  Optionally, allow handlers to be disabled (default is true)
    - name: add_handlers
      default: true
      type: bool
      description: "Whether to add handlers to the role."
```

Given the above in a playbook called "makerole", here are some example runs:

    $ ./up makerole
    usage: up:makerole [-h] [--add-handlers | --no-add-handlers] role-name
    up:makerole: error: the following arguments are required: role-name
    $ ./up makerole foo   #  Create a role "foo" with handlers
    $ ./up makerole foo --no-add-handlers  #  And without

The "options" can contain elements with the following values:

- name (Required): The name of the argument, this is the name used to access the value in
  templating, so it must be a valid Python identifier (no hyphens, for example), and
  is the name of the argument.
- type (Optional): Type of the value, defaults to "str".  Can also be "bool" for true/false
  arguments.
- default (Optional): Gives a default value.  If a default is given, the argument is
  optional.  This means it can be specified using "--<NAME>", otherwise it is a
  positional argument and must always be supplied on the command line by position.
- description (Optional): A sentence or two description of the argument's purpose.

## Loops

uPlaybook supports looping, somewhat similar to Ansible.  However, the keys in the
loop are directly loaded into the task, overriding any same-named task arguments.  In
other words, you can specify defaults in the main play, and override them in the
loop, or provide other keys that can be used by templated values.

For example:

    - template:
      src: "{{ dst|basename }}.j2"
      loop:
        - dst: /etc/services
        - dst: /etc/hosts
        - dst: /etc/shadow
          decrypt_password: supersecret
        - dst: /etc/systemd/system/myservice.service
          src: systemd.conf.j2

The above:

- Makes the default "src" file be the basename of the destination ("services" in the
  first line) with ".j2" appended: "services.j2".
- The shadow entry is decrypted.
- The systemd entry specifies a different source location.

## Blocks

Blocks are a simple way of combining a set of tasks, for example if you wanted a
couple of tasks to run with a loop.

For example:

    - block;
      tasks:
        - copy:
          src: "{{basename}}"
          dst: "{{basename}}.fernet"
          encrypt_password: "{{password}}"
        - if:
          condition: remove
          tasks:
            - rm:
              path: "{{basename}}"
    loop:
      #  note: 2 indentations needed under vars
      #  (YAML treats "basename" as a peer of "vars" without 2 indentation levels)
      - vars:
          basename: file1
      - vars:
          basename: file2

## Task Vars

Tasks (including "if" and "block", etc..) can have "vars" on them which
create variables local to that task.  This is primarily useful for loops or blocks
(or blocks with loops).

For an example, see the example in the "Blocks" section above.

## Playbook Search Path

The playbook will be searched for using a search path, which can be specified
by the "UP\_PLAYBOOK\_PATH" environment variable.  The default search path is:
".:.uplaybooks:~/.config/uplaybook/books:~/.config/uplaybook" Each component of
the path is separated by a colon.

There are two types of playbooks: a file and a package.  A file playbook is
simply a YAML file which specifies the play.  A package is a directory with a
file "up.yml" inside it.  Files are better for simple, self-contained plays,
where a package can bundle up templates and other files into a single location.

To find a playbook "foo", each directory in the search path is consulted, looking for:

- User expansion is done if "~" or "~user" are in the path.
- "foo.yml" is a file.
- "foo" is a file.

## File and Template Search Path

To find files and templates uPlaybook uses the "UP\_FILE\_PATH" environment variable
(with a default of "...:.../files:.").  Each component is separated by a ":", and
"..." at the beginning of the file path refers to the directory that contains the
playbook file.

The default search path looks for templates/files in:

- The same directory as the playbook
- In a subdirectory (by the playbook) named "files".
- The current working directory.

## Debugging

If you set "up\_debug" to true, debugging information will be printed during the
playbook run.  It can also be enabled from the CLI by adding the "--up-debug" argument:
`up --up-debug playbook`.

Example:

    - vars:
      up_debug: true

## Available Tasks

### block

See the "Blocks" section above.

### cd

Change working directory.

Arguments:

- path: The directory to change to (template expanded).

Example:

    - cd:
      path: /tmp/foo

### chmod

Change the permissions on a filesystem path.

Arguments:

- mode: The mode for the file, either by numeric (0755), octal string ("755"), or symbolic
  string ("a=rx,u+w").  (templated)
- path: Path to the filesystem object to set permissions on.  (templated)
- recurse: Whether to recursively set permissions on the filesystem objects under
  `path` if it is a directory.  (optional)

  Example:

      - chmod:
        path: /tmp/foo
        mode: a=rX,u+w
        recurse: true

### copy

Copy a (possibly encrypted) file verbatim.

Arguments:

- src: Filename of the source file (template expanded).
- dst: Filename to copy the file to (template expanded).
- decrypt\_password: A password to decrypt "src" with when copying.
- encrypt\_password: A password to encrypt "src" with when copying.
- mode: A mode (as with `chmod`) the `dat` file is set to.
- skip: If "if\_exists" the copy will be skipped if the destination exists.
    Otherwise the copy will always be done.

Example:

    - copy:
      src: program.fernet
      dst: /usr/bin/program
      skip: if\_exists
      decrypt\_password: foobar

### docs

This is a "no-op" task that is used to document the playbook.  Adding a "desc"
argument uses the associated value when "up --help" is run to list the available
playbooks as a description of what the playbook does.

Arguments:

- desc: String describing what this playbook does.  Generally kept short, say 60
  characters.

Example:

    - docs:
      desc: "Create a new release script."

### echo

Write a message to stdout, or optionally to stderr.  If neither is specified, a
newline is printed to stdout.

Arguments:

- msg: String that is printed to the output.  (template expanded)
- stderr: String that is written to stderr.  (template expanded)

Example:

    - echo:
      msg: "The value of argname is '{{argname}}'"

### exit

Terminate the playbook, optionally specifying an exit code or message.

Arguments:

- code: Exit code, defaults to 0 (success).
- msg: String that is printed to the output.  (template expanded)
- stderr: String that is written to stderr.  (template expanded)

Example:

    - exit:
      code: 1
      stderr: "Failed to engage oscillation overthruster."

### if/elif/else

This introduces a conditional with further tasks that run if the condition is true.

Arguments:

- condition: A Python expression or a YAML true/false.  (template expanded)
- tasks: A list of further tasks to run if condition is true.

Example:

    - if:
      condition: "os.path.exists('foo')"
      tasks:
        - mkdir:
          path: foo
    - elif:
      condition: "os.path.exists('bar')"
      tasks:
        - mkdir:
          path: bar
    - else:
      tasks:
        - echo:
          msg: "Both directories exist"

### mkdir

Create a directory.  Will create intermediate directories if they do not exist.

Arguments:

- path: Directory to create (template expanded).
- skip: If "if\_exists" the mkdir will be skipped if the destination exists.
    Otherwise the mkdir will always be done.

Example:

    - mkdir:
      path: /tmp/foo

### pause

Stop execution for a time.  This can be either a number, or a string representing an
interval.  The interval can use the format "XdXhXmXs" with any of the components
being optional.  The specifier can be short or long ("s" or "sec" or "second(s)", and
there can be spaces between them.  It can also start or end with "random" to
randomize the number up to the specified time.  Examples: "1h", "1min 30s" "random
90", "5m random".

Arguments:

- time: The number of seconds to wait or an interval string.  (templated)

Example:

    - pause:
      time: 5

### rm

Remove a file or directory (if recursive is specified).

Arguments:

- path: Directory to create (template expanded).
- recursive: If "true" and "path" is a directory, all contents below it are removed.

Example:

    - rm:
      path: /tmp/foo
      recursive: true

### run

Run a shell command.

Arguments:

- command: A shell command to run (template expanded).
- register_exit: The name of a variable that will be set with the process exit code.
- register_stdout: The name of a variable that will be set with stdout of the run
  program.
- register_stderr: The name of a variable that will be set with the stderr of the run
  program.

Example:

    - run:
      command: "date"
      register_exit: date_exit_code

### stat

Run a stat on a filesystem path.  FileNotFound exception will be raised if it does
not exist.

Arguments:

- path: The path of the file to stat.   (template expanded)
- register: The name of a variable that will be set with the result.  (optional)
       This will be a python stat object:

    os.stat_result(st_mode=33188, st_ino=7876932, st_dev=234881026,
    st_nlink=1, st_uid=501, st_gid=501, st_size=264, st_atime=1297230295,
    st_mtime=1297230027, st_ctime=1297230027)

Example:

    - stat:
      path: "/etc/services"
      register: stat_result
    - echo:
      msg: "Owned by: {{stat_result.st_uid}}"

### template

Copy a file to "dst" with template expansion of the contents and encryption/decryption.

Arguments:

- src: Filename of the source file (template expanded).
- dst: Filename to copy the file to (template expanded).
- decrypt\_password: A password to decrypt "src" with when copying.
- encrypt\_password: A password to encrypt "src" with when copying.
- mode: A mode (as with `chmod`) the `dat` file is set to.
- skip: If "if\_exists" the copy will be skipped if the destination exists.
    Otherwise the copy will always be done.

Example:

    - template:
      src: config.j2
      dst: /etc/my/config
      skip: if\_exists
      decrypt\_password: foobar

### umask

Set the default file creation permission mask.

Arguments:

- mask: New mask to set, either as in integer or as a string which will be
  interpreted as octal.  (templated)
- register: Variable name to store old mask in.  (optional)

Example:

    - umask:
      mask: "077"
      register: old_umask

### vars

Set variables in the environment, for use in templating.

Arguments:

Takes a key/value list.

Example:

    - vars:
      key: value
      foo: "{{key}}"
      path: "{{environ['PATH']}}"

## Jinja/Conditions Environment

The environment that the Jinja2 templating and the "condition" clauses run in have
the following available:

- environ: a dictionary of the environment variables available, for example:
  "environ['HOME']".
- os: The Python "os" module, for things like "os.path.exists()" checks.
- platform: Platform-specific information, for things like the OS name and version:
  "os.system == 'Linux'" or "(os.release\_version) > 22"

## Platform Details

The following information is made available to conditions and templates in the
"platform" variable:

    Linux:
         arch: x86_64
         release_codename: jammy
         release_id: ubuntu
         os_family: debian
         release_name: Ubuntu
         release_version: 22.04
         system: Linux

    MacOS:
        arch: arm64
        release_version: 13.0.1
        system: Darwin

    Windows:
        arch: AMD64
        release_edition: ServerStandard
        release_name: 10
        release_version: 10.0.17763
        system: Windows

    All Platforms:
        cpu_count: Number of CPUs.
        fqdn: Fully qualified domain name of system ("foo.example.com").

    Memory information is available if the "psutil" python module is installed:
        memory_total: Total memory on system (in bytes)
        memory_available: Available memory
        memory_used: Memory used
        memory_percent_used: Percentage of memory used (39.5).

## Fernet Encryption

The Fernet encryption used here was chosen because it is implemented directly in the
Python cryptography module, and implements best practices for encryption.  I had
wanted to use the gnupg module but that relies on the "gpg" command-line tool which
was tricky under Windows.

The Fernet files are formatted as 16 raw bytes of salt, randomly chosen, and then the
encrypted data as produced by the Fernet routines. [More information on
Fernet](https://cryptography.io/en/latest/fernet/ "Python Cryptography Fernet Module").

## License

CC0 1.0 Universal, see LICENSE file for more information.

<!-- vim: ts=4 sw=4 ai et tw=85
-->
