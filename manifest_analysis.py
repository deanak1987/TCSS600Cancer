import pandas as pd
df_manifest = pd.read_csv('gdc_manifest_20230403_215938.txt', sep="\t")
df_manifest.head()
barcode = []
for row in df_manifest.filename:
    rowsplit = row.split('-', 3)
    print(rowsplit)
    barcode.append("-".join([rowsplit[0], rowsplit[1], rowsplit[2]]))
df_manifest['bcr_patient_barcode'] = barcode
print(df_manifest.head())
output_folder = 'output'
df_clinic = pd.read_csv(output_folder + "/XML_TCGA_01_XmlDataCapture_output.csv")

img_count = []
for row1 in df_manifest['bcr_patient_barcode']:
    cnt = 0
    for row2 in df_clinic['shared-bcr_patient_barcode']:
        if row1 == row2:
            cnt += 1
    img_count.append(cnt)

df_manifest['images'] = img_count
print(df_manifest.head())