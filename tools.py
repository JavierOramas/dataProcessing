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
labels = ['DateTimeFrom', 'DateTimeTo','TimeWorkedInHours', 'ClientFirstName','ProviderId', 'ProviderFirstName', 'ProcedureCodeId','DateOfService', 'ClientId']

def get_data():
    df = pd.read_csv('data.csv')
    return df.drop(df.columns.difference(labels), 1)

def verify_valid_overlapping(entry, i, providerName, procedureCodeId, providerId):
    procedure = entry[procedureCodeId]
    id = entry[providerId]
    if entry[providerId] == i[providerId]:
        return False
    if entry[providerId] in RBTs and i[providerId] in trainees:
        return False

    if procedure in [150582, 194640] and i[procedureCodeId] in [150582, 194640]:
        return True
    if procedure in [150580] and i[procedureCodeId] in [150582, 194640]:
        return True
    if procedure == 194642 and i[procedureCodeId] == 150577:
        return True
    return False

def calculate_overlapping(entry, providerName,providerId,depured_data, procedureCodeId, client, DateTimeFrom, timeTo, risen_supervisors):
    overlapping = []

    try:
        entry_start = datetime.strptime(entry[DateTimeFrom], '%m/%d/%Y %H:%M')
        entry_end = datetime.strptime(entry[timeTo], '%m/%d/%Y %H:%M')
    except:
        try:
            entry_start = datetime.strptime(entry[DateTimeFrom], '%m/%d/%Y %H:%M:%S')
            entry_end = datetime.strptime(entry[timeTo], '%m/%d/%Y %H:%M:%S')
        except:
            pass

    for i in depured_data:
        # print(verify_valid_overlapping(entry,i,providerName,procedureCodeId,providerId, risen_supervisors))
        if  verify_valid_overlapping(entry,i,providerName,procedureCodeId,providerId):
            try:
                start = datetime.strptime(i[DateTimeFrom], '%m/%d/%Y %H:%M')
                end = datetime.strptime(i[timeTo], '%m/%d/%Y %H:%M')
            except:
                start = datetime.strptime(i[DateTimeFrom], '%m/%d/%Y %H:%M:%S')
                end = datetime.strptime(i[timeTo], '%m/%d/%Y %H:%M:%S')

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
    elif overlapping[0][1][procedureCodeId] == 150580:
        providersErrors.append(overlapping[0][1][providerId])

    return overlapping

