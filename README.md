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

