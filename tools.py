import pandas as pd
import numpy as np
from os import path
from datetime import datetime
import streamlit as st 
import json

risen_supervisors = pd.DataFrame([])

RBTs = []
trainees = []
risen_supervisors = []
supervisors = []

def get_providers():
    return pd.read_csv('providers.csv', sep=',')

def get_data():
    df = pd.read_csv('data.csv')
    labels = ['ProviderId', 'DateOfService', 'TimeWorkedFrom', 'TimeWorkedTo', 'TimeWorkedInHours', 'ClientFirstName', 'ProviderFirstName', 'ProcedureCode' ]
    return df.drop(df.columns.difference(labels), 1)

def verify_valid_overlapping(entry, i, providerName, procedureCode, providerId):
    # if entry[providerName] == 'Maggy' and i[providerName] == 'Rahimil':
    procedure = entry[procedureCode]
    if entry[providerId] == i[providerId]:
        return False
    if entry[providerId] in RBTs and i[providerId] in trainees:
        return False
    
    # if (entry[providerId] in RBTs or entry[providerId] in trainees) and i[providerId] in risen_supervisors:
        
    if procedure.lower().replace(' ', '') in ['97155'] and i[procedureCode].lower().replace(' ', '') in ['97155:non-billable']:
        return True
    if procedure.lower().replace(' ', '') in ['97153', '97153:non-billable'] and i[procedureCode].lower().replace(' ', '') in ['97155', '97155:non-billable']:
        return True
    if procedure.lower().replace(' ', '') == 'documentation' and i[procedureCode].lower().replace(' ', '') == 'remoteindividualsupervision':
        return True
    return False

def calculate_overlapping(entry, providerName,providerId,depured_data, procedureCode, client, timeFrom, timeTo, risen_supervisors):
    overlapping = []
    
    entry_start = datetime.strptime(entry[timeFrom], '%m/%d/%Y %H:%M')
    entry_end = datetime.strptime(entry[timeTo], '%m/%d/%Y %H:%M')
    procedure = entry[procedureCode]
    
    for i in depured_data:
        # print(verify_valid_overlapping(entry,i,providerName,procedureCode,providerId, risen_supervisors))
        if  verify_valid_overlapping(entry,i,providerName,procedureCode,providerId):
            start = datetime.strptime(i[timeFrom], '%m/%d/%Y %H:%M')
            end = datetime.strptime(i[timeTo], '%m/%d/%Y %H:%M')
            if not i[client] == entry[client]:
                continue
            
            if (entry_start >= start and entry_start <= end) or (entry_end >= start and entry_end <= end) or (start >= entry_start and end <= entry_end):
                time = min(entry_end,end)-max(entry_start, start)
                overlapping.append((entry,i, time))
    
    if len(overlapping) > 1:
        for i in overlapping:
            if i[1][procedureCode].lower().replace(' ', '') == '97155:non-billable':
                overlapping = [i]
                break
    return overlapping

