Processing Illumina Runs from Babraham
======================================

This document describes the procedures to process new Illumina runs from the Babraham sequencing pipeline.  Please update this document as you make changes to the scripts we're using so that this guide is always up to date.

General Overview
================

The summary of the movement of data during the sequencing pipeline is laid out below.  The main parts of the system are:

1) The PC attached to individual sequencers

2) The pipeline server - a linux server located in B580 which has a large directly attached storage array

3) The central illumina cluster, a large scale storage system which is the primary data store for all sequence data.  It appears on the pipeline server under /primary (rw) and on the compute cluster under /bi/seqfac/seqfac (ro) and on the web server under /data/private/sierra/data (ro)

4) The compute cluster - a ROCKS cluster of many hundreds of cores in B570

5) Bilin3 - the bioinformatics web server which hosts Sierra, the LIMS system for the sequencing facility which manages the metadata for all runs, and runs various monitoring jobs to alert us when runs need processing.

The data process for the sequencing pipeline is that data is initially generated on the PC of an individual sequencer.  This data is then base called on the PC from where it is copied to a mapped network share, which appears as drive Z: on the PC, but is actually the /data partition of the pipeline server served out via cifs.

Once the run is complete a cron job on bilin3 (web server) will spot that the run complete flag has been set but that no further data is avaialble and will email the bioinformatics group to say that a run is ready to be processed.

The initial processing consists of converting the illumina base call (BCL) files into a standard fastq format using Illuminas conversion software.  By default this also generates multiple fastq files per sample, but we merge these together so that only one fastq file per read per sample is produced.  We also create fastq files for barcode reads so we can analyse these and split them later on.

After the data has been converted to fastq format it is copied from the /data partition of the pipeline server - which is a working area, to the /primary folder which is the permanent storage area.  Only a subset of the data in the run folder is copied to the permanent storage to save on space.  Once this copy is compelte and the data has been verified on the permanent storage, the copy of the data on /data can be deleted.

Once the run folder is on the central cluster we can split the fastq files according to any barcodes which might be present so that we get data for each individual sub-sample in the lane.  This is also done on the pipeline server.

Once the samples have been split we can do the initial data analysis.  This is performed on the compute cluster using one of the standard set of analysis pipelines built into the clusterflow system.  The output from these jobs is writte to a temporary area on the cluster before finally being copied back to the pipeline server where they will finally reside.

Processing details
==================

1) Base calling, fastq creation, data backup
--------------------------------------------
Log into the SBSUser account on pipeline1 (the pipeline server) via ssh. Ask someone from bioinformatics if you don't know the password to this account.

Move to the /data directory and locate the run folder you want to process.  Check within Sierra to ensure this is the run you want to process.

Run:

 nohup ~/illumina_run_processing/process_run_folder [run folder name] > [run folder name].log &

This will do the base calling and backup of the called data, which will then appear under /primary.

Once you have validated the data under /primary you can delete the original run folder from /data.


2) Barcode splitting
--------------------
Log into the SBSUser account on pipeline1 (the pipeline server) via ssh. Ask someone from bioinformatics if you don't know the password to this account.

Look on Sierra to check whether any of the samples have barcodes.  If there are samples which look like they should have barcodes, but which don't have any barcode information then email the users to check and defer the processing of those samples.

To run the barcode splitting run:

cd /primary/[run folder name]

nohup ~/illumina_run_processing/split_barcodes [run folder name] > split_barcodes.log &

This will process all lanes from the run.

If you only want to process some lanes then you can append lane numbers after the run folder name, separated by spaces.

nohup ~/illumina_run_processing/split_barcodes [run folder name] 1 4 6 > split_barcodes.log &


3) Mapping and QC
-----------------
Log onto the compute cluster - you can do this under your normal user account.

Move to the /bi/scratch/run_processing folder

Run:

nohup  ~/illumina_run_processing/analyse_run_folder [run folder name] > [run folder name].log &

All of the lanes should be analysed through the appropriate clusterflow pipelines and the data should be copied back onto the pipeline server from where it will appear in Sierra.

You will be notified about completed analyses through the normal cluterflow emails.

Once the whole run has completed look though the log ([run folder name].log) to check that everything worked OK.  Once you're happy then you can delete the run folder under /bi/group/run_processing/. At this stage you can also delete the original sequence folder under /data on the pipeline server.

If there are lanes which weren't processed due to either not being annotated, or not having an associated clusterflow pipeline then either process these manually, or inform whoever is responsible for them that they are ready.

Once the run has completed processing you can delete the processing folder in /bi/scratch.


Processing data from Sanger
===========================

