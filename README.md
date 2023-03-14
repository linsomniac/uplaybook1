# uPlaybook -- An Ansible-Inspired Micro Playbook Runner

This is an extremely small, yaml-driven tool for doing simple file deployment and
templating sorts of tasks.  It only requires Python and a couple of libraries.

I implemented it primarily to deploy encrypted secrets and files, including templating,
to a group of Windows machines.  In particular, the templating and encryption are
more difficult to provide via a Powershell script.

## Features

- Templating (jinja2) of files, paths, and configuration values.
- Built in encryption/decryption (Fernet, via Python cryptography module)
- Ansible-inspired yaml configuration.
- Can template from the environment.
- Helpers for fernet encrypt/decrypt.

## Requirements

- Python 3
- Python libraries: cryptography, jinja2, pyyaml

For example, on Ubuntu: apt install python3 python3-cryptography python3-yaml python3-jinja2

## Examples

Given a "exampleconfig.yaml" that looks like this:

    - vars:
      suffix: "{{environ['EXAMPLE_SUFFIX'] | default('')}}"
      destdir: "/tmp/foo{{suffix}}"
      password: foobar
    
    - rm:
      path: "{{destdir}}"
      recursive: true
    - run:
      command: "ls -ld {{destdir}}"
    - mkdir:
      path: "{{destdir}}"
    - copy:
      src: foo.fernet
      dst: "{{destdir}}/bar"
      skip: if_exists
      decrypt_password: "{{password}}"
    - template:
      src: foo.j2
      dst: "{{destdir}}/foo-templated"
      skip: if_exists
    - cd:
      path: "{{destdir}}"
    - run:
      command: "ls -ld"

You can run the test by first encrypting a file:

    date >foo
    ./fernetencrypt foobar foo foo.fernet

Then run "up":

    up exampleconfig.yaml

## Modules

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

### mkdir

Create a directory.

Arguments:

- path: Directory to create (template expanded).
- skip: If "if\_exists" the mkdir will be skipped if the destination exists.
    Otherwise the mkdir will always be done.

Example:

    - mkdir:
      path: /tmp/foo

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

### vars

Set variables in the environment, for use in templating.

Arguments:

Takes a key/value list.

Example:

    - vars:
      key: value
      foo: "{{key}}"
      path: "{{environ['PATH']}}"

## License

CC0 1.0 Universal, see LICENSE file for more information.
