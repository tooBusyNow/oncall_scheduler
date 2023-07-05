<div align="left">
  <h1><strong>Oncall Scheduler</strong></h1>
  <p>Light and simple tool for manual schedule configuration at LinkedIn Oncall.</p>
</div>

![ResultDemo](/img/demo.png)

### Table of Contents
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)


## Prerequisites

1) Python with version 3.10 or higher 
2) Pipenv (actually, it's optional, you can use pip3 with venv instead)

## Installation

Just install required dependencies with: 
```bash
pipenv shell
pipenv install
```
Or you may choose the 'classic way', but don't forget to create venv manually at first: 
```bash
pip3 install -r requirements.txt
```

## Usage
Make sure you've created a valid config files at /configs directory and run:
```bash
make run
```