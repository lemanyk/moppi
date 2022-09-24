# Moppi
Moppi - Modern Python Package Installer  
Where you don't manually manage the package list file  
With an automatic dependecy file management  
With the explicit package dependecy tree. Inspired by yarn and go/mod.  
add creates new file moppi.yaml  

add / install / i, delete / remove / r  

```
python -m moppi add flask
python -m moppi add flask -d --dev
python -m moppi delete flask
python -m moppi apply
python -m moppi apply - f package.py / moppi.py
python -m moppi update flask
```

## Config file example, stored in moppi.yaml
```
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
```

## Installation
Moppi should be only used inside of a virtualenv.  
The best way to boot Moopi is to create a virtualenv and install `moppi` package via pip.  
```
python -m venv .env
source .env/bin/activate
pip install moppi
```


## todo
python -m moppi support  
unit tests  
tar.gz unpacking  
sha256 check, but don't save it into moppi.yaml (make configurable?)  
platform=Windows support  
extra=='package' support  
make public, upload to pipy, arch aur and ubuntu  

Is sha256 even neccesary(?)  
Package format is either python or yaml(with anchors) or json  
Async  
Check pip cli, but not the source  
Can install other moppi projects without extra configuration.  
In docker it's still better to use a non-root user, so third party packages won't tamper with hosts file, system clock or even run outside of a container using some vulnerabilty. Or run outside of a container into cluster causing catastrophe.

## done
CLI support  
connect to venv  
yaml load  
yaml dump indirect  
dependencies  
yaml dump  
dev packages  
indirect packages  
