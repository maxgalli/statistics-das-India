## 🧪 Step 1: Fitting the Signal and Backgrounds
To fit the simulated Z→bb signal and QCD backgrounds, and to generate the necessary datacards, run:
```bash
python3 prepareDatacardsZbb.py -i /afs/cern.ch/work/m/mukherje/public/IITH/combine/inputfiles/ -o output
```

## 📤 Step 2.1: .txt to .root conversion
defining the signal strength of the zjet process as r_zjet and the initial range from -10 to 10
```bash
text2workspace.py -P HiggsAnalysis.CombinedLimit.PhysicsModel:multiSignalModel --PO 'map=.*/zjet:r_zjet[1,-10,10]' datacard_zbb_tutorial_pass.txt -m 90 -o datacard_zbb_tutorial_pass.root
```

## 📤 Step 2.2: Running the signal strength
```bash
combine -M MultiDimFit -m 90 datacard_zbb_tutorial_pass.root --setParameters r_zjet=1 --setParameterRanges r_zjet=-10,10 --robustFit 1 --cminDefaultMinimizerStrategy 0 --algo grid --points 100 --redefineSignalPOIs r_zjet  -n boosted_zbb_tutorial.obs  --autoBoundsPOIs "*" --autoMaxPOIs "r_zjet" --autoRange 3 --floatOtherPOIs 1 --saveWorkspace
```

## 📤 Step 2.3: plot signal strength
```bash
python3 modified_plot1Dscan_coupling.py workspace/higgsCombineboosted_zbb_tutorial.obs.MultiDimFit.mH90.root --main-label="Obs" --main-color 1  --POI r_zjet -o zbb_tutorial
```

## 📤 Step 3.1: running FitDiagnostics
```bash
combine -M FitDiagnostics -m 90 -d datacard_zbb_tutorial_pass.root --setParameters r_zjet=1 --setParameterRanges r_zjet=-10,10 --robustFit 1 --cminDefaultMinimizerStrategy 0 --saveShapes --saveWithUncertainties -n _tutorial --redefineSignalPOIs r_zjet --saveWorkspace
```

## 📤 Step 3.1:Prefit/Post-fit distribution
```bash
python3 makeFitDistributionsComb.py  -i workspace/fitDiagnostics_tutorial.root -o tutorial -c pass --pre-fit
python3 makeFitDistributionsComb.py  -i workspace/fitDiagnostics_tutorial.root -o tutorial -c pass
```
