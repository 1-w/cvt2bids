# %%

# %%
text_file = open("/home/lennartw/probs", "r")
lines = text_file.read().split('\n')
text_file.close()

lines = [l.strip() for l in lines]
#%%
dirs = [os.path.basename(f) for f in glob.glob('/media/NAS99/Data/fcd_eval_study/dataset/sourcedata/*')]
for f in lines:
    if f not in dirs:
        print(f)
    
#%%
# copy over controlls
import shutil
old_path = '/media/NAS99/Data/fcd_eval_study/dataset/sourcedata_old'
new_path = '/media/NAS99/Data/fcd_eval_study/dataset/sourcedata'
count = 0
for f in glob.glob(old_path+'/*'):
    if os.path.basename(f) in lines:
        count+=1
        if not os.path.isdir(opj(f, 'raw_data')):
            shutil.copytree(f,opj(new_path,os.path.basename(f)))
print(count)
# %%
def copy_folders_with_dicoms(paths, destPath):
    for f in paths:
        print('looking for dicoms in',f)
        if not os.path.isdir(f):
            continue
        if len(glob.glob(f+'/*.dcm')) > 0:
            print('Found DICOMS, copying folder...')
            os.makedirs(opj(destPath),exist_ok=True)
            shutil.copytree(f, opj(destPath, os.path.basename(f)))
        elif len(glob.glob(f+'/*.IMA')) > 0:
            print('Found IMAs, copying folder...')
            os.makedirs(opj(destPath),exist_ok=True)
            shutil.copytree(f, opj(destPath, os.path.basename(f)))
        else:
            copy_folders_with_dicoms(glob.glob(f+'/*'), destPath)
#%%
# clean sourcedata
sourcePath = '/media/NAS99/Data/fcd_eval_study/dataset/sourcedata'

for f in glob.glob(sourcePath+'/*'):
    print('looking at file',f)
    if os.path.isdir(opj(f, 'raw_data')):
        continue
    else:
        copy_folders_with_dicoms(glob.glob(f+'/*'), opj(f, 'raw_data'))

# %%
# %%
