import os
import sys
import glob
import argparse
import time
import ROOT
import math
import numpy as np
from array import array 

ROOT.gROOT.SetBatch(True)

parser = argparse.ArgumentParser()
parser.add_argument('-i', '--input-file', type=str, default='', help='input directory with files');
parser.add_argument('-f', '--pre-fit', action='store_true', help='plot pre-fit instead of post-fit');
parser.add_argument('-c', '--category', type=str, default='zjet', choices=["zmm","zjet","pass"], help='categories');
parser.add_argument('-o', '--output-directory', type=str, default='', help='name of the output directory');
parser.add_argument('-p', '--postfix', type=str, default='', help='name to append to the output');
parser.add_argument('-r', '--rebin-factor', type=int, default=5, help='rebin factor for the distribution');
parser.add_argument('-y', '--year', type=str, default='2022', choices=['2022','2023','2022EE'], help='data taking period');
args = parser.parse_args()

ROOT.gInterpreter.ProcessLine('#include "CMS_style.h"')
ROOT.setTDRStyle();
ROOT.gStyle.SetOptStat(0);

lumi_dict = {
    '2022': 35.,
    '2023': 27.7,
    '2022EE': 27.,
}

f_input = ROOT.TFile(args.input_file,"READ");

if args.pre_fit:
    prefix = "shapes_prefit"
else:
    prefix = "shapes_fit_s"

if args.category == "zmm":
    
    h_zmm = f_input.Get(prefix+"/"+args.category+"/zmm");
    h_bkg = f_input.Get(prefix+"/"+args.category+"/bkg");
    h_data = f_input.Get(prefix+"/"+args.category+"/data");
    h_tot = f_input.Get(prefix+"/"+args.category+"/total");

    if h_zmm.GetNbinsX() % args.rebin_factor != 0:
        print("Please change the rebin factor as Nbins=",h_zmm.GetNbinsX()," cannot be divided by rebin factor of ",args.rebin_factor);
        sys.exit()

        
    if args.rebin_factor != 1:
       
        h_zmm.Rebin(args.rebin_factor)
        h_bkg.Rebin(args.rebin_factor)
        h_tot.Rebin(args.rebin_factor)

        g_data = ROOT.TGraphAsymmErrors();
        ## ibin takes already the rebin factor into account
        for ibin in range(0,h_zmm.GetNbinsX()):
            x_val, y_val, y_err_up, y_err_dw = 0, 0, 0, 0;
            x_val =  h_zmm.GetBinCenter(ibin+1);        
            for jbin in range(0,args.rebin_factor):
                y_val = y_val + h_data.GetY()[ibin*args.rebin_factor+jbin]
                y_err_up = y_err_up + h_data.GetErrorYhigh(ibin*args.rebin_factor+jbin)**2
                y_err_dw = y_err_dw + h_data.GetErrorYlow(ibin*args.rebin_factor+jbin)**2
            y_err_up = math.sqrt(y_err_up);
            y_err_dw = math.sqrt(y_err_dw);
            g_data.SetPoint(ibin,x_val,y_val);
            g_data.SetPointError(ibin,0,0,y_err_dw,y_err_up);
        h_data = g_data;
elif args.category == "pass":
    h_zjet = f_input.Get(prefix+"/"+args.category+"/zjet");
    h_wjet = f_input.Get(prefix+"/"+args.category+"/wjet");
    h_qcd = f_input.Get(prefix+"/"+args.category+"/qcd");
    h_data = f_input.Get(prefix+"/"+args.category+"/data");
    h_tot = f_input.Get(prefix+"/"+args.category+"/total");

    if h_zjet.GetNbinsX() % args.rebin_factor != 0:
        print("Please change the rebin factor as Nbins=",h_zjet.GetNbinsX()," cannot be divided by rebin factor of ",args.rebin_factor);
        sys.exit()

        
    if args.rebin_factor != 1:
    
        h_zjet.Rebin(args.rebin_factor)
        h_wjet.Rebin(args.rebin_factor)
        h_qcd.Rebin(args.rebin_factor)
        h_tot.Rebin(args.rebin_factor)

        g_data = ROOT.TGraphAsymmErrors();
        ## ibin takes already the rebin factor into account
        for ibin in range(0,h_zjet.GetNbinsX()):
            x_val, y_val, y_err_up, y_err_dw = 0, 0, 0, 0;
            x_val =  h_zjet.GetBinCenter(ibin+1);        
            for jbin in range(0,args.rebin_factor):
                y_val = y_val + h_data.GetY()[ibin*args.rebin_factor+jbin]
                y_err_up = y_err_up + h_data.GetErrorYhigh(ibin*args.rebin_factor+jbin)**2
                y_err_dw = y_err_dw + h_data.GetErrorYlow(ibin*args.rebin_factor+jbin)**2
            y_err_up = math.sqrt(y_err_up);
            y_err_dw = math.sqrt(y_err_dw);
            g_data.SetPoint(ibin,x_val,y_val);
            g_data.SetPointError(ibin,0,0,y_err_dw,y_err_up);
        h_data = g_data;
                    
c = ROOT.TCanvas("c","",600,650);
c.cd();

pad = ROOT.TPad("pad","",0,0,1,1);
pad.SetFillColor(0);
pad.SetFillStyle(0);
pad.SetTickx(1);
pad.SetTicky(1);
pad.SetBottomMargin(0.30);
pad.SetRightMargin(0.06);
pad.Draw();
pad.cd();

hs = ROOT.THStack("hs","");

if args.category == "zmm":
    h_bkg.SetFillColorAlpha(ROOT.kAzure+10,0.5);
    h_zmm.SetFillColorAlpha(ROOT.kOrange+1,0.5);
    h_bkg.SetLineColor(1);
    h_zmm.SetLineColor(1);
    hs.Add(h_bkg);
    hs.Add(h_zmm);
