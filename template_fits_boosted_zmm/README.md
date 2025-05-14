## 🛠️ Installation: Latest CMS Combine Setup

To set up the latest CMS Combine environment with CMSSW and CombineHarvester:

```bash
# Set up the CMSSW environment
cmsrel CMSSW_14_1_0_pre4
cd CMSSW_14_1_0_pre4/src
cmsenv

# Clone Combine framework
git clone https://github.com/cms-analysis/HiggsAnalysis-CombinedLimit.git HiggsAnalysis/CombinedLimit

# IMPORTANT: Checkout the recommended tag from the Combine GitHub page:
# https://github.com/cms-analysis/HiggsAnalysis-CombinedLimit

# Clone CombineHarvester and checkout a specific version
git clone https://github.com/cms-analysis/CombineHarvester.git CombineHarvester
cd CombineHarvester
git checkout v3.0.0-pre1
cd ../..

# Build the environment
scram b -j
```
## 🧪 Step 1: Fitting the Signal and Backgrounds
To fit the simulated Z→μμ signal and relevant backgrounds, and to generate the necessary datacards, run:
```bash
source runFit.csh
```
## 📤 Step 2: Extraction of Results
After generating the datacards, run the following script to create Combine workspaces and perform statistical fits:
```bash
source runWorkspace.csh
```
