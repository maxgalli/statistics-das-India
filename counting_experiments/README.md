# Counting Experiments

## Introduction

These exercises are taken from [this folder](https://github.com/FNALLPC/statistics-das/tree/master/3) in the FNAL-DAS repo.

## Analyze three counts using Combine ([link](https://github.com/FNALLPC/statistics-das/blob/master/3/exercise_3a.ipynb))

The following datacard
```
# derived from Table 4 (page 58) of http://arxiv.org/pdf/1312.5353v3
Combination of hzz.txt
imax 3 number of bins
jmax 2 number of processes minus 1
kmax 9 number of nuisance parameters
----------------------------------------------------------------------------------------------------------------------------------
bin          ch1_bin4e    ch1_bin2e2m  ch1_bin4m
observation  4            13           8
----------------------------------------------------------------------------------------------------------------------------------
bin                               ch1_bin4e    ch1_bin4e    ch1_bin4e    ch1_bin2e2m  ch1_bin2e2m  ch1_bin2e2m  ch1_bin4m    ch1_bin4m    ch1_bin4m
process                           h125         zz           zx           h125         zz           zx           h125         zz           zx
process                           0            1            2            0            1            2            0            1            2
rate                              3            1.1          0.8          7.9          3.2          1.3          6.4          2.5          0.4
----------------------------------------------------------------------------------------------------------------------------------
h125_rate_2e2m          lnN       -            -            -            1.13         -            -            -            -            -
h125_rate_4e            lnN       1.13         -            -            -            -            -            -            -            -
h125_rate_4m            lnN       -            -            -            -            -            -            1.11         -            -
zx_rate_2e2m            lnN       -            -            -            -            -            1.23         -            -            -
zx_rate_4e              lnN       -            -            1.25         -            -            -            -            -            -
zx_rate_4m              lnN       -            -            -            -            -            -            -            -            1.15
zz_rate_2e2m            lnN       -            -            -            -            1.06         -            -            -            -
zz_rate_4e              lnN       -            1.09         -            -            -            -            -            -            -
zz_rate_4m              lnN       -            -            -            -            -            -            -            1.08         -
```
describes a simple counting experiment in three bins.
Following the explanation reported [here](https://cms-analysis.github.io/HiggsAnalysis-CombinedLimit/latest/part3/commonstatsmethods/?h=asymptoticlimits), we can run
```
combine -M AsymptoticLimits hzz.txt
```
to print observed and expected limits on the signal strength $\mu$ (usually called `r` in Combine).

Some other methods, however, work only if the format of the datacard is shape-based. To do so, we need to run
```
combineCards.py hzz.txt -S > hzzshape.txt
```
which adds extra lines to the datacard (as explained [here](https://cms-analysis.github.io/HiggsAnalysis-CombinedLimit/latest/part3/nonstandard/?h=fake#normalizations)).

For instance, we can run
```
combine -M FitDiagnostics hzzshape.txt
```
to get an estimate for $\mu$ and some other useful outputs, described [here](https://cms-analysis.github.io/HiggsAnalysis-CombinedLimit/latest/part5/longexercise/?h=fitdia#b-running-combine-for-a-blind-analysis).

Another thing we can do is computing the [significance of a the result](https://cms-analysis.github.io/HiggsAnalysis-CombinedLimit/latest/part3/commonstatsmethods/?h=significance#asymptotic-significances)
```
combine -M Significance hzz.txt
```
in the Asymptotic limit. 

We can do the same for the expected significance, computed from an Asimov dataset of signal+background
```
combine -M Significance hzz.txt -t -1 --expectSignal=1
``` 
You can now play around with the quantities in the datacard and see how these results change.