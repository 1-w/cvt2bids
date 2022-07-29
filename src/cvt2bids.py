#%%
import os
import sys
import pandas as pd
import subprocess
import numpy as np
import multiprocessing
from os.path import join as opj
import argparse
import pydicom as pydi
import glob
from pkg_resources import require
import json

#%%
def find_corresponding_bids(id_, df):
    id_names = [
        x for x in df.columns if x in ["osepa_id", "lab_id", "neurorad_id", "folder_id"]
    ]

    for _, r in df.iterrows():
        for m in [r[id_name] for id_name in id_names]:
            if str(id_).strip() in m:
                return r.participant_id

    for _, r in df.iterrows():
        if str(id_).strip() == str(r.participant_id):
            return r.participant_id

    # print(id)
    return str(-1)


def start_proc(cmd):
    print("Running:", cmd)
    proc = subprocess.Popen(cmd)
    proc.wait()


def conv2idArray(s):
    try:
        idAr = eval(s)
        if type(idAr) != list:
            idAr = [str(idAr)]
        return idAr
    except:
        return [t.strip() for t in str(s).split(",")] if s is not np.nan else []


def preproc_ids(df):
    if "osepa_id" in df.columns:
        df.osepa_id = df.osepa_id.apply(lambda x: conv2idArray(x))
    if "lab_id" in df.columns:
        df.lab_id = df.lab_id.apply(lambda x: conv2idArray(x))
    if "neurorad_id" in df.columns:
        df.neurorad_id = df.neurorad_id.apply(lambda x: conv2idArray(x))
    if "folder_id" in df.columns:
        df.folder_id = df.folder_id.apply(lambda x: conv2idArray(x))
    return df


def ids2string(df):
    if "osepa_id" in df.columns:
        df.osepa_id = df.osepa_id.apply(lambda x: ",".join(x))
    if "lab_id" in df.columns:
        df.lab_id = df.lab_id.apply(lambda x: ",".join(x))
    if "neurorad_id" in df.columns:
        df.neurorad_id = df.neurorad_id.apply(lambda x: ",".join(x))
    if "folder_id" in df.columns:
        df.folder_id = df.folder_id.apply(lambda x: ",".join(x))
    return df


def convert2abs(path):
    if os.path.isabs(path):
        return path
    else:
        return os.path.normpath(opj(os.getcwd(), path))


def get_max_bids_id(df):
    ids = df.participant_id.apply(lambda x: int(x.split("-")[1][-5:]))
    if len(ids) == 0:
        return 0

    max_id = np.max(np.array(ids))
    if max_id >= 1:
        return max_id
    else:
        return 0


def extract_participant_info(dcm_path):
    # return dict with participant info from dcm header
    infotags = {
        "institution_name": ("0x0008", "0x0080"),
        #'acquisition_date':("0x0008","0x0022") ,
        "name": ("0x0010", "0x0010"),
        "id": ("0x0010", "0x0020"),
        "dob": ("0x0010", "0x0030"),
        "sex": ("0x0010", "0x0040"),
        #'other_ids':("0x0010","0x1000"),
        #'other_names':("0x0010","0x1001"),
        #'birth_name':("0x0010","0x1005"),
        #'age':("0x0010","0x1010"),
        "size": ("0x0010", "0x1020"),
        "weight": ("0x0010", "0x1030"),
    }
    subject_info = {}

    for key in infotags:
        subject_info[key] = []
    for f in os.listdir(dcm_path):
        print(opj(dcm_path, f))
        try:
            dcm_file = [
                x for x in glob.glob(opj(dcm_path, f) + "/*") if os.path.isfile(x)
            ][0]
        except:
            print("No dcm files in folder")

        if dcm_file:
            dcm = pydi.dcmread(dcm_file)
            for key in infotags:
                tg = pydi.tag.Tag(infotags[key])
                if tg in dcm:
                    if str(dcm[tg].value) not in subject_info[key]:
                        subject_info[key].append(str(dcm[tg].value))

    returnDict = {}
    for key in subject_info:
        print(key, subject_info[key])
        returnDict[key] = ",".join(subject_info[key])

    return returnDict


