# AVITI processing

# Quick summary of processing commands

The first step in processing an AVITI run is to run `bases2fastq`. This has been updated (04/04/2024) to the latest version (v1.7).

### Create fastq files

``` bash
nohup  ~/bases2fastq -p 16 --run-manifest ~/illuminaprocessing/aviti_run_manifest.csv [run_folder] [output_folder]
```

This uses a custom run manifest that creates index fastq files and does not demultiplex.

### Copy data to /primary and demultiplex

``` bash
cd /primary
mkdir [run_folder]
cd [run_folder]
~/illuminaprocessing/create_external_run_folder_structure_1_lane.sh

nohup cp /data/[output_folder]/Samples/DefaultProject/DefaultSample/*fastq.gz Unaligned/Project_External/Sample_lane1/ > copy.log &

rename DefaultSample lane1_NoIndex_L001 Unaligned/Project_External/Sample_lane1/*fastq.gz

nohup ~/illuminaprocessing/split_barcodes_aviti_dual_index [run_folder] > barcode_splitting.log &
```

------------------------------------------------------------------------

# Breakdown of processing steps

Code blocks here are the commands that were used to process the first test run.

This seems to have worked ok - it's sample 6041, lane 8639 in Sierra.

## bases2fastq

``` bash
nohup  ~/bases2fastq -p 16 --run-manifest ~/illuminaprocessing/aviti_run_manifest.csv 20240306_AV240405_InstallPV-SideA-AV240405-06Mar2024 20240306_AV240405_InstallPV-SideA-AV240405-06Mar2024/Unaligned
```

More details of the run manifest are in the later section [Custom run manifest]

## Demultiplexing

The `split_barcodes` script, in its existing format, does not work with the AVITI data (even after renaming files) because...

-   It gets file name and number info from the Illumina file RunInfo.xml which AVITI does not produce.

-   It expects index reads to be named \_R2/\_R3, not I1, I2.

-   If we run `create_external_run_folder_structure.sh`, it creates 8 lanes, and so split_barcodes then looks for 8 lanes of data.

For now, I've hardcoded some options in to the script `split_barcodes_aviti_dual_index` so that it expects R1, R2, I1, I2 files.\
There is also an accompanying script `split_barcodes_aviti_single_index` that doesn't expect I2, but this hasn't been tested.

There is also a very simple script `create_external_run_folder_structure_1_lane.sh` to just create one lane.

Copying the test run over to /primary\
I did try using the run folder name (20240306_AV240405_InstallPV-SideA-AV240405-06Mar2024) but Sierra rejected it as too long.

``` bash
cd /primary
mkdir 20240306_AV240405_InstallPV-SideA
cd 20240306_AV240405_InstallPV-SideA
~/illuminaprocessing/create_external_run_folder_structure_1_lane.sh

nohup cp /data/AV240405/20240306_AV240405_InstallPV-SideA-AV240405-06Mar2024/Unaligned_v1.7/Samples/DefaultProject/DefaultSample/DefaultSample*L001*fastq.gz Unaligned/Project_External/Sample_lane1/ > copy_L1.log &
```

In the `split_barcodes` script, the files are found using this line of perl code:

``` perl
my @files = <$data_folder/$run_folder/Unaligned/Project*/Sample_lane$lane/lane${lane}_NoIndex_L*_${read_number}.fastq.gz>;
```

Essentially, they need to be named:

lane1_NoIndex_L001_R1.fastq.gz\
lane1_NoIndex_L001_R2.fastq.gz\
lane1_NoIndex_L001_I1.fastq.gz\
lane1_NoIndex_L001_I2.fastq.gz

``` bash
rename DefaultSample lane1_NoIndex_L001 Unaligned/Project_External/Sample_lane1/*fastq.gz
```

Demultiplex using the slightly modified version of the split_barcodes script.

``` bash
nohup ~/illuminaprocessing/split_barcodes_aviti_dual_index 20240306_AV240405_InstallPV-SideA > barcode_splitting.log &
```

Hopefully there are now demultiplexed fastq files ready for downstream processing.

------------------------------------------------------------------------

# More details

## bases2fastq

The basecalling software is called `bases2fastq` and can be downloaded from\
<https://go.elementbiosciences.com/bases2fastq-download>

Usage:

``` bash
bases2fastq --run-manifest [run_manifest.csv] [run_folder] [output_folder]
```

A default run manifest is produced with the sequencing run and this is used by `bases2fastq` to demultiplex and convert to fastq. We don't want to demultiplex at this point - there are too many times when the barcodes provided are not quite correct, so we have to manually correct the sequences and re-run the demultiplexing. We therefore want to create the fastq files first and then demultiplex.

## Custom run manifest

To get fastq files for the indexes we need to set:

```         
I1FastQ True
I2FastQ True
```

By default these are false and no index fastq files are produced.

<https://docs.elembio.io/docs/run-manifest/settings/#umi-index-and-control-settings>

We have created a [run manifest](https://github.com/s-andrews/illuminaprocessing/blob/master/aviti_run_manifest.csv) that produces index fastq files. This is in the illuminaprocessing GitHub repo.

### Contents of aviti_run_manifest.csv

```         
[SETTINGS],,,
SettingName,Value,Lane,
SpikeInAsUnassigned,FALSE,,
R1FastQMask,R1:Y*N,1+2,
R2FastQMask,R2:Y*N,1+2,
,,,
# Index mask is set to index length with FASTQ generated for Index 1 and 2.,,,
I1Mask,I1:Y*,1+2,
I2Mask,I2:Y*,1+2,
I1FastQ,True,,
I2FastQ,True,,
```

## Pipeline server

The /data/AV240405 folder has all the AVITI runs in so far

### Running bases2fastq on the pipeline server

Example command for processing the test run from the AV240405 folder:

``` bash
nohup  ~/bases2fastq --legacy-fastq -p 16 --run-manifest ~/illuminaprocessing/aviti_run_manifest.csv 20240306_AV240405_InstallPV-SideA-AV240405-06Mar2024 20240306_AV240405_InstallPV-SideA-AV240405-06Mar2024/Unaligned
```

The run folder and output directory will need to be changed each time, but the first part of the command can remain the same (up to `.csv`) - unless we need to change the run manifest.

### Output files

fastq files located in `/data/AV240405/[bases2fastq_output_dir]/Samples/DefaultProject/DefaultSample/`

--legacy-fastq put half in L001 and half in L002. Without that option all R1 went into 1 file.

```         
DefaultSample_S1_L001_I1_001.fastq.gz
DefaultSample_S1_L001_I2_001.fastq.gz
DefaultSample_S1_L001_R1_001.fastq.gz
DefaultSample_S1_L001_R2_001.fastq.gz
```

The initial test run was PhiX with 4 multiplexed samples.

#### Note - SpikeInAsUnassigned setting

From https://docs.elembio.io/docs/run-manifest/settings/#umi-index-and-control-settings

```         
A Boolean value that specifies whether to categorize PhiX Control Library reads as unassigned: When libraries are absent or each lane contains only one unindexed library, the value defaults to true. You can reset it to false. When indexed libraries are present, the value defaults to false. If you reset it to true, Bases2Fastq displays a warning.
```