def process(fix=False):

    supervisors = providers_data[providers_data['Type'] == 'Supervisor']
    risen_supervisors = providers_data[providers_data['Type'] == 'Risen Supervisor']
    trainees = providers_data[providers_data['Status'] == 'Trainee']
    RBTs = providers_data[providers_data['Status'] == 'RBT']
    data = get_data()


    valid = [150582, 194640, 150577, 150580, 194642,194641]
    supervisors_id = [150582, 194640, 150577]
    supervisors_codes = ['risensupervisor', 'supervisor']

    # eliminar datos no deseados
    filter = [i in valid for i in data.ProcedureCodeId]
    data['Filter1'] = filter
    data = data[data.Filter1]
    data = data.drop('Filter1', 1)

    st.dataframe(data)

    errors = []
    notifications = []
    depured_data = []
    non_supervisors = []
    names = {}

    cols = data.columns

    providerId = list(cols).index('ProviderId')
    providerName = list(cols).index('ProviderFirstName')
    procedureCodeId = list(cols).index('ProcedureCodeId')
    # print(procedureCodeId)
    DateTimeFrom = list(cols).index('DateTimeFrom')
    timeTo = list(cols).index('DateTimeTo')
    client = list(cols).index('ClientId')
    clientName = list(cols).index('ClientFirstName')
    filter_supervisors =[i in supervisors_id for i in data.ProcedureCodeId]

    supervisors_data = data[filter_supervisors]

    supervisors_data = np.array(supervisors_data)

    # print(len(supervisors_data))

    for k in range(len(supervisors_data)):

        i = supervisors_data[k]
        if i[procedureCodeId] == 150577:
            if i[providerId] in list(trainees['ProviderId']):
                notifications.append(i)
                i[procedureCodeId] = 194642
                non_supervisors.append(i)
                continue
            elif i[providerId] in list(RBTs['ProviderId']):
                notifications.append(i)
                i[procedureCodeId] = 194642
                non_supervisors.append(i)
                continue

        if i[procedureCodeId] == 150582:
            if i[providerId] in list(risen_supervisors['ProviderId']+supervisors['ProviderId']) :
                notifications.append(i)
                i[procedureCodeId] = 194640
                depured_data.append(i)
                continue

            if i[providerId] in list(RBTs['ProviderId']):
                errors.append(i)
                providersErrors.append(i[providerId])
                continue

        if i[procedureCodeId] == 194640:
            # if i[providerId] in list(trainees['ProviderId']):
                # errors.append(i)
                # providersErrors.append(i[providerId])
                # continue
            if i[providerId] in list(RBTs['ProviderId']):
                errors.append(i)
                providersErrors.append(i[providerId])
                continue

        depured_data.append(i)

    # print(len(depured_data))
    code53 = np.array(data[[i == 150580 for i in data['ProcedureCodeId']]])
    code_doc = np.array(data[[i == 194642 for i in data['ProcedureCodeId']]])
    code55 = np.array(data[[i in [150582, 194640] for i in data['ProcedureCodeId']]])
    code_meeting = np.array(data[[i in [194641] for i in data['ProcedureCodeId']]])

    for i in code_doc:
        if i[procedureCodeId] == 194642:
            if i[providerId] in list(supervisors['ProviderId']):
                notifications.append(i)
                i[procedureCodeId] = 150577
                depured_data.append(i)
                continue

            elif i[providerId] in list(risen_supervisors['ProviderId']):
                notifications.append(i)
                i[procedureCodeId] = 150577
                depured_data.append(i)
                continue

        non_supervisors.append(i)

    for i in code55:
        if i[providerId] in list(risen_supervisors['ProviderId']):
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

    supervisors_meeting = []
    non_supervisors_meeting = []
    for i in code_meeting:
        if not i[providerId] in overlappings:
            overlappings[i[providerId]] = []
        
        if i[providerId] in list(supervisors['ProviderId']+risen_supervisors['ProviderId']):
            supervisors_meeting.append(i)
        else:
            non_supervisors_meeting.append(i)
    
    for i in non_supervisors_meeting:
        names[i[providerId]] = i[providerName]
        
        flag = False
        for j in supervisors_meeting:
            if i[DateTimeFrom] == j[DateTimeFrom]:
                overlappings[i[providerId]].append((i,j,datetime.strptime(i[timeTo], '%m/%d/%Y %H:%M')-datetime.strptime(i[DateTimeFrom], '%m/%d/%Y %H:%M')))
                flag = True
                break
        if not flag:
            overlappings[i[providerId]].append(('',i, datetime.strptime(i[timeTo], '%m/%d/%Y %H:%M')-datetime.strptime(i[DateTimeFrom], '%m/%d/%Y %H:%M')))
    
    for i in non_supervisors:

        names[i[providerId]] = i[providerName]

        new_ol = calculate_overlapping(i, providerName=providerName, providerId=providerId, depured_data=depured_data, procedureCodeId=procedureCodeId,
                                       client=client, DateTimeFrom=DateTimeFrom, timeTo=timeTo, risen_supervisors=risen_supervisors)

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


    lab = list(cols)
    lab.append('MeetingDuration')
    # print(overlappings)

    if not os.path.exists('done'):
        os.mkdir('done')
        
    for i in overlappings:
        ol = []
        final_labels = labels+['MeetingDuration']
        for j in overlappings[i]:
            try:
                d,i_ol,time = j[0]
                if time.seconds == 0:
                    continue
                i_ol = np.append(i_ol,time.seconds/3600)
                ol.append(i_ol)
            except:
                d,i_ol,time = j
                i_ol = np.append(i_ol,time.seconds/3600)
                ol.append(i_ol)
                
        if len(ol) > 0:
            ol = pd.DataFrame(np.stack(ol, axis=0), columns=lab)
            ol = ol[final_labels] 
            ol = ol.drop(['ClientId'], axis=1)
            ol.to_csv(path.join('done',names[i]+' '+str(i)+'.csv'))
        
    if len(errors) > 0:
        return 'errors'
    if len(notifications):
        return 'notifications'
    return 'ok'


if __name__ == '__main__':
    process()