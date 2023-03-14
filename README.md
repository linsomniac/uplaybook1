# uPlaybook -- An Ansible-Inspired Micro Playbook Runner

This is an extremely small, yaml-driven tool for doing simple file deployment and
templating sorts of tasks.  It only requires Python and a couple of libraries.

I implemented it primarily to deploy encrypted secrets and files, including templating,
to a group of Windows machines.  In particular, the templating and encryption are
more difficult to provide via a Powershell script.

# Features

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

    - config:
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

## License

CC0 1.0 Universal, see LICENSE file for more information.
