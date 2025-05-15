year="2022"
outdir="datacards_zmm_"$year"_pt450"
mkdir -p $outdir
python3 prepareDatacardsZmm.py -i "/eos/cms/store/group/phys_exotica/monojet/rgerosa/HH4b/Zbb_calibration/NTuples_Zmumu/2022EE/Ver2/Histogram/inputs_zmm_"$year"_450GeV_NoScaling.root" -o $outdir -y $year
