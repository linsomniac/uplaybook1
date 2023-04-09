= uPlaybook Examples

Here are some example playbooks.

- encryptall / decryptall - Helpers for situations where you have a lot of fernet
  encrypted files in your play, these helpers allow you to decrypt them all, work on
  them, and then re-encrypt them.  "up decryptall <PW>".  The encryptall playbook
  also by default deletes the plaintext files, see "up encryptall --help".

<!-- vim: ts=4 sw=4 ai et tw=85
-->
