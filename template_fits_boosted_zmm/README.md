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
