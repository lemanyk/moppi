# Moppi
Moppi - Modern Python Package Installer
Where you don't manually manage the package list file
With an automatic dependecy file management
With the explicit package dependecy tree. Inspired by yarn and go/mod.
add creates new file package.py / moppi.py

python -m moppi add flask
python -m moppi add flask -d --dev
python -m moppi delete flask
python -m moppi apply
python -m moppi apply - f package.py / moppi.py
python -m moppi update flask

# Config file example, stored in moppi.yaml
dependencies:
  Werkzeug:
    name: Werkzeug
    sha256: f979ab81f58d7318e064e99c4506445d60135ac5cd2e177a2de0089bfd4c9bd5
    version: 2.2.2
dev_dependencies: {}
indirect_dependencies:
  MarkupSafe:
    name: MarkupSafe
    needed_by:
    - Werkzeug
    sha256: 86b1f75c4e7c2ac2ccdaec2b9022845dbb81880ca318bb7a0a01fbf7813e3812
    version: 2.1.1
  PyYAML:
    name: PyYAML
    needed_by:
    - watchdog
    sha256: d4db7c7aef085872ef65a8fd7d6d09a14ae91f691dec3e87ee5ee0539d516f53
    version: '6.0'
  watchdog:
    name: watchdog
    needed_by:
    - Werkzeug
    sha256: a735a990a1095f75ca4f36ea2ef2752c99e6ee997c46b0de507ba40a09bf7330
    version: 2.1.9

# todo
yaml dump indirect
yaml load
tar.gz unpacking
platform=Windows support

Package format is either python or yaml(with anchors) or json
Async
Check pip cli, but not the source
Can install other moppi projects without extra configuration.
Should be only used inside of a virtualenv.
In docker it's still better to use a non-root user, so third party packages won't tamper with hosts file, system clock or even run outside of a container using some vulnerabilty. Or run outside of a container into cluster causing catastrophe.


# done
dependencies
yaml dump
dev packages
indirect packages
