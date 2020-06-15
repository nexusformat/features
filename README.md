# Overview

This repository contains the "features" curated by the community for 
NeXus file reading, validation and related uses.

The main objectives of this project is it to 
* to use a highlevel programming language to define how things a encoded in the file
* facilitate direct functional tests for file contents and information extraction logic 
  as a means to be less ambigous than documentation that needs to be parsed by developers
* lower the barrier for people to get involved in defining a meaningful standard 
  through bits of code
  
## Usage

Provided all dependencies are met (see below):

.. code-block:: bash 
  $ python src/nxfeature.py filewithfeature.nxs

should
* lookup the feature(s) in the file `filewithfeature.nxs`
* load and instantiate the recipe class(es)
* process the valid feature(s) correctly and display their output strings

#### Optional Flags
| Flag               | Arguments           | Description                                   |
|:------------------ |:--------------------|:----------------------------------------------|
| `-h`, `--help`     |                     | Show the help page for this script.           |
| `-t`, `--test`     |                     | Test the file against all possible recipes.   |
| `-f`, `--feature=` | feature id          | Test the file against specified recipe.       |
| `-v`, `--verbose`  |                     | Include full stacktraces of failures.         |
| `-x`, `--xml=`     | XML file location   | XML file to write the junit output to. Note: does not need to be an existing file as the script will create/truncate it.|

#### Requirements

Recipes in features are not allowed to require or otherwise load additional python packages.
Only numpy and h5py are available as per the top level `requirements.txt`. 

The rationale is that features should be self contained and be viewed on their own.
Feature are not the place to put complex analysis or processing tasks.

For reference, in order to install the requirements something the following is recommended:
.. code-block:: bash 
  $ python3 -m venv python3-environment
  $ . python3-environment/bin/activate
  $ pip install -r requirements.txt 

## Submitting your own features

One of the objectives was it to make this relatively simple to start with but maintain NeXus as a standard.

Features are referenced by a (semi-)random 64 bit uint identifier. To get an ID assigned for your own feature the process is as follows:

1. clone this repository into your own Github account or organisation.
2. checkout your clone 
3. run ./newfeature which will:
    * check your clone is up to date 
    * ask a few questions on the feature you indend to propose
    * register the proposal with our webservice which will issue a unique ID
    * generate some template code as a starting point
5. activate the feature by clicking on the link in the confirmation mail you received from the webservice
4. develop your code
6. submit a Github pull request when you are done with your code

The newfeature.py script could be made to be more helpful and assist with cloning repos and so on.
Feel free to suggest your ideas.

If at any point you encounter problems, just raise a ticket in this repository.

## Status

This is project is deemed useful by the NIAC, but progress to add more features is slow.

The travis build checks the example files against all recipes in the repository.

[![Build Status](https://travis-ci.org/nexusformat/features.svg?branch=master)](https://travis-ci.org/nexusformat/features)
[![Code Health](https://landscape.io/github/nexusformat/features/master/landscape.svg?style=flat)](https://landscape.io/github/nexusformat/features/master)
[![Scrutinizer Code Quality](https://scrutinizer-ci.com/g/nexusformat/features/badges/quality-score.png?b=master)](https://scrutinizer-ci.com/g/nexusformat/features/?branch=master)

