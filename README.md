# cvt2bids

---

A tool to autogenerate a BIDS conform dataset from dicom files.

Depends on a modified Version of [dcm2bids](https://github.com/1-w/Dcm2Bids) and (currently not yet supported) [nii2dcm](https://gitlab.com/lab_tni/projects/nii2dcm).

---

## Prerequisites

dcm2niix v1.0.20201102

Best to work in a virtual env, for example:

```
conda env create -f environment.yml
conda activate cvt2bids
```

---

## Install

```
git clone https://github.com/1-w/cvt2bids.git
cd cvt2bids
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
                        
 ``` -s SUBFOLDER, --subfolder SUBFOLDER ```if only a specific subfolder in a subjects directory should be searched for DICOMS
  
  ```--dcm DCM      ```       convert NIFTIS back to DICOMS, options: a = anonymize, d = defaced
 ``` -m, --multiproc   ```    control whether multi- or singlecore processing should be used

### Workflow

1. Execute command

2. ```cd <output directory>/tmp_dcm2bids/log```

3. ```grep *.log -e "No Pairing" >> all_unpaired.txt```

4. Open python

5. 
```
#imports
import pandas as pd
import re

#read unpaired sequence list
df = pd.read_csv(<path to all_unpaired.txt>,header=None)

#clean the list
df['sequence_names'] = df[0].apply(lambda x: x.split('  <-  ')[1])
print(df.sequence_names.unique())
df['sequence_names'] = df['sequence_names'].apply(lambda x: re.sub(r'^[0-9]*_','',x))
df['sequence_names'] = df['sequence_names'].apply(lambda x: re.sub(r'^[0-9]*.?_','',x))
df['sequence_names'] = df['sequence_names'].apply(lambda x: re.sub(r'_[0-9]*$','',x))

#only use unique sequence names
unmatched_sequences = df.sequence_names.unique()

#refine template matching to sequence names
#add the matched templates to the config file like described below

new_template = r'.*preop_ep2d_diff_b0_p4_17_preop_ep2d_diff_b0_p4.*'
unmatched_sequences = unmatched_sequences[
  unmatched_sequences.apply(lambda x: not bool(re.search(new_template,x)) )
]

#repeat until unmatched_sequences is empty
```

Please put the sequences like into the existing config repo like described here:
https://gitlab.com/lab_tni/projects/lab2bids_configs

More about config creation can also be found here:
https://unfmontreal.github.io/Dcm2Bids/docs/how-to/create-config-file/

Please note that we use regex matching instead of shell-style pattern matching!

Find more about regex here:
https://regex101.com/
