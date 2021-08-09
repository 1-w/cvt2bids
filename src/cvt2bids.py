#%%
import os
import json
import sys
import pandas as pd
import subprocess
import numpy as np
import multiprocessing
from os.path import join as opj
import argparse
import pydicom as pydi
import glob

import dcm2bids

#%%
def find_corresponding_bids(id, df):
    id_names = [x for x in df.columns if x in ['osepa_id', 'lab_id','neurorad_id','folder_id']]
    
    for i,r in df.iterrows():
        for m in [r[id_name] for id_name in id_names]:
            if str(id) in m: 
                return r.participant_id
    #print(id)
    return str(-1)

def start_proc(cmd):
    print("Running:",cmd)
    proc = subprocess.Popen(cmd)
    proc.wait()

def preproc_ids(df):
    if 'osepa_id' in df.columns:
        df.osepa_id = df.osepa_id.apply(lambda x: [t.strip() for t in str(x).split(',')] if x is not np.nan else [])
    if 'lab_id' in df.columns:
        df.lab_id = df.lab_id.apply(lambda x: [t.strip() for t in str(x).split(',')] if x is not np.nan else [])
    if 'neurorad_id' in df.columns:
        df.neurorad_id = df.neurorad_id.apply(lambda x: [t.strip() for t in str(x).split(',')] if x is not np.nan else [])
    if 'folder_id' in df.columns:
        df.folder_id = df.folder_id.apply(lambda x: [t.strip() for t in str(x).split(',')] if x is not np.nan else [])
    return df

def ids2string(df):
    if 'osepa_id' in df.columns:
        df.osepa_id = df.osepa_id.apply(lambda x: ','.join(x))
    if 'lab_id' in df.columns:
        df.lab_id = df.lab_id.apply(lambda x: ','.join(x))
    if 'neurorad_id' in df.columns:
        df.neurorad_id = df.neurorad_id.apply(lambda x: ','.join(x))
    if 'folder_id' in df.columns:
        df.folder_id = df.folder_id.apply(lambda x: ','.join(x))
    return df

def convert2abs(path):
    if os.path.isabs(path):
        return path
    else:
        return os.path.normpath(opj(os.getcwd(), path))

def get_max_bids_id(df):
    ids = df.participant_id.apply(lambda x: int(x.split('-')[1]))
    if len(ids) ==0:
        return 1
    
    max_id = np.max(np.array(ids))
    if max_id >= 1:
        return max_id
    else:
        return 1

def extract_participant_info(dcm_path):
    #return dict with participant info from dcm header
    infotags = {'institution_name':("0x0008","0x0080"),
        #'acquisition_date':("0x0008","0x0022") ,
        'name':("0x0010","0x0010"),
        'id':("0x0010","0x0020"),
        'dob':("0x0010","0x0030"),
        'sex':("0x0010","0x0040"),
        #'other_ids':("0x0010","0x1000"),
        #'other_names':("0x0010","0x1001"),
        #'birth_name':("0x0010","0x1005"),
        #'age':("0x0010","0x1010"),
        'size':("0x0010","0x1020"),
        'weight':("0x0010","0x1030")}
    subject_info = {}

    for key in infotags:
        subject_info[key] = []

    for f in os.listdir(dcm_path):
        dcm_file = glob.glob(opj(dcm_path,f)+'/*.dcm')[0]
        if dcm_file:
            dcm = pydi.dcmread(dcm_file)
            for key in infotags:
                tg = pydi.tag.Tag(infotags[key])
                if tg in dcm:
                    if str(dcm[tg].value) not in subject_info[key]:
                        subject_info[key].append(str(dcm[tg].value))

    returnDict = {}
    for key in subject_info:
        returnDict[key] = ','.join(subject_info[key])
            
    return returnDict

