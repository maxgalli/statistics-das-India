DIR=$PWD
year="2022"
out_dir="fit_zmm_"$year"_pt450"
datacard_path="datacards_zmm_"$year"_pt450"
rm -rf $out_dir
mkdir -p $out_dir
REL_Zmm_PATH="$(realpath -s --relative-to=$out_dir $datacard_path)"
cd $out_dir
scp $REL_Zmm_PATH/*txt ./
scp $REL_Zmm_PATH/*root ./
text2workspace.py -P HiggsAnalysis.CombinedLimit.PhysicsModel:multiSignalModel --PO 'map=.*/zmm:r_zmm[1,-10,10]' datacard_zmm.txt -m 90 -o datacard_zmm.root
combine -M FitDiagnostics -m 90 -d datacard_zmm.root --setParameters r_zmm=1 --setParameterRanges r_zmm=-10,10 --robustFit 1 --cminDefaultMinimizerStrategy 0 --saveShapes --saveWithUncertainties -n _zmm --redefineSignalPOIs r_zmm --saveWorkspace
cd $DIR
python3 makeFitDistributionsComb.py  -i $out_dir/fitDiagnostics_zmm.root  -o $out_dir -r 4 -y $year --category zmm --postfix inclusive --pre-fit
python3 makeFitDistributionsComb.py  -i $out_dir/fitDiagnostics_zmm.root  -o $out_dir -r 4 -y $year --category zmm --postfix inclusive
cd -
combine -M MultiDimFit -m 90 datacard_zmm.root --setParameters r_zmm=1 --setParameterRanges r_zmm=-10,10 --robustFit 1 --cminDefaultMinimizerStrategy 0 --algo grid --points 100 --redefineSignalPOIs r_zmm -n _zmm_scan --autoBoundsPOIs "r_zmm" --autoMaxPOIs "r_zmm" --autoRange 3 --floatOtherPOIs 1 --saveWorkspace
plot1DScan.py higgsCombine_zmm_scan.MultiDimFit.mH90.root -o r_zmm_scan --POI r_zmm --main-label "With systematics" --main-color 1

combineTool.py -M Impacts -d datacard_zmm.root -m 90 --setParameters r_zmm=1 --setParameterRanges r_zmm=-10,10 --robustFit 1 --cminDefaultMinimizerStrategy 0  --doInitialFit -n _impact_zmm --redefineSignalPOIs r_zmm
combineTool.py -M Impacts -d datacard_zmm.root -m 90 --setParameters r_zmm=1 --setParameterRanges r_zmm=-10,10 --robustFit 1 --cminDefaultMinimizerStrategy 0 --doFits -n _impact_zmm --redefineSignalPOIs  r_zmm
combineTool.py -M Impacts -d datacard_zmm.root -m 90 --setParameters r_zmm=1 --setParameterRanges r_zmm=-10,10 --robustFit 1 --cminDefaultMinimizerStrategy 0 -n _impact_zmm -o impacts_zmm.json --redefineSignalPOIs  r_zmm
plotImpacts.py -i impacts_zmm.json -o impacts_zmm
