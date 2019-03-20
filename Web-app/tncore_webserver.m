function tncore_webserver(growthFrac, expressThresh)

%
% An overall pipeline for running Tn-Core from the webserver
%
% AUTHORS
%   George diCenzo and Marco Fondi - 05/04/2019
%

%% Set up the environment

% Set up the paths and initialize the COBRA Toolbox
addpath(genpath('../../../Software/cobratoolbox/'));
addpath(genpath('../../../Software/libSBML/'));
addpath(genpath('../../../Software/SBMLToolbox/'));
addpath(genpath('../../../Software/Tn-Core/'));
addpath(genpath('../../../Software/tiger/'));
initCobraToolbox;
addpath(genpath('../../../Software/FastCore/'));
rmpath(genpath('../../../Software/cobratoolbox/src/dataIntegration/transcriptomics/FASTCORE'));
changeCobraSolver('ibm_cplex', 'all');

%% Check that all data is provided

% Is there a model file
if exist('inputModel.xml') == 2
    inModelPres = true;
else
    inModelPres = false;
end
assert(inModelPres == true, 'Please prepare an inputModel.xml file with the exchange reactions to set, and place in the current directory');

% Is there a ExRxns file
if exist('ExRxns.txt') == 2
    ExRxnsPres = true;
else
    ExRxnsPres = false;
end
assert(ExRxnsPres == true, 'Please prepare a ExRxns.txt file with the exchange reactions to set, and place in the current directory');

% Is there a ObjectiveRxn file
if exist('ObjectiveRxn.txt') == 2
    ObjRxnPres = true;
else
    ObjRxnPres = false;
end
assert(ObjRxnPres == true, 'Please prepare a ObjectiveRxn.txt file with the exchange reactions to set, and place in the current directory');

% Is there TnSeq data
if exist('TnSeqData.txt') == 2
    tnseqData = true;
else
    tnseqData = false;
end
assert(tnseqData == true, 'Please provide TnSeq data');

% Is there RNAseq data
if exist('RnaSeqData.txt') == 2
    rnaseqData = true;
else
    rnaseqData = false;
end

%% Import the data

% Import the data
if rnaseqData == true
   [model, tnseq, rnaseq] = tncore_import();
else
   [model, tnseq] = tncore_import();
end

%% Set the default growthFrac and expressThresh variables

% Set default growthFrac
if nargin < 1
    growthFrac = 0.5;
elseif isempty(growthFrac)
    growthFrac = 0.5;
end

% Set default expressThresh
if rnaseqData == true
    if nargin < 2
        expressThresh = sum(cell2mat(rnaseq(:,1))) / 5000;
    elseif isempty(expressThresh)
        expressThresh = sum(cell2mat(rnaseq(:,1))) / 5000;
    end
end

%% Prepare the core reconstruction

% Turn on the parallel pool
parpool(8);

% Prepare the core model
if rnaseqData == true
    [contextModel, reducedModel] = tncore_core(model, tnseq, [], [], ...
        growthFrac, rnaseq, expressThresh);
else
    [contextModel, reducedModel] = tncore_core(model, tnseq, [], [], ...
        growthFrac);
end

%% Export the data

% Export the model as an excel file
if tnseqData == true && rnaseqData == true
    tncore_export(contextModel, reducedModel, tnseq, rnaseq);
elseif tnseqData == true && rnaseqData == false
    tncore_export(contextModel, reducedModel, tnseq);
end

% Export the model in cobra format
clearvars -except contextModel
save('exportedModel.mat', 'contextModel');

%% Quit

quit
