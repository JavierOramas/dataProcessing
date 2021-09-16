import pandas as pd
import numpy as np
from os import path
from datetime import datetime
import streamlit as st 
import json
import os

risen_supervisors = pd.DataFrame([])

RBTs = []
trainees = []
risen_supervisors = []
supervisors = []
providersErrors = []

def get_providers():
    return pd.read_csv('providers.csv', sep=',')

providers_data = get_providers()
labels = ['TimeWorkedFrom', 'TimeWorkedTo','TimeWorkedInHours', 'ClientFirstName','ProviderId', 'ProviderFirstName', 'ProcedureCode','DateOfService', 'ClientId']

def get_data():
    df = pd.read_csv('data.csv')
    return df.drop(df.columns.difference(labels), 1)
    
def verify_valid_overlapping(entry, i, providerName, procedureCode, providerId):
    procedure = entry[procedureCode]
    id = entry[providerId]
    if entry[providerId] == i[providerId]:
        return False
    if entry[providerId] in RBTs and i[providerId] in trainees:
        return False
    
        
    if procedure.lower().replace(' ', '') in ['97155', '97155:non-billable'] and i[procedureCode].lower().replace(' ', '') in ['97155', '97155:non-billable']:
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
    
    for i in depured_data:
        # print(verify_valid_overlapping(entry,i,providerName,procedureCode,providerId, risen_supervisors))
        if  verify_valid_overlapping(entry,i,providerName,procedureCode,providerId):
            start = datetime.strptime(i[timeFrom], '%m/%d/%Y %H:%M')
            end = datetime.strptime(i[timeTo], '%m/%d/%Y %H:%M')
            if not i[client] == entry[client]:
                continue
            
            if (entry_start >= start and entry_start <= end) or (entry_end >= start and entry_end <= end) or (start >= entry_start and end <= entry_end):
                time = min(entry_end,end)-max(entry_start, start)
                if time != 0:
                    overlapping.append((entry,i, time))
    
    if len(overlapping) == 0:
        return []
    if len(overlapping) > 1:
        new_overlapping = ''
        for i in overlapping:
            if i[1][providerId] in risen_supervisors:
                overlapping = [i]
                break
            if i[1][providerId] in supervisors:
                new_overlapping = [i]
            if new_overlapping == '' and i[1][providerId] in trainees:
                new_overlapping = [i]
        if new_overlapping != '':
            overlapping == new_overlapping
    elif overlapping[0][1][procedureCode].lower().replace(' ', '') == '97153:non-billable':
        providersErrors.append(overlapping[0][1][providerId])

    return overlapping

def process(fix=False):    
    
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
    names = {}
    
    cols = data.columns

    providerId = list(cols).index('ProviderId')
    providerName = list(cols).index('ProviderFirstName')
    procedureCode = list(cols).index('ProcedureCode')
    timeFrom = list(cols).index('TimeWorkedFrom')
    timeTo = list(cols).index('TimeWorkedTo')
    client = list(cols).index('ClientId')
    clientName = list(cols).index('ClientFirstName')

    filter_supervisors =[i.replace(' ', '').lower() in supervisors_codes for i in data.ProcedureCode]
    
    supervisors_data = data[filter_supervisors]

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
            # if i[providerId] in list(trainees['ProviderId']):
                # errors.append(i)
                # providersErrors.append(i[providerId])
                # continue
            if i[providerId] in list(RBTs['ProviderId']):
                errors.append(i)
                providersErrors.append(i[providerId])
                continue
            
        depured_data.append(i)

    code53 = np.array(data[[i.lower().replace(' ', '') == '97153' for i in data['ProcedureCode']]])
    code_doc = np.array(data[[i.lower().replace(' ', '') == 'documentation' for i in data['ProcedureCode']]])
    code55 = np.array(data[[i.lower().replace(' ', '') in ['97155', '97155:non-billable'] for i in data['ProcedureCode']]])
    
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
        # if i[procedureCode].replace(' ', '').lower() == '97155':
        if i[providerId] in list(risen_supervisors['ProviderId']):
            # errors.append(i)
            # providersErrors.append(i[providerId])
            # i[procedureCode] = '97155:non-billable'
            depured_data.append(i)
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
        
    # print(non_supervisors)
    if len(non_supervisors) > 0:
        non_supervisors = np.stack(non_supervisors, axis=0)
    if len(depured_data) > 0:    
        depured_data = np.stack(depured_data, axis=0)
    if len(errors) > 0:
        errors = np.stack(errors, axis=0)

    overlappings = {}
    providers_data_with_errors = {}
        
    for i in non_supervisors:
        
        names[i[providerId]] = i[providerName]
        
        new_ol = calculate_overlapping(i, providerName=providerName, providerId=providerId, depured_data=depured_data, procedureCode=procedureCode, 
                                       client=client, timeFrom=timeFrom, timeTo=timeTo, risen_supervisors=risen_supervisors)
        
        if i[providerId] in providersErrors:

            if not i[providerId] in providers_data_with_errors:
                providers_data_with_errors[i[providerId]] = []

            providers_data_with_errors[i[providerId]].append(new_ol) 
        
        else:
            if not i[providerId] in overlappings:
                overlappings[i[providerId]] = []

            if len(new_ol) != 0:
                overlappings[i[providerId]].append(new_ol) 

    
    
    if len(errors) > 0:  
        pd.DataFrame(errors).to_csv('errors.csv')
        pd.DataFrame(supervisors_data).to_csv('supervisors_data.csv')
    if len(notifications) > 0:
        notifications = pd.DataFrame(np.stack(notifications, axis=0), columns=cols)
        notifications.to_csv('auto_fixed.csv')


    lab = list(labels)
    lab.append('MeetingDuration')
    # print(overlappings)
    
    if not os.path.exists('done'):
        os.mkdir('done')
        
    for i in overlappings:
        ol = []
        for j in overlappings[i]:
            d,i_ol,time = j[0]
            if time == 0:
                continue
            i_ol = np.append(i_ol,time.seconds/3600)
            ol.append(i_ol)
        if len(ol) > 0:
            ol = pd.DataFrame(np.stack(ol, axis=0), columns=lab)
            ol = ol.drop(['ClientId'], axis=1)
            ol.to_csv(path.join('done',names[i]+' '+str(i)+'.csv'))
        
    if len(errors) > 0:
        return 'errors'
    if len(notifications):
        return 'notifications'
    return 'ok'


if __name__ == '__main__':
    process()