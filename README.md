# uPlaybook -- An Ansible-Inspired Micro Playbook Runner

This is an extremely small, yaml-driven tool for doing simple file deployment and
templating sorts of tasks.  It only requires Python and a couple of libraries.

I implemented it primarily to deploy encrypted secrets and config files to a group
of Windows machines.  Python was available but Ansible failed to run.

While uPlaybook provides many shell-like commands ("tasks" in uPlaybook), it has the
benefit of a rich templating language to manipulate placed files, and can also
decrypt files that contain secrets.

My initial use case was much like what Ansible solves: a way to deploy control and
configuration files, including passwords and ssh keys, during new machine deployment.

## Features

- Templating (jinja2) of files, paths, and configuration values.
- Built in encryption/decryption (Fernet, via Python cryptography module)
- Ansible-inspired yaml configuration.
- Environment variables are brought into template namepsace.
- Helpers for fernet encrypt/decrypt.
- Good command-line argument handling.

## Requirements

- Python 3
- Python libraries: cryptography, jinja2, pyyaml

For example, on Ubuntu: apt install python3 python3-cryptography python3-yaml python3-jinja2

## Examples

Given a "exampleplaybook.yaml" that looks like this:

    ---
    #  Most values below can use jinja2 templating syntax
    - vars:
      #  pull the suffix from the environment $EXAMPLE_SUFFIX, or empty string if not set
      suffix: "{{environ['EXAMPLE_SUFFIX'] | default('')}}"
      destdir: "/tmp/foo{{suffix}}"
      password: foobar
    
    #  Remove directory
    - rm:
      path: "{{destdir}}"
      recursive: true
    #  List directory
    - run:
      command: "ls -ld {{destdir}}"
    #  Create directory
    - mkdir:
      path: "{{destdir}}"
      skip: if_exists
    #  Make multiple directories via "loop"
    - mkdir:
      loop:
        - path: "{{destdir}}/a"
        - path: "{{destdir}}/b"
        - path: "{{destdir}}/c"
    #  Copy an encrypted file
    - copy:
      src: foo.fernet
      dst: "{{destdir}}/bar"
      skip: if_exists
      decrypt_password: "{{password}}"
    #  Template a file to destination
    - template:
      src: foo.j2
      dst: "{{destdir}}/foo-templated"
      skip: if_exists
    #  Change to directory
    - cd:
      path: "{{destdir}}"
    - run:
      command: "ls -ld"
    - if:
      condition: "not os.path.exists('foo')"
      tasks:
        - mkdir:
          path: foo
    
You can run the test by first encrypting a file:

    date >foo.j2
    ./fernetencrypt foobar foo.j2 foo.fernet

Then run "up":

    up exampleplaybook.yaml

NOTE: The example playbook includes references to several templates that are not
created above, so it will error out if they do not exist.

## Playbook Arguments

User-supplied arguments can be specified in an "args" section of the playbook.  For
example:

```yaml
- args:
  schema:
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

The "schema" can contain elements with the following values:

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
- "foo" as a drectory with a "up.yml" file in it.
- "foo" is a file.
- "foo.yml" is a file.

## File and Template Search Path

uPlaybook does not use different directories to store files and templates, like
Ansible does.

Templates and files are searched for in a colon-separated path, either gotten from the
UP\_FILE\_PATH or the default of ".:./files".  A "." in the file path is
relative to the directory that contains the playbook file.

The default search path looks for templates/files in:

- The same directory as the playbook
- In a subdirectory (by the playbook) named "files".

## Debugging

If you set "up\_debug" to true, debugging information will be printed during the
playbook run.  It can also be enabled from the CLI by adding the "--up-debug" argument:
`up --up-debug playbook`.

Example:

    - vars:
      up_debug: true

## Available Tasks

### cd

Change working directory.

Arguments:

- path: The directory to change to (template expanded).

Example:

    - cd:
      path: /tmp/foo

### copy

Copy a (possibly encrypted) file verbatim.

Arguments:

- src: Filename of the source file (template expanded).
- dst: Filename to copy the file to (template expanded).
- skip: If "if\_exists" the copy will be skipped if the destination exists.
    Otherwise the copy will always be done.
- decrypt\_password: A password to decrypt "src" with when copying.
- encrypt\_password: A password to encrypt "src" with when copying.

Example:

    - copy:
      src: program.fernet
      dst: /usr/bin/program
      skip: if\_exists
      decrypt\_password: foobar

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

Example:

    - run:
      command: "date"

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
- skip: If "if\_exists" the copy will be skipped if the destination exists.
    Otherwise the copy will always be done.
- decrypt\_password: A password to decrypt "src" with when copying.
- encrypt\_password: A password to encrypt "src" with when copying.

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
