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
- Environment variables are brought into template namepsace.
- Helpers for fernet encrypt/decrypt.

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
    
You can run the test by first encrypting a file:

    date >foo.j2
    ./fernetencrypt foobar foo.j2 foo.fernet

Then run "up":

    up exampleplaybook.yaml

NOTE: The example playbook includes references to several templates that are not
created above, so it will error out if they do not exist.

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