elif args.category == "pass":
    h_qcd.SetFillColorAlpha(ROOT.kAzure+10,0.5);
    h_wjet.SetFillColorAlpha(ROOT.kBlue,0.5);
    h_zjet.SetFillColorAlpha(ROOT.kOrange+1,0.5);
    h_qcd.SetLineColor(1);
    h_wjet.SetLineColor(1);
    h_zjet.SetLineColor(1);
    hs.Add(h_qcd);
    hs.Add(h_wjet);
    hs.Add(h_zjet);

h_data.SetMarkerColor(ROOT.kBlack);
h_data.SetLineColor(ROOT.kBlack);
h_data.SetMarkerSize(0.8);
h_data.SetMarkerStyle(20);

h_temp = h_tot.Clone("h_temp");
h_temp.GetYaxis().SetTitle("Events / GeV");
h_temp.GetXaxis().SetTitleSize(0);
h_temp.GetXaxis().SetLabelSize(0);
h_temp.GetYaxis().SetRangeUser(0.,h_tot.GetMaximum()*1.5);
h_temp.Draw("hist");

hs.Draw("hist same");
h_data.Draw("EP0same");
h_data.Draw("EP1same");
ROOT.CMS_lumi(c,"%.1f"%(lumi_dict[args.year]),False,False,True);
pad.RedrawAxis("sameaxis");
pad.RedrawAxis("g");

leg = ROOT.TLegend(0.6,0.75,0.90,0.90);    
leg.SetFillColor(0);
leg.SetFillStyle(0);
leg.SetBorderSize(0);
leg.AddEntry(h_data,"Data","PE1");
if args.category == "zmm":
    leg.AddEntry(h_zmm,"Z+jets","F");
    leg.AddEntry(h_bkg,"Background","F");
elif args.category == "pass":
    leg.AddEntry(h_zjet,"Z+jets","F");
    leg.AddEntry(h_wjet,"W+jets","F");
    leg.AddEntry(h_qcd,"QCD","F");
leg.Draw("same");

pad2 = ROOT.TPad("pad2","pad2",0,0.,1,0.96);
pad2.SetFillColor(0);
pad2.SetGridy(1);
pad2.SetFillStyle(0);
pad2.SetTickx(1);
pad2.SetTicky(1);
pad2.SetTopMargin(0.71);
pad2.SetBottomMargin(0.10);
pad2.SetRightMargin(0.06);
pad2.Draw();
pad2.cd();

h_ratio = h_data.Clone("h_ratio");
h_tot_clone = h_tot.Clone("h_tot_clone");
for i in range(1,h_tot_clone.GetNbinsX()+1): h_tot_clone.SetBinError(i, 0);
for i in range(0,h_ratio.GetN()):
    h_ratio.SetPoint(i,h_ratio.GetX()[i],h_ratio.GetY()[i]/h_tot_clone.GetBinContent(i+1));
    h_ratio.SetPointError(i,h_data.GetErrorXlow(i),h_data.GetErrorXhigh(i),h_data.GetErrorYlow(i)/h_tot_clone.GetBinContent(i+1),h_data.GetErrorYhigh(i)/h_tot_clone.GetBinContent(i+1));
    
h_ratio.SetLineColor(ROOT.kBlack);
h_ratio.SetMarkerColor(ROOT.kBlack);
h_ratio.SetMarkerSize(0.8);

h_tot_ratio = h_tot.Clone("h_tot_ratio");
for i in range(1,h_tot_ratio.GetNbinsX()+1):
    h_tot_ratio.SetBinContent(i, 1);
    h_tot_ratio.SetBinError(i, 0);

h_tot_ratio.SetMarkerSize(0);
h_tot_ratio.SetLineWidth(2);
h_tot_ratio.SetLineColor(ROOT.kRed);
h_tot_ratio.SetFillColor(0);
h_tot_ratio.GetYaxis().CenterTitle();
h_tot_ratio.GetYaxis().SetTitle("Data/Pred.");
h_tot_ratio.GetYaxis().SetTickLength(0.08);
h_tot_ratio.GetXaxis().SetTitle("mass (GeV)")

if args.category == "zmm":
    h_tot_ratio.GetYaxis().SetRangeUser(0.,2.);
else:
    h_tot_ratio.GetYaxis().SetRangeUser(0.5,1.5);
    
h_tot_ratio_err = h_tot.Clone("h_tot_ratio_err");
h_tot_ratio_err.Divide(h_tot_clone);
h_tot_ratio_err.SetLineColor(0);
h_tot_ratio_err.SetLineWidth(0);
h_tot_ratio_err.SetFillColor(ROOT.kGray);

h_tot_ratio.GetYaxis().SetNdivisions(506);

h_tot_ratio.Draw("hist");
if not args.pre_fit:
    h_tot_ratio_err.Draw("E2same");
h_tot_ratio.Draw("hist same");
h_ratio.Draw("PE0 same");
h_ratio.Draw("PE1 same");
pad2.RedrawAxis("sameaxis");
pad2.RedrawAxis("g");

os.system("mkdir -p "+args.output_directory);
if args.pre_fit:
    c.SaveAs(args.output_directory+"/distribution_prefit_"+args.category+"_"+args.postfix+".png","png");
    c.SaveAs(args.output_directory+"/distribution_prefit_"+args.category+"_"+args.postfix+".pdf","pdf");
else:
    c.SaveAs(args.output_directory+"/distribution_postfit_"+args.category+"_"+args.postfix+".png","png");
    c.SaveAs(args.output_directory+"/distribution_postfit_"+args.category+"_"+args.postfix+".pdf","pdf");
