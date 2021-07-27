import pandas as pd
import numpy as np
from os import path
from datetime import datetime
import streamlit as st 

risen_supervisors = pd.DataFrame([])

def get_providers():
    return pd.read_csv('providers.csv', sep=',')

def get_data():
    df = pd.read_csv('data.csv')
    labels = ['ProviderId', 'DateOfService', 'TimeWorkedFrom', 'TimeWorkedTo', 'TimeWorkedInHours', 'ClientFirstName', 'ProviderFirstName', 'ProcedureCode' ]
    return df.drop(df.columns.difference(labels), 1)

def verify_valid_overlapping(entry, i, providerName, procedureCode, providerId ,risen_supervisors):
    
    procedure = entry[procedureCode]
    # print(risen_supervisors)
    # if entry[providerId] == i[providerId]:
    #     return False
    if entry[providerName] == 'Maggy' :
    #     print( procedure.lower().replace(' ', ''))
    #     print(i[procedureCode].lower().replace(' ', ''))
    #     print(procedure.lower().replace(' ', '') in ['97155'] and i[procedureCode].lower().replace(' ', '') in ['remoteindividualsupervision', '97155:non-billable'])
    #     print()
        if procedure.lower().replace(' ', '') in ['97155'] and i[procedureCode].lower().replace(' ', '') in ['remoteindividualsupervision', '97155:non-billable']:
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
        if entry[providerName] == 'Maggy' :
            start = datetime.strptime(i[timeFrom], '%m/%d/%Y %H:%M')
            end = datetime.strptime(i[timeTo], '%m/%d/%Y %H:%M')
            if not i[client] == entry[client]:
                continue
            else:
#                 print(i,entry)
                pass
            if (entry_start >= start and entry_start <= end) or (entry_end >= start and entry_end <= end) or (start >= entry_start and end <= entry_end):
                time = min(entry_end,end)-max(entry_start, start)
                print(entry[providerName])
                print(i[providerName])
                # print(entry,i)
                print(verify_valid_overlapping(entry,i,providerName,procedureCode,providerId, risen_supervisors))
                print()
        if  verify_valid_overlapping(entry,i,providerName,procedureCode,providerId, risen_supervisors):
            # print('here')
            start = datetime.strptime(i[timeFrom], '%m/%d/%Y %H:%M')
            end = datetime.strptime(i[timeTo], '%m/%d/%Y %H:%M')
            if not i[client] == entry[client]:
                continue
            else:
#                 print(i,entry)
                pass
            if (entry_start >= start and entry_start <= end) or (entry_end >= start and entry_end <= end) or (start >= entry_start and end <= entry_end):
                time = min(entry_end,end)-max(entry_start, start)
                overlapping.append((entry,i, time))
    return overlapping

