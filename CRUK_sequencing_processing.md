# Processing external sequencing data from CRUK

## Download

We receive an email that looks something like this:

    A sequencing run containing your libraries has been published.
    Remember that your data will remain on our FTP server for 30 days. Please make sure you have downloaded it before Friday 5 August.

    Run: 220705_A00489_1414_AH7HTTDRX2 lanes 1, 2

    SLX-22121
    Projects:
    BABRAHAMsequencing
    Samples:
    WT1lv (BABRAHAMsequencing)
    WT2lv (BABRAHAMsequencing)
    WT3lv (BABRAHAMsequencing)
    WT4lv (BABRAHAMsequencing)
    WT5lv (BABRAHAMsequencing)
    Mut1lv (BABRAHAMsequencing)
    Mut2lv (BABRAHAMsequencing)

Create a run folder in `/bi/scratch/run_processing/`
e.g. `mkdir 220705_CRUK_external`

Go into that folder and download the data by adapting the following
command (change the SLX number):

    nohup wget --user=babraham_kokkogonzales --password=noisyrhino61 ftp1.cruk.cam.ac.uk:SLX-22121* &
    
### Downloading data that hasn't gone through the BI sequencing facility   

Occasionally requests come in from people via email who have used a different account at CRUK. They should provide the ftp details including the user name and password, and the data can be downloaded similarly to the command above.   
If the samples have gone through the BI sequencing facility they should be in the queue on Sierra, and a flowcell can be created, as described [below](#create-flowcell).   
If the samples are not on Sierra, then they will have to be added before a flowcell can be created.

#### Creating and receiving a sample in Sierra

**_Only do this if the sample does not already exist!_**   
   
In Sierra:

    Create sample
    Show Queue
    Receive sample
    Pass Individual QC
    Pass final QC

Then a flowcell can be created.

## Create flowcell on Sierra and set up folder structure

### Create flowcell

Select the New flowcell option in Sierra menu.  
Use the run folder name you created in /bi/scratch/run_processing/ as
the Serial Number.  
Select samples, Create Flowcell

### Create folder structure on pipeline server

    ssh SBSUser@pipeline1
    cd /primary/
    mkdir 22xxxx_CRUK_external
    cd 22xxxx_CRUK_external/
    ~/illuminaprocessing/create_external_run_folder_structure.sh

This is now ready for files to be copied to using copy_back_files, but
first we want to rename them.

# Rename files

Cellranger is very fussy about filenames, so we need to get rid of
certain characters `. -`, and capitalise s, r, i etc. Even if we’re not
running cellranger, we still want to add the sample names and lane
number to the fastq files.

The rename_samples.sh script takes the contents.csv file from CRUK and
uses that to rename fq files.

We go from something like this

    SLX-22125.NEBNext16.H7HTTDRX2.s_2.r_1.fq.gz

to:

    SLX22125_NEBNext16_Mut2k_S2_L002_R1.fastq.gz

or for using with cellranger:

    SLX22125_NEBNext16_Mut2k_S2_L002_R1_001.fastq.gz

The script needs updating for the \_001 to be an option - we don’t want to add
that if we’re not using cellranger, as bismark (maybe others but not
sure) do not recognise paired end files, they expect xxxx_R1.fastq.gz
and xxxx_R2.fastq.gz.

    ~/illuminaprocessing/rename_CRUK_samples.sh SLX-22121.H7HTTDRX2.s_1.contents.csv 1 H7HTTDRX2
    ~/illuminaprocessing/rename_CRUK_samples.sh SLX-22125.H7HTTDRX2.s_2.contents.csv 2 H7HTTDRX2

# Tidy the extra files

    mkdir raw_data
    mv *lostreads* raw_data/
    mv *bcl2fastq.zip raw_data/
    mv *md5sums.txt raw_data/

    nohup tar -zcvf raw_data_L001_.tar.gz raw_data &

# Running standard pipelines

For bulk RNA-seq, bisulfite etc, the standard nextflow pipelines can be
used, then copy_back_files to copy them to the pipeline server (Sierra).

# Processing 10x multiome data  

If the libraries have been prepared using the 10x multiome protocol for scRNA and scATAC-seq, there will be one set of gene expression fastq files and one set of ATACseq fastq files. These need to be processed together with cellranger-arc.

## Creating library files  

One of the arguments passed to cellranger-arc is a library file which contains the location of the data for each sample. This will comprise a header line and then 2 further lines specifying the data locations. For example:

    fastqs,sample,library_type
    /bi/scratch/run_processing/220620_CRUK_external/SLX22124,SLX22124_SITTC1_AME_E,Gene Expression
    /bi/scratch/run_processing/220620_CRUK_external/SLX22107,SLX22107_SINAC1_AME_E,Chromatin Accessibility

One library file per sample is required. If there are only a couple of samples, these can be created manually. For more samples, a script can be used - this needs a bit of polishing before adding to this repo, so I'll just put the code here for now:

    #!/bin/bash
    #usage:  ./create_libraries.sh rna_sample_sheet atac_sample_sheet
    RNA=$1
    ATAC=$2
    while read -r LINE; do
        LINEARRAY=(${LINE//,/ })
        SLX=${LINEARRAY[0]}
            SLX2=$(echo $SLX | tr -d -)
        BARCODE=${LINEARRAY[1]}
        NAME=${LINEARRAY[3]}
        OUTFILE=libraries_${NAME}.csv
        echo "fastqs,sample,library_type" > $OUTFILE
        echo "/bi/scratch/run_processing/220725_CRUK_external/RNA,${SLX2}_${BARCODE}_${NAME},Gene Expression" >> $OUTFILE
    done < $RNA

    while read -r LINE; do
        LINEARRAY=(${LINE//,/ })
        SLX=${LINEARRAY[0]}
        SLX2=$(echo $SLX | tr -d -)
        BARCODE=${LINEARRAY[1]}
        NAME=${LINEARRAY[3]}
        OUTFILE=libraries_${NAME}.csv
        echo "/bi/scratch/run_processing/220725_CRUK_external/ATAC,${SLX2}_${BARCODE}_${NAME},Chromatin Accessibility" >> $OUTFILE
    done < $ATAC

## Running cellranger-arc

This is an example cellranger-arc command for human multiome data:

    ssub --mem 36G --cores 32 -o libraries_AME_E.log -j ArcRanger9 --email /bi/apps/cellranger-arc/cellranger-arc-2.0.0/bin/cellranger-arc count --id=libraries_AME_E --reference=/bi/apps/cellranger-arc/references/refdata-cellranger-arc-GRCh38-2020-A-2.0.0 --libraries=libraries_AME_E.csv --localcores=32 --localmem=32
    
### Creating cellranger-arc commands

If there are many samples, a bash command similar to this can be useful for creating a set of commands - it will write these to a file so that they can be checked before submission.

    for i in libraries*csv; do ID=$(sed 's/.csv//' <<< $i); echo "ssub --mem 36G --cores 32 -o ${ID}.log -j ArcRanger9 --email /bi/apps/cellranger-arc/cellranger-arc-2.0.0/bin/cellranger-arc count --id=${ID} --reference=/bi/apps/cellranger-arc/references/refdata-cellranger-arc-GRCh38-2020-A-2.0.0 --libraries=${i} --localcores=32 --localmem=32" >> cellranger_arc_commands.sh; done
    
## Renaming output files for copying over to Sierra

cellranger-arc will write output files to the folder specified in the --id argument. A script can be used to transform the output filenames into Sierra/copy-back_files compatible names.

    /bi/scratch/scripts/prepare_10X_folder_for_copy_back_multiome.pl [output_folder_name] [L00x]
    
The copy_back_files script can then be run to copy the files across to Sierra

    module load copy_back_files
    copy_back_files [run_folder_name] *

# Extracting reads from lostreads files

This does not need to be done for most runs, though if something has gone
wrong with the demultiplexing e.g. incorrect barcodes were supplied, or no
barcodes were supplied, then we can use the CRUK demultiplexing scripts to extract sequences from the lostreads files.

The CRUK demultiplexing script is described here:
<https://genomicsequencing.cruk.cam.ac.uk/submission/help/demultiplexing.jsp>

This is an example of a run where none of the samples had been split.  
<https://www.bioinformatics.babraham.ac.uk/cgi-bin/helpdeskuser.cgi?action=show_job&public_id=unifyblink>

This is another example where one of the barcodes had been mislabelled,
so we needed to extract one barcode from the lostreads fastq file.  
<https://www.bioinformatics.babraham.ac.uk/cgi-bin/helpdeskuser.cgi?action=show_job&public_id=beeprose>

Example of demultiplexing command:

    ssub -o zzlog_SLX22121.txt --email --mem 10G --cores 8 ~/demultiplexer.rhel/demuxFQ -b SLX22121_NoCode_L001_R1.fastq -c -d -i -e -t 0 -s SLX22121_demux_report_R1.txt demux_SLX22121.txt SLX-22121.H7HTTDRX2.s_1.r_1.lostreads.fq.gz
    ssub -o zzlog_SLX22125.txt --email --mem 10G --cores 8 ~/demultiplexer.rhel/demuxFQ -b SLX22125_NoCode_L001_R1.fastq -c -d -i -e -t 0 -s SLX22125_demux_report_R1.txt demux_SLX22125.txt SLX-22125.H7HTTDRX2.s_2.r_1.lostreads.fq.gz
