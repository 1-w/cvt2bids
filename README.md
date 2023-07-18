# cvt2bids

---

A tool to autogenerate a BIDS conform dataset from dicom files.

Depends on a modified Version of [dcm2bids](https://github.com/1-w/Dcm2Bids) and (currently not yet supported) [nii2dcm](https://gitlab.com/lab_tni/projects/nii2dcm).

---

## Prerequisites

Read about dcm2bids (https://github.com/UNFmontreal/Dcm2Bids) and dcm2niix (https://github.com/rordenlab/dcm2niix), it's important for converting the right dcm files to the right bids files! 


Best to work in a virtual env, for example:

```
conda env create -f environment.yml
conda activate cvt2bids
```

---

## Install

```
pip install .
```

---

## Usage

Example:
```
cvt2bids -d sourcedata -o rawdata -c configs/example.json -m
```

optional arguments:

  ```-h, --help``` show this help message and exit
  
  ```-d DICOM_PATH, --dicom_path DICOM_PATH ``` BIDS conform dir containing all relevant niftis. participants.tsv needs to allow a mapping between the files in sourcedata and the participant_ids.
  
 ``` -o OUT_PATH, --out_path OUT_PATH``` provide output directory path. If it does not include a participants.tsv file, a new one will be generated from dicom data
  
  ```-c CONFIG_PATH, --config_path CONFIG_PATH``` provide the path to a valid config file.
  
  ```-i ID, --id ID```        Single participant_id. Only this id will be processed from participants.tsv file. If no participants.tsv file is provided, all found DICOMS will be stored under this id
  
  ```-p PARTICIPANTS_FILE, --participants_file PARTICIPANTS_FILE ```if participants.tsv file included somewhere other than out_path
                          
  ```--dcm DCM      ```       convert NIFTIS back to DICOMS, options: a = anonymize, d = defaced

  ``` -m, --multiproc   ```    control whether multi- or singlecore processing should be used

### Find sequences that were not included in the config

1. Execute command

2. ```cd <output directory>```

3.1 ```grep tmp_dcm2bids/sub-*/*.json -e SequenceName```

You can also check if there were several pairings (i.e. multiple entries in the config matched for the same file:

3.2 ```grep tmp_dcm2bids/log/*.log -e "Several Pairing"```

Please put the sequences like into the existing config repo like described here:
https://gitlab.com/lab_tni/projects/lab2bids_configs

More about config creation can also be found here:
https://unfmontreal.github.io/Dcm2Bids/docs/how-to/create-config-file/

Please note that we use regex matching instead of shell-style pattern matching!

Find more about regex here:
https://regex101.com/
