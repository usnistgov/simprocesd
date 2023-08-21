# Getting Started
Installing SimPROCESD on your device.

## Requirements
Python3, version 3.7 or later.


## Installation

The package is available online at [pypi.org/project/simprocesd/](https://pypi.org/project/simprocesd/)

### Option 1: Standard installation

Installing SimPROCESD using pip:
```
$ pip install simprocesd
```
Installing SimPROCESD with additional dependencies needed to run the [examples](examples.md):
```
$ pip install simprocesd[examples]
```

### Option 2: Developer setup

If you would like to make local changes to the **simprocesd** package in your environment.

**1.** Fetch the code to a local folder
```
git clone https://github.com/usnistgov/simprocesd.git <local_folder_path>
```

**2.** Add the local code as a package with pip: navigate to `<folder_path>` and run
```
pip install -e .[examples]
```
Using **-e** flag means the install will be editable and any changes made to the code in
`<local_folder_path>` will be reflected without needing to reinstall the SimPROCESD package.

&nbsp;  
**3.** Import and use SimPROCESD package as you normally would except that now you can make changes
to the code and have them be reflected in the package.

&nbsp;  
4. To **uninstall** a package installed with a **-e** flag navigate to `<local_folder_path>` and run:
```
python setup.py develop -u
```
