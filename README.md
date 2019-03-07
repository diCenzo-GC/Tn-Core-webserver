# Tn-Core Webserver

Transposon-sequencing (TnSeq) and genome-scale constraint-based metabolic modelling are highly complementary experimental and in silico approaches. Workflows combining these two approaches have the potential to provide insights not obtainable by either method alone. The Tn-Core Toolbox was designed to provide tools for integrating these methods, facilitating the contextualization of TnSeq data and the formation of context-specific core metabolic reconstructions. The output models provide a framework to assist in the functional interpretation of TnSeq data and in identifying gaps in the data, in addition to being useful in downstream modelling pipelines.

The Tn-Core webserver is a web-based implementation of one of the main functionalities of Tn-Core: extraction of a context-specific core metabolic network on the basis of TnSeq data. The webserver returns the core metabolic network in two formats: i) as an easy-to-understand Excel file, and ii) as a COBRA-formatted model as a MATLAB file. The webserver was developed to (hopefully) be accessible even to those with little to no experience in metabolic modelling. Below, you will find a description of the input requirements and the outputs. Additionally, this repository contains five files aside from the README file; these files are sample data for use with the Tn-Core webserver.


## Contacts

If you have questions about the use of the Tn-Core webserver, please send inquiries to George diCenzo (george.dicenzo [at] queensu.ca) or Marco Fondi (marco.fondi [at] unifi.it).


## Principle

The main idea behind the Tn-Core webserver is to use metabolic reconstructions to functionally interpret TnSeq data. A genome-scale metabolic reconsruction is meant to capture the entire metabolism of the cell, with every reaction linked to the gene(s) whose gene product(s) catalyze the reaction. One of these reactions represents the formation of biomass by combining the relevant molecules (protein, DNA, RNA, lipids, etc.) in the appropriate ratio. Mathematical methods, such as FBA, can be used to run simulations with these reconstructions, with the aim of the simulations being to produce as much biomass as possible with a given set of input nutrients.

Essentially, Tn-Core takes a genome-scale metabolic reconstruction and attempts to produce a reduced 'core' reconstruction that is still able to produce biomass, using the tranTnSeq data (and optionally also RNA-sequencing data) as a guide to select which genes (and thus reactions) to remove from the reconstruction. The final output is therefore a context-specific core reconstruction, containing just the metabolism that is essential for growth in a given environment. These reconstructions, or essentially a list of metabolic reactions, can be used to gain a functional understanding of the TnSeq data; i.e., what are the essential metabolic functions? Importantly, they can identify metabolic reactions that are essential in a given environment that for some reason (e.g., functional redundancy) did not appear essential in the TnSeq data. In this way, Tn-Core can help provide a more comprehensive understanding of the metabolic processes underlying growth in an environment of interest.


## Required Inputs

### Metabolic Reconstruction
A metabolic reconstruction for your organism of interest must be obtained. This can be your own metabolic reconstruction, or can be downloaded from the web (for example, from the BiGG or VMH databases). The reconstruction should be in SBML format and saved as a .xml file. Additionally, it is important that the reconstruction have a biomass reaction, and that the gene names in the reconstruction match the gene names in the TnSeq data.

### Exchange Reactions
Exchange reactions provide a way of setting the growth medium for the simulations. Here, you should provide a tab-delineated text file providing the reaction identifiers of the exchange reactions in the 1st column and the maximal influx rate (a negative value) in the 2nd column (if unsure of what values to use, using -10 for all reactions should provide a reasonable starting point). The closer the medium resembles the experimental conditions, the better the output is likely to be. Although Tn-Core will run so long as there is at least one reaction in this file, we recommend at minimum listing the carbon source, the nitrogen source, the phosphorus source, and the sulphur source.

### Objective Reaction
This should indicate the biomass reaction. Here, you should provide a tab-delineated text file consisting of one line: the reaction identifier of the biomass reaction, followed by the objective coefficient (should always be 1).

### TnSeq Data
This should be a tab-delineated text file containing the TnSeq data. The 1st column should be the gene names (ensure the gene names are the same as the gene names in the metabolic reconstruction, and the 2nd column should be a summary statistic of the TnSeq data. The TnSeq data should not be log-transformed, and should be in a format where the lower the number, the more important the gene. For example, it could consist of the number of reads mapping to the gene divided by the gene length.


## Optional Inputs

### RNAseq Data
This should be a tab-delineated text file containing the RNAseq data. The 1st column should be the gene names (ensure the gene names are the same as the gene names in the metabolic reconstruction, and the 2nd column should be the RNAseq data as either RPKM or TPM.

### Growth Fraction
This should be a value greater than 0 and lesser than or equal to 1 (i.e., 0 < n ≤ 1). This number sets the minimal rate that the output model can produce biomass relative to the input genome-scale metabolic model. For example, if the input model produces 0.3 g of biomass per hour per gram of biomass, and this value is set to 0.5, then the output model must produce at least 0.15 g of biomass per hour per gram of biomass. If no value is entered, the default is 0.5.

### Expression Threshold
This should be the minimum RPKM or TPM value for a gene to be considered 'highly-expressed'. This could be, for example, the average RPKM value of all genes. If no value is given, the default is to calculate the threshold as 0.02% the sum of all the expression values.


## Outputs

### Excel File
The Excel file contains three sheets summarizing the core metabolic reconstruction. The first sheet include information on the reactions. The following columns are included: XXX. The second sheet includes information on the metabolites present in the core metabolic reconstruction. The following columns are included: XXX. The third sheed includes information on the genes present in the core metabolic reconstruction. The following columns are included: XXX.

### MATLAB File
The MATLAB file contains the core metabolic reconstruction as a COBRA-formatted model.


## Sample Data

Five files are provided for testing the Tn-Core webserver.
input_model.xml - A sample file to enter in the 'Metabolic Reconstruction' field.
Exchange_reactions.txt - A sample file to enter in the 'Exchange Reactions' field.
Objective_reaction.txt - A sample file to enter in the 'Exchange Reactions' field.
TnSeqData.txt - A sample file to enter in the 'TnSeq Data' field.
RNAseqData.txt - A sample file to enter in the 'RNAseq Data' field.


## Citation

If you find the output of the Tn-Core webserver to be helpful, we ask you to consider including a statement such as the following in the Methods section of your manuscript:

Transposon-sequencing data was integrated with the metabolic reconstruction using the Tn-Core webserver (ref), which is dependent on MATLAB 2016b (mathworks.com), the iLOG CPLEX solver v.XXX (ibm.com), the COBRA Toolbox (ref), the TIGER Toolbox v.XXX (ref), the Tn-Core Toolbox v.XXX (ref), FASTCORE v.XXX (ref), GIMME (ref), libSBML (ref), and XXX.
