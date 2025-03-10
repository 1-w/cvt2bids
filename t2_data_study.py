# %%
from math import e
import os
from posixpath import dirname
import shutil
import pandas as pd
from os.path import join as opj
import glob
import tqdm

# %%
all_data_path = "/mnt/NAS99/Data/all_lab_data/rawdata"

# %%
fcd180_pats = pd.read_csv("/mnt/NAS99/Data/fcd180/participants.tsv", sep="\t")
# %%
lab_pats = pd.read_csv(opj(all_data_path, "participants.tsv"), sep="\t")
# %%
fcd_pats = [
    os.path.basename(f)
    for f in glob.glob(
        opj("/mnt/NAS99/studies/fcd_detection_study/sourcedata/fcd_data", "*")
    )
]
# %%

lab_pats.query("dcm_header_id in @fcd_pats")

# %%
outdir = "/home/lennartw/wdir/data/fcdt2iso/"
os.makedirs(outdir, exist_ok=True)
relevant = lab_pats.query("dcm_header_id in @fcd_pats")
for i, r in tqdm.tqdm(relevant.iterrows(), total=len(relevant)):
    t2isofiles = glob.glob(
        opj(
            all_data_path,
            "%s" % r["participant_id"],
            "*",
            "*",
            "*TSEch32iso08_T2w.nii.gz",
        )
    )

    r180 = fcd180_pats.query(f"lab_id == {str(int(r.dcm_header_id))}")

    if len(t2isofiles) > 0:
        outfolder = opj(outdir, "%s" % r180["participant_id"].values[0])
        os.makedirs(outfolder, exist_ok=True)
        for t2 in t2isofiles:
            session = os.path.basename(os.path.dirname(os.path.dirname(t2)))
            outpath = opj(outfolder, session, "anat")
            os.makedirs(outpath, exist_ok=True)

            for f in glob.glob(opj(os.path.dirname(t2), "*")):
                if "STIRch32hippo" in f:
                    continue
                newfn = os.path.basename(f).replace(
                    r["participant_id"], r180["participant_id"].values[0]
                )
                shutil.copy2(
                    f,
                    opj(outpath, newfn),
                )


# %%

from bids import BIDSLayout
import SimpleITK as sitk

# %%
t2ds = BIDSLayout("/home/lennartw/wdir/data/fcdt2iso", validate=False)
fcd180 = BIDSLayout("/home/lennartw/wdir/data/fcd180", validate=False)
fov = BIDSLayout("/home/lennartw/wdir/data/fcd180/derivatives/fov", validate=False)

# %%
resampler = sitk.ResampleImageFilter()

for s in t2ds.get_subjects():
    fcd180_t1_bf = fcd180.get(suffix="T1w", subject=s, extension=".nii.gz")[0]

    fcd180_mask_bf = fov.get(
        suffix="mask", space="T1wFOV", subject=s, extension=".nii.gz"
    )[0]

    t1_bf = t2ds.get(suffix="T1w", subject=s, extension=".nii.gz")[0]

    fcd180_t1 = sitk.ReadImage(fcd180_t1_bf.path)
    fcd180_mask = sitk.ReadImage(fcd180_mask_bf.path)
    t1 = sitk.ReadImage(t1_bf.path)

    if fcd180_t1.GetSize() != t1.GetSize():
        print(f"Size mismatch for {s}")
        print(fcd180_t1.GetSize(), t1.GetSize())
        continue
    else:
        if np.sum(sitk.GetArrayFromImage(fcd180_t1) - sitk.GetArrayFromImage(t1)):
            print(f"Array mismatch for {s}")
            continue

    resampler.SetReferenceImage(t1)
    resampler.SetInterpolator(sitk.sitkNearestNeighbor)
    resampler.SetDefaultPixelValue(0)
    mask_res = resampler.Execute(fcd180_mask)
    dest = t1_bf.path.replace("T1w.nii.gz", "T1w_mask.nii.gz")
    if dest != t1_bf.path:
        sitk.WriteImage(mask_res, dest)
    else:
        print("Something went wrong with the destination path", s)


# %%
s = "00005"
flair_t2_path = t2ds.get(suffix="FLAIR", subject=s, extension=".nii.gz")[1]

flair180_path = fcd180.get(suffix="FLAIR", subject=s, extension=".nii.gz")[0]

flair_t2 = sitk.ReadImage(flair_t2_path.path)
flair_180 = sitk.ReadImage(flair180_path.path)

# %%
import numpy as np

np.all(sitk.GetArrayFromImage(flair_t2) == sitk.GetArrayFromImage(flair_180))
# %%
