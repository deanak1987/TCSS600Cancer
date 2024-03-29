import glob

filenames = []

for filename in glob.glob("1script/*.xml"):
    filenames.append(filename)

import xml.etree.ElementTree as ET
from lxml import etree as LT

roots = []
trees = []
namespaces = []
for filename in filenames:
    tree = ET.parse(filename)  # Read file
    root = tree.getroot()  # Parse XML
    roots.append(root)
    trees.append(tree)

    root_node = LT.parse(filename).getroot()
    namespace = root_node.nsmap
    namespaces.append(namespace)

len(roots), len(trees), len(namespaces)



def xml_element_valid(xml_element, path):
    return True if xml_element.find(path) is not None else False


def many_xml_attrib(xml_element, path, attributes):
    results = []
    for attr in attributes:
        data = xml_one_element(xml_element, path, attr)
        results.append(data)
    return results


def xml_one_element(xml_element, path, attrib):
    if xml_element_valid(xml_element, path):
        return xml_element.find(path).attrib.get(attrib)
    else:
        return None


def xml_many_elements(xml_element, path):
    return xml_element.findall(path)


def xml_text_value(xml_element, path):
    if xml_element_valid(xml_element, path):
        return xml_element.find(path).text
    else:
        return None


def xml_many_text_elements(xml_element, path):
    list_elements = xml_many_elements(xml_element, path)
    if len(list_elements) > 1:
        text_one = list_elements[0].text
        text_two = list_elements[1].text
    elif len(list_elements) == 1:
        text_one = list_elements[0].text
        text_two = 'NA'
    else:
        text_one = 'NA'
        text_two = 'NA'
    return (text_one, text_two)


tag_lists = []
tag_list = []
# Capturando todas as tags do documento
for tree in trees:
    for elem in tree.iter():
        tag_list.append(elem.tag)
    # tag_list  = list(set(tag_list))
    tag_lists.append(tag_list)

# for tag_list in tag_lists:
#   # print(len(tag_list))

# print(tag_list)

tag_lists[0].index('{http://tcga.nci/bcr/xml/clinical/radiation/2.7}radiations')


tag_list = []
rows = []

for root, namespace in zip(roots, namespaces):
    substitutions = {v: k for k, v in namespace.items()}
    patient_index_namespace = list(namespace.items())[0][0]

    path = '{' + namespace[patient_index_namespace] + '}' + 'patient'
    patient_data = {}
    patients = xml_many_elements(root, path)

    for patient in patients:
        attrib = 'preferred_name'
        for element in patient.iter():
            # print(elem.tag)
            tag = element.tag
            tag_list.append(tag)
            preferred_name = xml_one_element(patient, tag, attrib)
            # print(tag, preferred_name)
            address = tag.split('}')[0].replace('{', '')
            # print('prefixo: ', address)

            if preferred_name == '' or preferred_name == None:
                preferred_name = tag.split('}')[1]
                # print("###", tag, preferred_name)

            value = xml_text_value(patient, tag)

            prefix = substitutions[address]
            # print('prefixo: ', prefix)

            key = prefix + '-' + preferred_name
            # key = preferred_name

            patient_data[key] = value
            # print('chave: ',key, ' ++ valor: ',value)
    rows.append(patient_data)

len(patient_data.keys())

import pandas as pd

df = pd.DataFrame(rows, columns=patient_data.keys())
print(df.head())

# for col in df.columns:
#     print(col)
#     print("Absolute count: ", df[col].value_counts())
#     print("Relative count: ", df[col].value_counts(normalize=True))
#     print('Valores Na: ', df[col].isna().sum())
#     # Count distinct observations over requested axis.
#     # print(len(df)/df[col].nunique())
#     print('\n')

"""Removing columns containing ONLY na values"""

query_cols = [col for col in df.columns if 'status_by_ihc' in col]
print(query_cols)