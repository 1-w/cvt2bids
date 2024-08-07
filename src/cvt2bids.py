# %%
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
import re

import dcm2bids


# %%
def find_corresponding_bids(id_, df):
    id_names = [
        x
        for x in df.columns
        if x in ["osepa_id", "lab_id", "neurorad_id", "dcm_header_id"]
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


def start_proc(cmd_list):
    for cdm in cmd_list:
        print("Running:", cdm)
        proc = subprocess.Popen(cdm)
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
    if "dcm_header_id" in df.columns:
        df.dcm_header_id = df.dcm_header_id.apply(lambda x: conv2idArray(x))
    return df


def ids2string(df):
    if "osepa_id" in df.columns:
        df.osepa_id = df.osepa_id.apply(lambda x: ",".join(x))
    if "lab_id" in df.columns:
        df.lab_id = df.lab_id.apply(lambda x: ",".join(x))
    if "neurorad_id" in df.columns:
        df.neurorad_id = df.neurorad_id.apply(lambda x: ",".join(x))
    if "dcm_header_id" in df.columns:
        df.dcm_header_id = df.dcm_header_id.apply(lambda x: ",".join(x))
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
    if not os.path.isfile(dcm_path):
        raise ValueError
    # return dict with participant info from dcm header
    infotags = {
        "institution_name": ("0x0008", "0x0080"),
        "acquisition_date": ("0x0008", "0x0022"),
        "content_date": ("0x0008", "0x0023"),
        "name": ("0x0010", "0x0010"),
        "id": ("0x0010", "0x0020"),
        "dob": ("0x0010", "0x0030"),
        "sex": ("0x0010", "0x0040"),
        #'other_ids':("0x0010","0x1000"),
        #'other_names':("0x0010","0x1001"),
        #'birth_name':("0x0010","0x1005"),
        # 'age':("0x0010","0x1010"),
        "size": ("0x0010", "0x1020"),
        "weight": ("0x0010", "0x1030"),
    }
    subject_info = {}

    for key in infotags:
        subject_info[key] = []
    # for f in os.listdir(dcm_path):

    dcm = pydi.dcmread(dcm_path)
    for key in infotags:
        tg = pydi.tag.Tag(infotags[key])
        if tg in dcm:
            if (
                str(dcm[tg].value) not in subject_info[key]
                and str(dcm[tg].value) != ""
                and str(dcm[tg].value) is not None
            ):
                subject_info[key].append(str(dcm[tg].value))

    returnDict = {}
    for key in subject_info:
        print(key, subject_info[key])
        returnDict[key] = ",".join(subject_info[key])

    return returnDict


# %% prepare conversion
def main(
    dicom_path,
    out_path,
    config_path,
    id_=None,
    participants_file=None,
    pathology="",
    multiproc=False,
):
    welcome_str = "cvt2bids " + require("cvt2bids")[0].version
    welcome_decor = "-" * len(welcome_str)
    print(welcome_decor + "\n" + welcome_str + "\n" + welcome_decor)

    dicom_path = convert2abs(dicom_path)
    out_path = convert2abs(out_path)

    patho = pathology
    os.makedirs(out_path, exist_ok=True)

    config_file_path = convert2abs(config_path)

    if participants_file:
        participants_file = convert2abs(participants_file)
        participants = pd.read_csv(participants_file, sep="\t", dtype=object)
    else:
        if os.path.isfile(opj(out_path, "participants.tsv")):
            participants_file = opj(out_path, "participants.tsv")
            participants = pd.read_csv(participants_file, sep="\t", dtype=object)

        else:
            # generate participants.tsv
            participants_file = opj(out_path, "participants.tsv")
            participants = pd.DataFrame(
                columns=["participant_id", "dcm_header_id", "folder_path"], dtype=object
            )

    if "dcm_header_id" not in participants.columns:
        participants["dcm_header_id"] = []

    subject = None
    if id_:
        if id_ in participants.participant_id.values:
            subject = participants[participants.participant_id == id_].iloc[0]

        else:
            print("Did not find participant_id", id_)
            # the whole folder becomes the id, since an id is provided but not found in participants.tsv
            # folder_id = os.path.basename(dicom_path)
            participants.append(
                {
                    "participan_id": id_,
                    "dcm_header_id": [],
                    "folder_path": dicom_path,
                },
                ignore_index=True,
            )
            # dicom_path = opj(dicom_path, "../")
            subject = participants[participants.participant_id == id].iloc[0]

    participants = preproc_ids(participants)

    commandStrings = []
    commands = []
    commands_dict = {}

    used_ids = []
    bids_id_count = get_max_bids_id(participants)

    # dcm2nii conversion
    for directory, subdirlist, filelist in os.walk(dicom_path):
        print(directory)

        # find all subfolders containing dicoms:
        conv = False
        ind = 0
        print(f"{directory}: Trying to find dcm files...")
        for i, f in enumerate(filelist):
            _, ext = os.path.splitext(f)
            if ext == ".dcm" or ext == "":
                try:
                    pydi.dcmread(os.path.join(directory, f))
                    conv = True
                    ind = i
                    print(f"{directory}: Found dcm files!")
                    break
                except:
                    # could not read file as dcm, so continue
                    continue

        if conv:
            try:
                dcm_info = extract_participant_info(
                    os.path.join(directory, filelist[ind])
                )
            except:
                print(os.path.join(directory, filelist[ind]))
                continue
        else:
            print(f"{directory}: Did not find dcm files...")
            continue

        # here only if conv == True -> dcm_info is defined

        print(f"{directory}: Searching for bids ID for", dcm_info["id"])

        # greifswald addon
        if dcm_info["id"] == "":
            print(f"{directory}: Could not find ID for", dcm_info["id"])
            continue

        id_ = dcm_info["id"]  # .split("_")[0]

        bids_id = find_corresponding_bids(id_, participants)
        session = "tmp"
        if "acquisition_date" in dcm_info and dcm_info["acquisition_date"] != "":
            session = re.sub(r"[^0-9]", "", dcm_info["acquisition_date"])
        elif "content_date" in dcm_info and dcm_info["content_date"] != "":
            session = re.sub(r"[^0-9]", "", dcm_info["content_date"])
        else:
            print(f"{directory}: Could not find session for", id_)
            session = "1"
        print(f"{directory}: Found session", session, "for", id_)
        if subject is not None:
            if bids_id in subject.participant_id:
                if bids_id not in commands_dict.keys():
                    commands_dict[bids_id] = []

                cmd = [
                    "dcm2bids",
                    "-d",
                    directory,
                    "-p",
                    bids_id.split("-")[1],
                    "-c",
                    config_file_path,
                    "-o",
                    out_path,
                    "--forceDcm2niix",
                    "-s",
                    session,
                ]
                commandStrings.append(" ".join(cmd))
                commands.append(cmd)
                commands_dict[bids_id].append(cmd)
        else:
            if bids_id == "-1":
                bids_id = "sub-" + patho + str(bids_id_count + 1).zfill(5)
                bids_id_count += 1
                print(f"{directory}: Could not find entry for", id_)
                print(f"{directory}: Creating new subject with BIDS id", bids_id)

                # info = extract_participant_info(fname)
                info = {}
                info["participant_id"] = bids_id
                info["osepa_id"] = []
                info["lab_id"] = []
                info["neurorad_id"] = []
                info["dcm_header_id"] = [id_]
                # info["folder_path"] = [opj(directory.split()))]
                participants = participants._append(info, ignore_index=True)
            else:
                print(f"{directory}: Found entry for", id_, bids_id)
                if (
                    id_
                    not in participants[participants.participant_id == bids_id]
                    .iloc[0]
                    .dcm_header_id
                ):
                    participants[participants.participant_id == bids_id].iloc[
                        0
                    ].dcm_header_id.append(id_)

            if bids_id not in commands_dict.keys():
                commands_dict[bids_id] = []

            cmd = [
                "dcm2bids",
                "-d",
                directory,
                "-p",
                bids_id.split("-")[1],
                "-c",
                config_file_path,
                "-o",
                out_path,
                "--forceDcm2niix",
                "-s",
                session,
            ]
            commandStrings.append([" ".join(cmd)])
            commands.append([cmd])
            commands_dict[bids_id].append(cmd)

    # save participants.tsv back to output directory
    print("Temporary saving participants.tsv to BIDS format... ")

    participants = ids2string(participants)
    participants.to_csv(opj(out_path, "participants.tsv"), sep="\t", index=False)

    # %% start conversion
    print("Starting conversion to BIDS format... ")
    if multiproc:
        num_cpus = multiprocessing.cpu_count()
        print("Running in parallel with", num_cpus, "cores.")
        p = multiprocessing.Pool(min(len(commands_dict), num_cpus))
        print(list(commands_dict.values())[0])
        p.map(start_proc, commands_dict.values())
    else:
        for cmd in commands:
            start_proc(cmd)
    #
    print("Final saving participants.tsv to BIDS format... ")

    fields = [
        "PatientName",
        "PatientID",
        "PatientBirthDate",
        "PatientAge",
        "PatientSex",
        "AcquisitionDateTime",
        "DeviceSerialNumber",
    ]
    # populate with additional info

    additional_infos = []

    for pat in participants.participant_id:
        info = {}
        # find all json sidecars in out_path
        json_sidecars = glob.glob(opj(out_path, pat, "*", "*", "*.json"))
        for field in fields:
            info[field] = []
        for js in json_sidecars:
            print("found sidecar", js)
            with open(js) as jf:
                data = json.load(jf)
            for field in fields:
                try:
                    tmpvar = data[field]
                    if field == "AcquisitionDateTime":
                        tmpvar = tmpvar.split("T")[0]
                    if tmpvar not in info[field]:
                        info[field].append(tmpvar)
                except:
                    continue

        for field in fields:
            info[field] = ";".join(info[field])

        additional_infos.append({k: t for k, t in info.items()})

    df = pd.DataFrame.from_dict(additional_infos)

    for field in fields:
        participants[field] = df[field]

    participants.to_csv(opj(out_path, "participants.tsv"), sep="\t", index=False)

    print("Finished!")


# %%


def main_wrapper():
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
        "-pat",
        "--pathology",
        default="",
        required=False,
        help="specify pathology for pat ID",
    )

    # unfortunately not supported currently by dcm2bids/dcm2niix .. but we can at least parallelise subjects
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
        return -1

    # args =parser.parse_args(args, namespace = v)
    return main(
        args.dicom_path,
        args.out_path,
        args.config_path,
        args.id,
        args.participants_file,
        args.pathology,
        args.multiproc,
    )


# %%
if __name__ == "__main__":
    sys.exit(main_wrapper())
