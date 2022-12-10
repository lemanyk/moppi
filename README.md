# Moppi
Moppi - Modern Python Package Installer.  
Automatically manages dependencies using pyproject.toml file.  

## Usage
```
moppi add flask fastapi
moppi add black --dev
moppi update flask
moppi remove flask
moppi apply
moppi apply --dev
```

## Config file example, stored in pyproject.toml
```
[project]
dependencies = [
    "fastapi==0.88.0",
]

[project.optional-dependencies]
dev = [
    "black==22.12.0",
]

[tool.moppi]
indirect-dependencies = [
    "starlette==0.23.1 :: fastapi==0.88.0",
    "idna==3.4 :: anyio==3.6.2",
    "platformdirs==2.6.0 :: black==22.12.0",
    "click==8.1.3 :: black==22.12.0",
    "anyio==3.6.2 :: starlette==0.23.1",
    "pydantic==1.10.2 :: fastapi==0.88.0",
    "typing-extensions==4.4.0 :: pydantic==1.10.2",
    "mypy-extensions==0.4.3 :: black==22.12.0",
    "sniffio==1.3.0 :: anyio==3.6.2",
    "pathspec==0.10.2 :: black==22.12.0",
]
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
Drop yaml support?  
--dev -d / --test / --cicd / --doc / --tools / --all  


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