def process(fix=False):    
    providers_data = get_providers()
    
    supervisors = providers_data[providers_data['Type'] == 'Supervisor']
    risen_supervisors = providers_data[providers_data['Type'] == 'Risen Supervisor']
    trainees = providers_data[providers_data['Status'] == 'Trainee']
    RBTs = providers_data[providers_data['Status'] == 'RBT']
    
    # print(risen_supervisors)
    
    data = get_data()
    
    labels = ['ProviderId', 'DateOfService', 'TimeWorkedFrom', 'TimeWorkedTo', 'TimeWorkedInHours', 'ClientFirstName', 'ProviderFirstName', 'ProcedureCode' ]
    valid = ['97153', '97155', '97153: Non-Billable', '97155: Non-Billable', 'Documentation', 'Remote Individual Supervision']
    valid = [i.replace(' ','').lower() for i in valid]
    
    filter = [i.replace(' ', '').lower() in valid for i in data.ProcedureCode]
    data['Filter1'] = filter
    data = data[data.Filter1]
    data = data.drop('Filter1', 1)  
    
    providers = data['ProviderId']
    providers = set(providers)
    
    supervisors_codes = ['97155', '97155:non-billeable', 'remoteindividualsupervision']
    filter_supervisors =[i.replace(' ', '').lower() in supervisors_codes for i in data.ProcedureCode]
    supervisors_data = data[filter_supervisors]
    
    errors = []
    notifications = []
    depured_data = []
    doc_depured = []
    rbt53_depured = []
    rbt55_depured = []
    providersErrors = []

    cols = supervisors_data.columns

    providerId = list(cols).index('ProviderId')
    providerName = list(cols).index('ProviderFirstName')
    procedureCode = list(cols).index('ProcedureCode')
    timeFrom = list(cols).index('TimeWorkedFrom')
    timeTo = list(cols).index('TimeWorkedTo')
    client = list(cols).index('ClientFirstName')

    supervisors_data = np.array(supervisors_data)

    for k in range(len(supervisors_data)):
        i = supervisors_data[k]
        if i[procedureCode].replace(' ', '').lower() == 'remoteindividualsupervision':
            if i[providerId] in list(trainees['ProviderId']):
                notifications.append(i)
                i[procedureCode] = 'Documentation'
                doc_depured.append(i)
                continue
            elif i[providerId] in list(RBTs['ProviderId']):
                notifications.append(i)
                i[procedureCode] = 'Documentation'
                rbt53_depured.append(i)
                continue
                
        if i[procedureCode] == '97155':
            if i[providerId] in list(risen_supervisors['ProviderId']):
                notifications.append(i)
                i[procedureCode] = '97155:non-billeable'
                depured_data.append(i)
                continue
                
            if i[providerId] in list(RBTs['ProviderId']):
                errors.append(i)
                providersErrors.append(i[providerId])
                continue
        if i[procedureCode].replace(' ', '').lower() == '97155:non-billeable':
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
                i[providerId] = 'Remote Individual Supervision'
                depured_data.append(i)
                continue
            
            elif i[providerId] in list(risen_supervisors['ProviderId']):
                notifications.append(i)
                i[procedureCode] = 'Remote Individual Supervision'
                depured_data.append(i)
                continue
            
        doc_depured.append(i)
    
    for i in code55:
        if i[procedureCode].replace(' ', '').lower() == '97155':
            if i[providerId] in list(risen_supervisors['ProviderId']):
                # errors.append(i)
                # providersErrors.append(i[providerId])
                i[procedureCode] = '97155:non-billeable'
                continue
            rbt55_depured.append(i)

    for i in code53:
        if i[procedureCode].replace(' ', '').lower() == 'documentation':
        
            if i[providerId] in list(supervisors['ProviderId']):
                errors.append(i)
                providersErrors.append(i[providerId])
                continue
            
            elif i[providerId] in list(risen_supervisors['ProviderId']):
                errors.append(i)
                providersErrors.append(i[providerId])
                continue
            
        rbt53_depured.append(i)
        
    if len(doc_depured) > 0:
        doc_depured = np.stack(doc_depured, axis=0)
    if len(code55) > 0:
        rbt55_depured = np.stack(code55, axis=0)
    if len(rbt53_depured) > 0:
        rbt53_depured = np.stack(rbt53_depured, axis=0) 
    if len(depured_data) > 0:    
        depured_data = np.stack(depured_data, axis=0)
    if len(errors) > 0:
        errors = np.stack(errors, axis=0)

    overlappings = {}
    providers_data_with_errors = {}

    for i in np.concatenate((doc_depured, rbt53_depured, rbt55_depured)):
    
        new_ol = calculate_overlapping(i, providerName=providerName, providerId=providerId, depured_data=depured_data, procedureCode=procedureCode, 
                                       client=client, timeFrom=timeFrom, timeTo=timeTo, risen_supervisors=risen_supervisors)

        if i[providerId] in providersErrors:
            if not i[providerId] in providers_data_with_errors:
                overlappings[i[providerId]] = []

            providers_data_with_errors[i[providerId]].append(new_ol) 
            continue
        
        if not i[providerId] in overlappings:
            overlappings[i[providerId]] = []

        if len(new_ol) != 0:
            overlappings[i[providerId]].append(new_ol) 

    # for i in rbt53_depured:
    #     new_ol = calculate_overlapping(i,  providerName=providerName, providerId=providerId, depured_data=depured_data, procedureCode=procedureCode, 
    #                                    client=client, timeFrom=timeFrom, timeTo=timeTo)

    #     if i[providerId] in providersErrors:
    #         if not i[providerId] in providers_data_with_errors:
    #             overlappings[i[providerId]] = []

    #         providers_data_with_errors[i[providerId]].append(new_ol) 
    #         continue
        
    #     if not i[providerId] in overlappings:
    #         overlappings[i[providerId]] = []

    #     if len(new_ol) != 0:
    #         overlappings[i[providerId]].append(new_ol) 

    notifications = pd.DataFrame(np.stack(notifications, axis=0), columns=cols)

    import json
    if len(errors) > 0:
        with open('overlapping_missing_errors.json', 'w') as f:
            f.write(json.dumps(providers_data_with_errors))
        with open('supervisors_data.json', 'w') as f:
            f.write(json.dumps(supervisors_data))
    if len(notifications) > 0:
        with open('auto_fixed_errors.json', 'w') as f:
            notifications.to_csv('auto_fixed.csv')


    lab = list(cols)
    lab.append('MeetingDuration')

    for i in overlappings:
        ol = []
        for j in overlappings[i]:
            d,i_ol,time = j[0]
            i_ol = np.append(i_ol,time)
            ol.append(i_ol)
        if len(ol) > 0:
            ol = pd.DataFrame(np.stack(ol, axis=0), columns=lab)
            ol.to_csv(path.join('done',str(i)+'.csv'))
        
    if len(errors) > 0:
        return 'errors'
    if len(notifications):
        return 'notifications'
    return 'ok'