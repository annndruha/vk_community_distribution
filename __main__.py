import time
import json
import os

from vk_api import VkApi
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np


class GetInfo:
    def __init__(self, login, password, target, type = 'group_members'):
        self.vk = VkApi(login, password)
        self.vk.auth()

        self.target = target
        self.type = type

        self.members = []
        self.bdate_mans = []
        self.bdate_womans = []
        self.count_of_members = 0
        self.mens = 0
        self.womans =0
        self.no_sex = 0
        self.deleted = 0
        self.banned = 0
        self.active = 0
        self.open_accounts=0
        self.closed_accounts=0


    def get_members_ids(self):
        offset = 0
        if not os.path.exists(str(self.target)):
            os.makedirs(str(self.target))

        if self.type == 'group_members':
            self.count_of_members = self.vk.method('groups.getMembers', {'group_id':self.target, 'count':1})['count']
            start_time = time.time()
            while len(self.members)<self.count_of_members:
                print(f'Get ids: {len(self.members)}/{self.count_of_members}')
                self.members += self.vk.method('execute',
                    {'code':
                        '''var members = [];
                        var offset = %i; 
                        var i = 0;
                        var members_count = %i;

                        while ((i<25) &&(offset<members_count))
                        {
                        members = members + API.groups.getMembers({"group_id":"%s", "offset":offset })["items"];
                        i = i + 1;
                        offset = offset + 1000;
                        };
                        return members;''' % (offset, self.count_of_members, self.target)
                    })
                offset +=25000
                print(f'Users: {len(self.members)}\t Time:{time.time()-start_time}')

        elif self.type == 'user_friends':
            print(f'Get friens ids...')
            try:
                id = int(self.target.replace('id',''))
            except:
                id = self.vk.method('users.get', {'user_ids':self.target})[0]['id']
            else:
                self.vk.method('friends.get', {'user_id':id})

            self.members +=self.vk.method('friends.get', {'user_id':id})["items"]
            self.count_of_members = len(self.members)
            print(f'Users: {self.count_of_members}')

        print('Get ids done')
        with open(f'{self.target}/{self.target}_ids.json', 'w') as outfile:
            json.dump(self.members, outfile)
        print('Ids wrote')
        return None

    def get_users_data(self):
        print('Ids loaded')
        members_ids = json.load(open(f'{self.target}/{self.target}_ids.json'))

        offset = 0
        members_data = []
        start_time = time.time()
        while offset<len(members_ids):
            members = members_ids[offset:offset+1000]
            members_str = ','.join(map(str, members))
            members_data += self.vk.method('users.get', {'user_ids':members_str, 'fields':'bdate, sex'})
            offset += 1000
            print(f'Get users gata: {len(members_data)}/{len(members_ids)}\t Time:{time.time()-start_time}')

        print('Get users data done')
        with open(f'{self.target}/{self.target}_data.json', 'w') as outfile:
            json.dump(members_data, outfile)
        print('Users data wrote')
        return None

    def calculate(self):
        members_data = json.load(open(f'{self.target}/{self.target}_data.json'))
        print('Users data loaded')

        print('Calculate...')
        for data in members_data:
            if 'deactivated' in data:
                if data['deactivated']=='deleted':
                    self.deleted+=1
                elif data['deactivated']=='banned':
                    self.banned+=1
            else:
                self.active += 1
                if data['is_closed']==True:
                    self.closed_accounts +=1
                else:
                    self.open_accounts +=1
                    if data['sex']==1:
                        self.womans += 1
                    elif data['sex']==2:
                        self.mens += 1
                    else:
                        self.no_sex +=1

                    if 'bdate' in data:
                        if len(data['bdate'].split('.'))==3:
                            year = int((data['bdate'].split('.'))[2])
                            if year>1960:
                                if data['sex']!=0:
                                    if data['sex']==2:
                                        self.bdate_mans.append(year)
                                    else:
                                        self.bdate_womans.append(year)
        print('Calculate done')
        return None

    def make_plot(self):
        print('Plotting...')
        bdate_womans = np.array(self.bdate_womans)
        bdate_mans = np.array(self.bdate_mans)
        bins = np.arange(min(bdate_womans), max(bdate_womans) + 1, 1)

        fig, ax1 = plt.subplots()
        fig.set_size_inches((16, 9), forward=False)

        bdates = np.array([bdate_womans, bdate_mans])
        ax1.hist(bdates, bins, histtype='bar', align='left', color = ['violet','slateblue'])

        labels = [str(i) for i in bins]
        ax1.set_xticks(bins)
        ax1.set_xticklabels(labels, rotation=90)
        ax1.set_xlabel("Год рождения")
        ax1.set_ylabel("Количество человек")
        

        labels_top = [str(2020-i) for i in bins]
        ax2 = ax1.twiny()
        ax2.set_xlim(ax1.get_xlim())
        ax2.set_xticks(bins)
        ax2.set_xticklabels(labels_top, rotation=90)
        ax2.set_xlabel("Возраст")

        plt.title(f'Возрастно-половая диаграмма: {self.target}')
        
        a = mpatches.Patch(color='slateblue', label=f'Mens = {self.mens} ({int(100*(self.mens/(self.mens+self.womans)))}%)')
        b = mpatches.Patch(color='violet', label=f'Womans = {self.womans} ({int(100*(self.womans/(self.mens+self.womans)))}%)')
        c = mpatches.Patch(color='gray', label=f'deleted = {self.deleted} ({int(100*(self.deleted/(self.banned+self.active+self.deleted)))}%)')
        d = mpatches.Patch(color='gray', label=f'banned = {self.banned} ({int(100*(self.banned/(self.banned+self.active+self.deleted)))}%)')
        e = mpatches.Patch(color='gray', label=f'active = {self.active} ({int(100*(self.active/(self.banned+self.active+self.deleted)))}%)')
        f = mpatches.Patch(color='gray', label=f'open_accounts = {self.open_accounts} ({int(100*(self.open_accounts/(self.open_accounts+self.closed_accounts)))}%)')
        g = mpatches.Patch(color='gray', label=f'closed_accounts = {self.closed_accounts} ({int(100*(self.closed_accounts/(self.open_accounts+self.closed_accounts)))}%)')
        z = mpatches.Patch(color='gray', label=f'total = {len(self.members)}')

        plt.legend(handles=[a,b,c,d,e,f,g,z], loc='upper left')

        plt.savefig(f'{self.target}/{self.target}.png', dpi=420, bbox_inches='tight')
        print(f'Plot save in {self.target}/{self.target}.png')
        return None

if __name__=='__main__':
    TARGET = 'sessiyabot'

    login, password = json.load(open('secret.json'))
    getter = GetInfo(login, password, TARGET, type = 'user_friends') # or type = 'group_members'
    getter.get_members_ids()
    getter.get_users_data()
    getter.calculate()
    getter.make_plot()
    print('Done')