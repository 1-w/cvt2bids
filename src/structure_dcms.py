# %%
import os
import pydicom  # pydicom is using the gdcm package for decompression
import tqdm
import multiprocessing
from os.path import join as opj
from tqdm.contrib.concurrent import process_map  # or thread_map
import pickle


# %%
def clean_text(string):
    # clean and standardize text descriptions, which makes searching files easier
    forbidden_symbols = ["*", ".", ",", '"', "\\", "/", "|", "[", "]", ":", ";", " "]
    for symbol in forbidden_symbols:
        string = string.replace(symbol, "_")  # replace everything with an underscore
    return string.lower()


# %%
# user specified parameters
src = "/media/NAS99/Data/dicoms/Horos Data/DATABASE.noindex"
dst = "/media/NAS99/Data/all_lab_data/sourcedata"

print("reading file list...")
unsortedList = []
for root, dirs, files in os.walk(src):
    for file in tqdm.tqdm(files):
        _, ext = os.path.splitext(file)
        if ext == ".dcm" or ext == "":  # exclude non-dicoms, good for messy folders
            unsortedList.append(os.path.join(root, file))

print("%s files found." % len(unsortedList))
# %%

with open("all_dicoms.pkl", "wb") as fp:  # Pickling
    pickle.dump(unsortedList, fp)
# def create_folders(dicom_loc):
#     # for dicom_loc in tqdm.tqdm(unsortedList):
#     # read the file
#     ds = pydicom.read_file(dicom_loc, force=True)

#     # get patient, study, and series information
#     patientID = clean_text(ds.get("PatientID", "NA"))
#     studyDate = clean_text(ds.get("StudyDate", "NA"))
#     studyDescription = clean_text(ds.get("StudyDescription", "NA"))
#     seriesDescription = clean_text(ds.get("SeriesDescription", "NA"))

#     # generate new, standardized file name
#     modality = ds.get("Modality", "NA")
#     studyInstanceUID = ds.get("StudyInstanceUID", "NA")
#     seriesInstanceUID = ds.get("SeriesInstanceUID", "NA")
#     instanceNumber = str(ds.get("InstanceNumber", "0"))
#     fileName = modality + "." + seriesInstanceUID + "." + instanceNumber + ".dcm"

#     return opj(dst, patientID, studyDate, studyDescription, seriesDescription, fileName)


# %%
# fileNames = process_map(create_folders, unsortedList, max_workers=2, chunksize=100)

# with multiprocessing.Pool(processes=22) as pool:
#     fileNames = pool.map(create_folders, unsortedList)

# %%
# for f in fileNames:
#     # save files to a 4-tier nested folder structure
#     foldername = os.path.dirname(f)
#     os.makedirs(foldername, exist_ok=True)

# %%
for dicom_loc in tqdm.tqdm(unsortedList):
    # read the file
    ds = pydicom.read_file(dicom_loc, force=True)

    # get patient, study, and series information
    patientID = clean_text(ds.get("PatientID", "NA"))
    studyDate = clean_text(ds.get("StudyDate", "NA"))
    studyDescription = clean_text(ds.get("StudyDescription", "NA"))
    seriesDescription = clean_text(ds.get("SeriesDescription", "NA"))

    # generate new, standardized file name
    modality = ds.get("Modality", "NA")
    studyInstanceUID = ds.get("StudyInstanceUID", "NA")
    seriesInstanceUID = ds.get("SeriesInstanceUID", "NA")
    instanceNumber = str(ds.get("InstanceNumber", "0"))
    fileName = modality + "." + seriesInstanceUID + "." + instanceNumber + ".dcm"

    # uncompress files (using the gdcm package)
    try:
        ds.decompress()
    except:
        print(
            'an instance in file %s - %s - %s - %s" could not be decompressed. exiting.'
            % (patientID, studyDate, studyDescription, seriesDescription)
        )

    dst_name = os.path.join(
        dst, patientID, studyDate, studyDescription, seriesDescription, fileName
    )

    foldername = os.path.dirname(dst_name)
    os.makedirs(foldername, exist_ok=True)

    # save files to a 4-tier nested folder structure
    ds.save_as(dst_name)

print("done.")

# %%
