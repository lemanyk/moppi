# Moppi
Moppi - Modern Python Package Installer.  
Automatically manages dependencies using either pyproject.toml or it's own yaml file.  

## Usage
```
python -m moppi add flask
python -m moppi add black --dev
python -m moppi add flask gunicorn
python -m moppi update flask
python -m moppi remove gunicorn
python -m moppi apply
python -m moppi apply --dev
```

## Config file example, stored in pyproject.toml
```
[project]
dependencies = [
    "Werkzeug==2.2.2",
]

[project.optional-dependencies]
dev = [
    "moppi==0.2",
]

[tool.moppi]
indirect-dependencies = [
    [
        "PyYAML==6.0",
        "moppi==0.2",
    ],
    [
        "MarkupSafe==2.1.1",
        "Werkzeug==2.2.2",
    ],
]
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

## Docker usage example
```
FROM python:3.11-slim

# Creating a non-root user, so third party packages can't tamper with the hosts file,
system clock or run outside of a container using some vulnerabilty.
RUN useradd -D app
WORKDIR /home/app
USER app

# Create venv and install moppi
RUN python -m venv env
RUN source env/bin/activate
RUN pip install moppi

# Install production dependencies.
COPY --chown=app:app moppi.yaml .
RUN python -m moppi apply

# Copy local code to the container image.
COPY --chown=app:app . .

# Run the web service on container startup. Here we use the gunicorn
# webserver, with one worker process and 8 threads.
CMD ["gunicorn", "--bind", ":$PORT", "--threads", "8", "main:app"]
```

## todo
tar.gz unpacking  
sha256 check, but don't save it into moppi.yaml (make configurable?)  
platform=Windows support  
extra=='package' support  
upload to arch aur and ubuntu?  
Caching  
Async  
Replace print with logging error warning info  
Check pip cli, but not the source  
Can install other moppi projects without extra configuration.  
sysconfig:  
purelib = "/home/gen/moppi/.env/lib/python3.11/site-packages"  
scripts = "/home/gen/moppi/.env/bin"  
moppi[full] - includes tomli_w and pyyaml. Or moppi[lean]  
--index-url https://test.pypi.org/simple/  
--no-deps  


## done
unit tests  
Config, ConfigTOML, ConfigTOMLW, ConfigYAML  
moppi folder, config.py  
.env/bin/moppi  
add / install / i, remove / delete / r  
Has an explicit package dependecy tree. Inspired by yarn and go/mod.  
Packages stored in pyproject.toml file or in moppi.yaml  
In pyproject.toml add [tools.moppi.dependency-lock]  
manage dependencies directly in pyproject.toml? direct-dependencies and indirect-dependencies  
Package format is either python or yaml(with anchors) or json - toml + yaml  
upgrade  
apply  
add and remove should work for list of packages  
uninstall  
make public, upload to pipy  
python -m moppi support  
CLI support  
connect to venv  
yaml load  
yaml dump indirect  
dependencies  
yaml dump  
dev packages  
indirect packages  
