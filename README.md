# Moppi
Modern Python Package Installer.  
`Moppi` automatically manages dependencies using `pyproject.toml` file.  

## Usage
```
moppi add flask fastapi     # install 2 packages
moppi add black --dev       # install an optional package
moppi update flask          # update a package and all it's dependencies
moppi update                # update everything
moppi remove flask          # remove
moppi apply                 # install packages from pyroject.toml
moppi apply --dev           # install only optional packages from pyroject.toml
```

## Config file example, stored in pyproject.toml
The sequence of commands above will produce the following `pyproject.toml` file.
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