Some groups will do their sequencing at the Sanger centre.  We want to import this data into Sierra so we can keep a consistent view of all data at the institute.  The proceedure for processing this data is therefore somewhat different.

Data Annotation
---------------

Data from the Sanger comes pre-split by barcode and is delivered as a set of cram files.  The annotations will be emailed from Sanger to the bioinformatics group and will consist of a set of user supplied sample descrptions, the barcode they used and the run and lane ids of the files for that sample.  Eg;

4_2_ETOH_2i (tagged with 1)	15945_1#1	15945_2#1	15951_1#1	15951_2#1
4_3_ETOH_2i (tagged with 2)	15945_1#2	15945_2#2	15951_1#2	15951_2#2
F2S2_sperm (tagged with 3)	15945_1#3	15945_2#3	15951_1#3	15951_2#3
Black6_sperm (tagged with 4)	15945_1#4	15945_2#4	15951_1#4	15951_2#4
4_2_4OHT_2i_low (tagged with 17)	15945_1#17	15945_2#17	15951_1#17	15951_2#17
4_3_4OHT_2i_low (tagged with 18)	15945_1#18	15945_2#18	15951_1#18	15951_2#18
4_1_ETOH_2i_low (tagged with 19)	15945_1#19	15945_2#19	15951_1#19	15951_2#19

Downloading data
----------------

The data initially needs to be downloaded to the cluster and processed into fastq.gz files which can be uploaded to Sierra.

The data can be downloaded via ftp from ngs.sanger.ac.uk in scratch/project/ncb/Babraham.  Make sure that you do the download in BINARY mode and that you only pull the cram files for the run you're working on (there may be several runs files in that folder).  Using the example run above (15945), you'd do;

$ ftp ngs.sanger.ac.uk
Connected to ngs.sanger.ac.uk (193.62.203.121).
220 ProFTPD 1.3.4a Server (NGS ftp server) [::ffff:193.62.203.121]
Name (ngs.sanger.ac.uk:andrewss): anonymous
331 Anonymous login ok, send your complete email address as your password
Password:
230 Anonymous access granted, restrictions apply
Remote system type is UNIX.
Using binary mode to transfer files.
ftp> cd scratch/project/ncb/Babraham
250 CWD command successful
ftp> binary
200 Type set to I
ftp> prompt off
Interactive mode off.
ftp> mget 15945*cram

Initial conversion and processing
---------------------------------

The first step of processing is to convert the data from cram to fastq.gz format, and to change the names to the format needed by Sierra and to include the users sample names.

To do this you need to make up a sample sheet from the annotation given by Sanger.  The file you make up needs to be a tab delimited file with the following columns:

1) sampleID - the run number and lane from sanger (eg 15945_1)

2) barcode - the numeric barcode used by sanger (eg 1 if the original file said 'tagged with 1')

3) name - the users sample name (eg Black6_sperm)

4) lane - the lane number for the flowcell on sierra you're going to put this data in (eg 3)

To do the processing (rename cram, cram to bam, sort bam, bam to fastq, compress fastq) you then simply need to do;

nohup ~/illumina_run_processing/sanger2babraham [sample_sheet_name] > sanger2babraham.log &


Uploading data to Sierra
------------------------

Once the conversion is complete you'll have a set of fastq.gz files which need to be uploaded into Sierra.  Before you can do this you'll need to make up a run on Sierra to put the samples in.

The first thing to do will be to make up the appropriate Sample entries in Sierra if these aren't there already.  You can do this using the information supplied by Sanger / the user to specify the type of run and the search database etc.  For the barcodes the sanger2babraham script will write out a sierra barcode sheet for each of the lanes it processes so you can just use that to input the barcode sequences.  You'll have to work out the run type (single vs paired end and read length) from looking at the generated fastq files.

Once you've created the samples you need to receive them and make them pass QC using the controls under "Show Queue" in Sierra.  Then you can create a new flowcell for this run.  Add in the samples you processed and set any remaining lanes to be empty lanes so you can make the run.

Once you've done that you'll need to create a basic folder layout to put the data in.  To do this, log into the pipeline server and run:

~/illumina_run_processing/make_run_folder_layout [run folder name] [number of lanes]

Once you've done this then you can upload the fastq.gz files into this run.  To do this log into the cluster and move to the folder where you processed the data and do:

module load copy_back_files
copy_back_files [run folder name] *fastq.gz


Analysing Sanger Runs
---------------------
Once you've uploaded the Sanger data into Sierra then you can analyse it using exactly the same procedure as for Babraham runs, so just look at the existing analysis section above.


