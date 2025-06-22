void setTDRStyle (){
  
  gStyle->SetCanvasBorderMode(0);
  gStyle->SetCanvasColor(0);
  gStyle->SetCanvasDefH(600);
  gStyle->SetCanvasDefW(600);
  gStyle->SetCanvasDefX(0);
  gStyle->SetCanvasDefY(0);

  gStyle->SetPadBorderMode(0);
  gStyle->SetPadColor(0); 
  gStyle->SetPadGridX(0);
  gStyle->SetPadGridY(0);
  gStyle->SetGridColor(0);
  gStyle->SetGridStyle(3);
  gStyle->SetGridWidth(1);

  gStyle->SetFrameBorderMode(0);
  gStyle->SetFrameBorderSize(1);
  gStyle->SetFrameFillColor(0);
  gStyle->SetFrameFillStyle(0);
  gStyle->SetFrameLineColor(1);
  gStyle->SetFrameLineStyle(1);
  gStyle->SetFrameLineWidth(1);
  gStyle->SetHistLineColor(1);
  gStyle->SetHistLineStyle(0);
  gStyle->SetHistLineWidth(1);

  gStyle->SetEndErrorSize(2);
  gStyle->SetFuncColor(2);
  gStyle->SetFuncStyle(1);
  gStyle->SetFuncWidth(1);
  gStyle->SetOptDate(0);
  
  gStyle->SetOptFile(0);
  gStyle->SetStatColor(0); 
  gStyle->SetStatFont(42);
  gStyle->SetStatFontSize(0.04);
  gStyle->SetStatTextColor(1);
  gStyle->SetStatFormat("6.4g");
  gStyle->SetStatBorderSize(1);
  gStyle->SetStatH(0.1);
  gStyle->SetStatW(0.15);

  gStyle->SetPadTopMargin(0.07);
  gStyle->SetPadBottomMargin(0.13);
  gStyle->SetPadLeftMargin(0.12);
  gStyle->SetPadRightMargin(0.05);

  gStyle->SetOptTitle(0);
  gStyle->SetTitleFont(42);
  gStyle->SetTitleColor(1);
  gStyle->SetTitleTextColor(1);
  gStyle->SetTitleFillColor(10);
  gStyle->SetTitleFontSize(0.05);

  gStyle->SetTitleColor(1, "XYZ");
  gStyle->SetTitleFont(42, "XYZ");
  gStyle->SetTitleSize(0.05, "XYZ");
  gStyle->SetTitleXOffset(0.9);
  gStyle->SetTitleYOffset(1.05);
 
  gStyle->SetLabelColor(1, "XYZ");
  gStyle->SetLabelFont(42, "XYZ");
  gStyle->SetLabelOffset(0.007, "XYZ");
  gStyle->SetLabelSize(0.04, "XYZ");

  gStyle->SetAxisColor(1, "XYZ");
  gStyle->SetStripDecimals(1); 
  gStyle->SetTickLength(0.025, "XYZ");
  gStyle->SetNdivisions(510, "XYZ");
  gStyle->SetPadTickX(1); 
  gStyle->SetPadTickY(1);

  gStyle->SetOptLogx(0);
  gStyle->SetOptLogy(0);
  gStyle->SetOptLogz(0);

  gStyle->SetPaperSize(20.,20.);
  gStyle->SetPaintTextFormat(".2f");
}

void CMS_lumi(TPad* pad, string lumi, bool isPreliminary = false, bool isSimulation = false, bool isWorkInProgress = false, float xoffset = 0){

  TLatex* latex = new TLatex();
  latex->SetNDC();
  latex->SetTextSize(0.6*pad->GetTopMargin());
  latex->SetTextFont(42);
  latex->SetTextAlign(31);
  
  if(lumi != "")
    latex->DrawLatex(0.94-xoffset,0.95,(lumi+" fb^{-1} (13.6 TeV)").c_str());
  else
    latex->DrawLatex(0.94-xoffset,0.95,"13.6 TeV");
  
  latex->SetTextSize(0.6*pad->GetTopMargin());
  latex->SetTextFont(62);
  latex->SetTextAlign(11);      
  latex->DrawLatex(0.165, 0.86, "CMS");
  
  if(isPreliminary and isSimulation){
    latex->SetTextSize(0.6*pad->GetTopMargin());
    latex->SetTextFont(52);
    latex->SetTextAlign(11);    
    latex->DrawLatex(0.255, 0.86, "Preliminary Simulation");
  }  
  else if(isPreliminary and not isSimulation){
    latex->SetTextSize(0.6*pad->GetTopMargin());
    latex->SetTextFont(52);
    latex->SetTextAlign(11);    
    latex->DrawLatex(0.255, 0.86, "Preliminary");
  }
  else if(not isPreliminary and isSimulation){
    latex->SetTextSize(0.6*pad->GetTopMargin());
    latex->SetTextFont(52);
    latex->SetTextAlign(11);    
    latex->DrawLatex(0.255, 0.86, "Simulation");
  }
  else if(isWorkInProgress){
    latex->SetTextSize(0.6*pad->GetTopMargin());
    latex->SetTextFont(52);
    latex->SetTextAlign(11);    
    latex->DrawLatex(0.255, 0.86, "Work in progress");
  }
}

