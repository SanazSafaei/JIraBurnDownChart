from datetime import datetime
import json
from time import strptime
import zoneinfo
import requests
import matplotlib.pyplot as plt
from requests.auth import HTTPBasicAuth
import yaml
from yaml.loader import SafeLoader


class Jira:

    cookies = None
    issues = []
    sprint = 0

    from_status = ''
    to_status = ''

    def __init__(self) -> None:

        with open('credential.yml') as f:
            data = yaml.load(f, Loader=SafeLoader)

        user_name = data['user_name']
        password = data['password']
        self.base_url = ['base_url']

        self.from_status = input('from status: ')
        self.to_status = input('to status: ')

        self.sprint = int(input("Sprint ID: "))
        
        data = {"username" : user_name, "password": password}

        res = requests.post(f'{self.base_url}/auth/1/session', json=data)
        self.cookies = res.cookies


    def getSprintData(self)-> list:

        try:
            res = requests.get(f'{self.base_url}/agile/1.0/sprint/{self.sprint}/', cookies = self.cookies)
            sprint = res.json()

            start_date = datetime.strptime(sprint['startDate'], '%Y-%m-%dT%H:%M:%S.%f%z').astimezone(zoneinfo.ZoneInfo('Iran'))
            end_date = datetime.strptime(sprint['endDate'], '%Y-%m-%dT%H:%M:%S.%f%z').astimezone(zoneinfo.ZoneInfo('Iran'))
            length = end_date - start_date
    
            return {
                'name': sprint['name'],
                'start_date': start_date,
                'end_date': end_date,
                'length': length.days
            }
        except:
            print('spirint is not available')


    def getSprintTickets(self) -> list:
        try:
            res = requests.get(f'{self.base_url}/agile/1.0/sprint/{self.sprint}/issue/?maxResults=200&expand=changelog', cookies = self.cookies)
            sprint = res.json()
            self.issues = sprint.get('issues')
            return self.issues
        except:
            print('could not get tickets')


    def createBurnDownChart(self):

        tickets = self.getSprintTickets()
        sprint = self.getSprintData()

        total = 0

        done = [0]*sprint['length']
        
        for ticket in tickets:
            if(ticket['fields']['customfield_10106']):
                ticket_fields = ticket['fields']
                total = total + ticket_fields['customfield_10106']
                if(ticket_fields['status']['name'] in ('Ready To Deploy', 'Ready To Test', 'Closed', 'Testing', 'Test Passed')):
                    endedAt = self.getTicketEndDate(ticket)
                    index = (endedAt - sprint['start_date']).days
                    if(0<index and index<len(done)):
                        done[index-1] = done[index-1] + ticket_fields['customfield_10106']

           
        x = [i for i in range(0, len(done))]
        temp = 0
        y= []
        for i in range(0, len(done)):
            temp = done[i] + temp
            y.append(total - temp)
        plt.plot(x, y)
        plt.xlabel('days')
        plt.ylabel('story points')
        plt.title('Burndown Chart')
        plt.show()


    def getTicketEndDate(self, ticket):

        for t in ticket:
            if(t == 'changelog'):
                for log in ticket[t]['histories']:
                    for item in log['items']:
                        if(item['field'] == 'status'):
                            if(item['toString'] == 'Ready To Test'):
                                endedAt = datetime.strptime(log['created'], '%Y-%m-%dT%H:%M:%S.%f%z').astimezone(zoneinfo.ZoneInfo('Iran'))
                                return endedAt




        
        

    

j = Jira()
j.createBurnDownChart()
