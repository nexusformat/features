# Overview

This repository is for the (for the moment) experimental work on features for 
NeXus file reading, validation and related uses.

The main objectives of this project is it to 
* lower the barrier for people to get involved in defining a meaningful standard
* to use a highlevel programming language to define how things a encoded in the file.
  This allows more direct tests of any logic and is less ambigous than plain English.
  In contrast to XML defining logic is more straight forward.

## Usage

Provided all dependencies are met:

$ python src/nxfeature.py filewithfeature.nxs

should
* lookup the feature(s) in the file *filewithfeature.nxs*
* successfully load and instantiate the recipe class(es)
* process the feature(s) and output 

You can use the -t flag to test the file against all possible recipes.

## Submitting your own features

One of the objectives was it to make this relatively simple to start with but maintain NeXus as a standard.

Features are referenced by a (semi-)random 64 bit uint identifier. To get an ID assigned for your own feature the process is as follows:

1. clone this repository into your own Github account or organisation.
2. checkout your clone 
3. run ./newfeature which will
  a. check your clone is up to date 
  b. ask a few questions on the feature you indend to propose
  c. register the proposal with our webservice which will issue a unique ID
  d. generate some template code as a starting point
5. activate the feature by clicking on the link in the confirmation mail you received from the webservice
4. develop your code
6. submit a Github pull request when you are done with your code

The newfeature.py script could be made to be more helpful and assist with cloning repos and so on.
Feel free to suggest your ideas.

If at any point you encounter problems, just raise a ticket in this repository.

## Status

This is still work in progress.

The travis build checks the example files against all recipes in the repository.

[![Build Status](https://travis-ci.org/nexusformat/features.svg?branch=master)](https://travis-ci.org/nexusformat/features)