def process(fix=False):    
    providers_data = get_providers()
    
    supervisors = providers_data[providers_data['Type'] == 'Supervisor']
    risen_supervisors = providers_data[providers_data['Type'] == 'Risen Supervisor']
    trainees = providers_data[providers_data['Status'] == 'Trainee']
    RBTs = providers_data[providers_data['Status'] == 'RBT']

    data = get_data()
    
    valid = ['97153', '97155', '97153: Non-Billable', '97155: Non-Billable', 'Documentation', 'Remote Individual Supervision']
    supervisors_codes = ['97155', '97155:non-billable', 'remoteindividualsupervision']
    valid = [i.replace(' ','').lower() for i in valid]
    
    # eliminar datos no deseados
    filter = [i.replace(' ', '').lower() in valid for i in data.ProcedureCode]
    data['Filter1'] = filter
    data = data[data.Filter1]
    data = data.drop('Filter1', 1)  
    
    errors = []
    notifications = []
    depured_data = []
    non_supervisors = []
    providersErrors = []

    cols = data.columns

    providerId = list(cols).index('ProviderId')
    providerName = list(cols).index('ProviderFirstName')
    procedureCode = list(cols).index('ProcedureCode')
    timeFrom = list(cols).index('TimeWorkedFrom')
    timeTo = list(cols).index('TimeWorkedTo')
    client = list(cols).index('ClientFirstName')
    # print(data[data['ProviderFirstName'] == 'Rahimil'])
    
    # test = np.array(data)
    # #datos de los
    # for i in test:
    #     # print(i)
    #     if i[providerName] == 'Rahimil':
    #         print(i[procedureCode].lower().replace(' ', '') in supervisors_codes)
    #         print(i[procedureCode].lower().replace(' ', '') )
    #         print()
    filter_supervisors =[i.replace(' ', '').lower() in supervisors_codes for i in data.ProcedureCode]
    
    supervisors_data = data[filter_supervisors]
    # print(supervisors_data[supervisors_data['ProviderFirstName'] == 'Rahimil'])

    supervisors_data = np.array(supervisors_data)

    for k in range(len(supervisors_data)):
        i = supervisors_data[k]
        if i[procedureCode].replace(' ', '').lower() == 'remoteindividualsupervision':
            if i[providerId] in list(trainees['ProviderId']):
                notifications.append(i)
                i[procedureCode] = 'Documentation'
                non_supervisors.append(i)
                continue
            elif i[providerId] in list(RBTs['ProviderId']):
                notifications.append(i)
                i[procedureCode] = 'Documentation'
                non_supervisors.append(i)
                continue
                
        if i[procedureCode] == '97155':
            if i[providerId] in list(risen_supervisors['ProviderId']+supervisors['ProviderId']) :
                notifications.append(i)
                i[procedureCode] = '97155:non-billable'
                depured_data.append(i)
                continue
                
            if i[providerId] in list(RBTs['ProviderId']):
                errors.append(i)
                providersErrors.append(i[providerId])
                continue

        if i[procedureCode].replace(' ', '').lower() == '97155:non-billable':
            if i[providerId] in list(trainees['ProviderId']):
                errors.append(i)
                providersErrors.append(i[providerId])
                continue
            elif i[providerId] in list(RBTs['ProviderId']):
                errors.append(i)
                providersErrors.append(i[providerId])
                continue
            
        depured_data.append(i)

    code53 = np.array(data[[i.lower().replace(' ', '') == '97153' for i in data['ProcedureCode']]])
    code_doc = np.array(data[[i.lower().replace(' ', '') == 'documentation' for i in data['ProcedureCode']]])
    code55 = np.array(data[[i.lower().replace(' ', '') == '97155' for i in data['ProcedureCode']]])
    
    for i in code_doc:
        if i[procedureCode].replace(' ', '').lower() == 'documentation':

            if i[providerId] in list(supervisors['ProviderId']):
                notifications.append(i)
                i[procedureCode] = 'Remote Individual Supervision'
                depured_data.append(i)
                continue
            
            elif i[providerId] in list(risen_supervisors['ProviderId']):
                notifications.append(i)
                i[procedureCode] = 'Remote Individual Supervision'
                depured_data.append(i)
                continue
            
        non_supervisors.append(i)
    
    for i in code55:
        if i[procedureCode].replace(' ', '').lower() == '97155':
            if i[providerId] in list(risen_supervisors['ProviderId']):
                # errors.append(i)
                # providersErrors.append(i[providerId])
                i[procedureCode] = '97155:non-billable'
                continue
            non_supervisors.append(i)

    for i in code53:
    
        if i[providerId] in list(supervisors['ProviderId']):
            errors.append(i)
            providersErrors.append(i[providerId])
            continue
        
        elif i[providerId] in list(risen_supervisors['ProviderId']):
            errors.append(i)
            providersErrors.append(i[providerId])
            continue
            
        non_supervisors.append(i)
        
    if len(non_supervisors) > 0:
        doc_depured = np.stack(non_supervisors, axis=0)
    if len(depured_data) > 0:    
        depured_data = np.stack(depured_data, axis=0)
    if len(errors) > 0:
        errors = np.stack(errors, axis=0)

    overlappings = {}
    providers_data_with_errors = {}
    
    for i in non_supervisors:
    
        new_ol = calculate_overlapping(i, providerName=providerName, providerId=providerId, depured_data=depured_data, procedureCode=procedureCode, 
                                       client=client, timeFrom=timeFrom, timeTo=timeTo, risen_supervisors=risen_supervisors)
        
        # print(new_ol)
        if i[providerId] in providersErrors:
            
            if not i[providerId] in providers_data_with_errors:
                providers_data_with_errors[i[providerId]] = []

            providers_data_with_errors[i[providerId]].append(new_ol) 
        
        else:
            if not i[providerId] in overlappings:
                overlappings[i[providerId]] = []
                # overlappings[i[providerId]]

            if len(new_ol) != 0:
                overlappings[i[providerId]].append(new_ol) 

    
    notifications = pd.DataFrame(np.stack(notifications, axis=0), columns=cols)
    
    if len(errors) > 0:
        
        # # with open('overlapping_missing_errors.json', 'w') as f:
        # #     f.write(json.dumps(for i in providers_data_with_errors))
        
        # for i in providers_data_with_errors:
            
        pd.DataFrame(supervisors_data).to_csv('supervisors_data.csv')
    if len(notifications) > 0:
        with open('auto_fixed_errors.json', 'w') as f:
            notifications.to_csv('auto_fixed.csv')


    lab = list(cols)
    lab.append('MeetingDuration')
    # print(overlappings)
    for i in overlappings:
        ol = []
        for j in overlappings[i]:
            d,i_ol,time = j[0]
            i_ol = np.append(i_ol,time.seconds/3600)
            ol.append(i_ol)
        if len(ol) > 0:
            ol = pd.DataFrame(np.stack(ol, axis=0), columns=lab)
            ol.to_csv(path.join('done',str(i)+'.csv'))
        
    if len(errors) > 0:
        return 'errors'
    if len(notifications):
        return 'notifications'
    return 'ok'