#%%
def get_arguments():
    """Load arguments for main"""
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=""" Convert DICOMS to NIFTIS and back, with possible defacing and header annonymization {}""".format( '0.1.0' #TODO
        ), epilog=""" Documentation not yet at https://github.com/1-w/cvt2bids """, )

    parser.add_argument(
        "-d", "--dicom_path", required=True, help="BIDS conform dir containing all relevant niftis. participants.tsv needs to allow a mapping between the files in sourcedata and the participant_ids."
    )

    parser.add_argument(
        "-o","--out_path", required=True, help="provide output directory path. If it does not include a participants.tsv file, a new one will be generated from dicom data"
    )

    parser.add_argument(
        "-c","--config_path", required=True, help="provide the path to a valid config file."
    )

    parser.add_argument("-i", "--id", required=False, help="Single participant_id. Only this id will be processed from participants.tsv file. If no participants.tsv file is provided, all found DICOMS will be stored under this id") #TODO

    parser.add_argument(
        "-p", "--participants_file", required=False, help="if participants.tsv file included somewhere other than out_path"
    )

    parser.add_argument(
        "-s", "--subfolder", default='',required=False, help="if only a specific subfolder in a subjects directory should be searched for DICOMS"
    )

    parser.add_argument(
        "--dcm",
        required=False,
        help="""
        convert NIFTIS back to DICOMS, options: a = anonymize, d = defaced""",
    )

    parser.add_argument(
        "-m",
        "--multiproc",
        action="store_true",
        help="""
        control whether multi- or singlecore processing should be used""",
    )

    args = parser.parse_args()
    return args


#%% prepare conversion 
def main():
    args = get_arguments()

    dicom_path = convert2abs(args.dicom_path)
    out_path = convert2abs(args.out_path)
    os.makedirs(out_path,exist_ok=True)

    config_file_path = convert2abs(args.config_path)

    if args.participants_file:
        participants_file = convert2abs(args.participants_file)
        participants = pd.read_csv(participants_file,sep='\t',dtype=object)
    else:
        if os.path.isfile(opj(out_path, 'participants.tsv')):
            participants_file = opj(out_path, 'participants.tsv')
            participants = pd.read_csv(participants_file,sep='\t',dtype=object)
            
        else:
            #generate participants.tsv
            participants_file = opj(out_path, 'participants.tsv')
            participants = pd.DataFrame(columns=['participant_id','folder_id'],dtype=object)

    if 'folder_id' not in participants.columns:
        print("Adding 'folder_id' column...")
        participants['folder_id'] = ''

    if args.id:
        if args.id in participants.participant_id:
            subject = participants[participants.participant_id == args.id].iloc[0]

        else:
            # the whole folder becomes the id, since an id is provided but not found in participants.tsv
            folder_id = os.path.basename(dicom_path)
            participants.append( {'participan_id':args.id, 'folder_id':folder_id},ignore_index=True)
            dicom_path = opj(dicom_path,'../')
            subject = participants[participants.participant_id == args.id].iloc[0]

    print(subject)
    participants = preproc_ids(participants)

    subfolder = args.subfolder

    commandStrings = []
    commands = []

    used_ids = []
    bids_id_count = get_max_bids_id(participants)

    # dcm2nii conversion
    for f in [name for name in os.listdir(dicom_path) if os.path.isdir(opj(dicom_path,name,subfolder))]:
        bids_id = find_corresponding_bids(f, participants)
        if subject is not None:
            if bids_id in subject.participant_id:
                cmd = ["dcm2bids","-d",opj(dicom_path,f,subfolder),"-p",bids_id.split('-')[1],"-c",config_file_path,"-o",out_path]
                commandStrings.append(' '.join(cmd))
                commands.append(cmd)
        else:
            print("Found BIDS ID",bids_id,"for file",f)
            if bids_id == '-1':
                bids_id = 'sub-'+ str(bids_id_count+1).zfill(5)
                bids_id_count += 1
                print('Could not find entry for subject',f)
                print('Creating new subject',bids_id)

                info = extract_participant_info(opj(dicom_path,f,subfolder))
                info['participant_id'] = bids_id
                info['folder_id'] = f
                participants = participants.append(info,ignore_index=True)
            else:
                participants[participants.participant_id == bids_id].iloc[0].folder_id.append(f)

            cmd = ["dcm2bids","-d",opj(dicom_path,f,subfolder),"-p",bids_id.split('-')[1],"-c",config_file_path,"-o",
                out_path]
            commandStrings.append(' '.join(cmd))
            commands.append(cmd)

    #%% start conversion
    if args.multiproc:
        num_cpus = multiprocessing.cpu_count()
        print("Running in parallel with",num_cpus,"cores.")
        p = multiprocessing.Pool(num_cpus)
        p.map(start_proc, commands)
        print("Finished!")
    else:
        for cmd in commands:
            p = subprocess.Popen(cmd)
            p.wait()

    #save participants.tsv back to output directory
    participants = ids2string(participants)
    participants.to_csv(opj(out_path,'participants.tsv'),sep='\t',index=False)


    # nii2dcm conversion
    if not args.dcm:
        return

    #convert niftis back to dicoms
    
    
# %%
if __name__ == "__main__":
    sys.exit(main())

# %%
