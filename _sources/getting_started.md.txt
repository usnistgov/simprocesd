# Getting Started
How to get started with using the SimPROCESD simulator package.

## Requirements
Python3, version 3.7 or later.


## Installation

### Option 1: Standard package install

Install Sim-PROCESD via `pip` using:
```
$ pip install simprocesd
```
To install with optional requirements needed to run some of the examples use:
```
$ pip install simprocesd[examples]
```

### Option 2: Developer setup

If you would like to make local changes to the `simprocesd` package you are running.

**1.** Fetch the code to a local folder
```
git clone https://github.com/usnistgov/simprocesd.git <root_repo_folder_path>
```

**2.** Add the local code as a package with pip. Navigate to `<root_repo_folder_path>` and run:
```
pip install -e .[examples]
```
Using `-e` flag means the install will be <u>editable</u> and any changes made to the code in
`<root_repo_folder_path>` will be reflected without needing to reinstall the SimPROCESD package.

&nbsp;  
**3.** Import and use SimPROCESD package as you normally would except that now you can make changes
to the code and have them be reflected in the package.

&nbsp;  
4. To uninstall a package installed with a `-e` flag navigate to `<root_repo_folder_path>` and run:
```
python setup.py develop -u
```
