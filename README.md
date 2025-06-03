# CMS Data Analysis School (CMSDAS): Statistics Short Exercise

## Introduction

This is a set of tutorials for the CMS Data Analysis School (CMSDAS) Statistics Short Exercise held in June 2025 in Hyderabad.
The main reference is the [original FNAL DAS](https://github.com/FNALLPC/statistics-das).

## Set up

Following are the different ways in which we can set up an environment and run the exercises.

### Lxplus

Install Combine following the instructions reported [here](https://cms-analysis.github.io/HiggsAnalysis-CombinedLimit/v10.2.X/).
As Jupyter seems to be broken, one option is to install (and run it) using ```uv```.
Firts, install it running
```
curl -Ls https://astral.sh/uv/install.sh | sh
```
then run
```
uv run --with jupyter jupyter lab --no-browser
```
To open the tab in the browser, on your laptop run
```
ssh -Y -N -f -L localhost:<local port number>:localhost:<remote port number, usually 8888> <username>@<lxplus machine>.cern.ch
```
You can then locally connect to ```localhost:<local port number>``` and run the notebooks available in this tutorial.

### Locally

We can use [pixi](https://pixi.sh/latest/) to set up a workspace and install combine from conda.

Install pixi with
```
curl -fsSL https://pixi.sh/install.sh | sh
pixi self-update
```

and create/activate an environment where we install combine

```
pixi init combine
cd combine
pixi add cms-combine
pixi shell
```

we can then access the workspace and clone a repo with combine (that we can use to do the tutorials) and this repo

```
cd combine
git clone https://github.com/cms-analysis/HiggsAnalysis-CombinedLimit.git src/HiggsAnalysis/CombinedLimit
export CMSSW_BASE=$PWD

git clone https://github.com/maxgalli/statistics-das-India.git
```