#%% prepare conversion
def main():
    """Load arguments for main"""
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=""" Convert DICOMS to NIFTIS and back, with possible defacing and header annonymization {}""".format(
            require("dcm2bids")[0].version  # TODO
        ),
        epilog=""" Documentation not yet at https://github.com/1-w/cvt2bids """,
    )

    parser.add_argument(
        "--version",
        action="version",
        help="Display verison.",
        version=require("cvt2bids")[0].version,
    )

    parser.add_argument(
        "-d",
        "--dicom_path",
        required=True,
        help="BIDS conform dir containing all relevant niftis. participants.tsv needs to allow a mapping between the files in sourcedata and the participant_ids.",
    )

    parser.add_argument(
        "-o",
        "--out_path",
        required=True,
        help="provide output directory path. If it does not include a participants.tsv file, a new one will be generated from dicom data",
    )

    parser.add_argument(
        "-c",
        "--config_path",
        required=True,
        help="provide the path to a valid config file.",
    )

    parser.add_argument(
        "-i",
        "--id",
        required=False,
        help="Single participant_id. Only this id will be processed from participants.tsv file. If no participants.tsv file is provided, all found DICOMS will be stored under this id",
    )  # TODO

    parser.add_argument(
        "-p",
        "--participants_file",
        required=False,
        help="if participants.tsv file included somewhere other than out_path",
    )

    parser.add_argument(
        "-s",
        "--subfolder",
        default="",
        required=False,
        help="if only a specific subfolder in a subjects directory should be searched for DICOMS",
    )

    parser.add_argument(
        "-pat",
        "--pathology",
        default="",
        required=False,
        help="specify pathology for pat ID",
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

    if len(sys.argv) == 1:
        parser.print_help()
        return 0

    try:
        args = parser.parse_args()
    except argparse.ArgumentError:
        parser.print_usage()
        exit(-1)

    # args =parser.parse_args(args, namespace = v)

    welcome_str = "cvt2bids " + require("cvt2bids")[0].version
    welcome_decor = "-" * len(welcome_str)
    print(welcome_decor + "\n" + welcome_str + "\n" + welcome_decor)

    dicom_path = convert2abs(args.dicom_path)
    out_path = convert2abs(args.out_path)

    patho = args.pathology
    os.makedirs(out_path, exist_ok=True)

    config_file_path = convert2abs(args.config_path)

    if args.participants_file:
        participants_file = convert2abs(args.participants_file)
        participants = pd.read_csv(participants_file, sep="\t", dtype=object)
    else:
        if os.path.isfile(opj(out_path, "participants.tsv")):
            participants_file = opj(out_path, "participants.tsv")
            participants = pd.read_csv(participants_file, sep="\t", dtype=object)

        else:
            # generate participants.tsv
            participants_file = opj(out_path, "participants.tsv")
            participants = pd.DataFrame(
                columns=["participant_id", "folder_id"], dtype=object
            )

    if "folder_id" not in participants.columns:
        participants["folder_id"] = ""

    subject = None
    if args.id:
        if args.id in participants.participant_id.values:
            subject = participants[participants.participant_id == args.id].iloc[0]

        else:
            print("Did not find participant_id", args.id)
            # the whole folder becomes the id, since an id is provided but not found in participants.tsv
            folder_id = os.path.basename(dicom_path)
            participants.append(
                {"participan_id": args.id, "folder_id": folder_id}, ignore_index=True
            )
            dicom_path = opj(dicom_path, "../")
            subject = participants[participants.participant_id == args.id].iloc[0]

    participants = preproc_ids(participants)

    names = os.listdir(dicom_path)

    commandStrings = []
    commands = []

    used_ids = []
    bids_id_count = get_max_bids_id(participants)

    # dcm2nii conversion
    for name in names:
        if args.subfolder == "":
            subfolders = os.listdir(opj(dicom_path, name))
        else:
            subfolders = [args.subfolder]

        # find all subfolders containing dicoms:

        if os.path.isdir(opj(dicom_path, name)):
            fname = opj(dicom_path, name)
        else:
            continue
        bids_id = find_corresponding_bids(name, participants)
        if subject is not None:
            if bids_id in subject.participant_id:
                cmd = [
                    "dcm2bids",
                    "-d",
                    fname,
                    "-p",
                    bids_id.split("-")[1],
                    "-c",
                    config_file_path,
                    "-o",
                    out_path,
                ]
                commandStrings.append(" ".join(cmd))
                commands.append(cmd)
        else:
            if bids_id == "-1":
                bids_id = "sub-" + patho + str(bids_id_count + 1).zfill(5)
                bids_id_count += 1
                print("Could not find entry for subject", str(fname))
                print("Creating new subject", bids_id)

                # info = extract_participant_info(fname)
                info = {}
                info["participant_id"] = bids_id
                info["folder_id"] = [name]
                info["osepa_id"] = []
                info["lab_id"] = []
                info["neurorad_id"] = []
                participants = participants.append(info, ignore_index=True)
            else:
                print("Found BIDS ID", bids_id, "for file", fname)
                if (
                    name
                    not in participants[participants.participant_id == bids_id]
                    .iloc[0]
                    .folder_id
                ):
                    participants[participants.participant_id == bids_id].iloc[
                        0
                    ].folder_id.append(name)

            cmd = [
                "dcm2bids",
                "-d",
                fname,
                "-p",
                bids_id.split("-")[1],
                "-c",
                config_file_path,
                "-o",
                out_path,
            ]
            commandStrings.append(" ".join(cmd))
            commands.append(cmd)

    #%% start conversion
    if args.multiproc:
        num_cpus = multiprocessing.cpu_count()
        print("Running in parallel with", num_cpus, "cores.")
        p = multiprocessing.Pool(min(len(commands), num_cpus))
        p.map(start_proc, commands)
    else:
        for cmd in commands:
            start_proc(cmd)
    print("Finished!")

    # save participants.tsv back to output directory
    participants = ids2string(participants)

    fields = [
        "PatientName",
        "PatientID",
        "PatientBirthDate",
        "PatientSex",
        "AcquisitionDateTime",
        "DeviceSerialNumber",
    ]
    # populate with additional info

    additional_infos = []

    for pat in participants.participant_id:
        info = {}
        json_sidecars = glob.glob(opj(out_path, f"{pat}/anat/*.json"))
        for field in fields:
            info[field] = []
        for js in json_sidecars:
            print("found sidecar", js)
            with open(js) as jf:
                data = json.load(jf)
            for field in fields:
                tmpvar = data[field]
                if field == "AcquisitionDateTime":
                    tmpvar = tmpvar.split("T")[0]
                if tmpvar not in info[field]:
                    info[field].append(tmpvar)

        for field in fields:
            info[field] = ";".join(info[field])

        additional_infos.append({k: t for k, t in info.items()})

    df = pd.DataFrame.from_dict(additional_infos)

    for field in fields:
        participants[field] = df[field]

    participants.to_csv(opj(out_path, "participants.tsv"), sep="\t", index=False)

    # nii2dcm conversion
    if not args.dcm:
        return


# %%
if __name__ == "__main__":
    sys.exit(main())
# %%
