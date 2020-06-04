import time
import json

from vk_api import VkApi
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard
from vk_api.utils import get_random_id
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np


class GetInfo:
    def __init__(self, login, password, token, target):
        self.vk = VkApi(login, password)
        self.vk.auth()
        self.token = token
        self.target = target

        self.members = []
        self.count_of_members = 0

    def get_members_ids(self):
        offset = 0
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
        print('Get ids done')
        with open(f'{str(self.target)}_ids.json', 'w') as outfile:
            json.dump(self.members, outfile)
        print('Ids wrote')
        return None

    def get_users_data(self):
        print('Ids loaded')
        members_ids = json.load(open(f'{self.target}_ids.json'))

        offset = 0
        members_data = []
        while offset<len(members_ids):
            members = members_ids[offset:offset+1000]
            members_str = ','.join(map(str, members))
            members_data += self.vk.method('users.get', {'user_ids':members_str, 'fields':'bdate, sex'})
            offset += 1000
            print(f'Get users gata: {offset}/{len(members_ids)}')

        print('Get users data done')
        with open(f'{str(self.target)}_data.json', 'w') as outfile:
            json.dump(members_data, outfile)
        print('Users data wrote')
        return None

    def calculate(self):
        members_data = json.load(open(f'{str(self.target)}_data.json'))
        print('Users data loaded')

        mens = 0
        womans =0
        no_sex = 0
        deleted = 0
        banned = 0
        active = 0
        open_accounts=0
        closed_accounts=0

        bdate_mans = []
        bdate_womans = []
        print('Calculate...')
        for data in members_data:
            if 'deactivated' in data:
                if data['deactivated']=='deleted':
                    deleted+=1
                elif data['deactivated']=='banned':
                    banned+=1
            else:
                active += 1
                if data['is_closed']==False:
                    open_accounts +=1
                    if data['sex']==1:
                        womans += 1
                    elif data['sex']==2:
                        mens += 1
                    else:
                        no_sex +=1

                    if 'bdate' in data:
                        if len(data['bdate'].split('.'))==3:
                            year = int((data['bdate'].split('.'))[2])
                            if year>1960:
                                if data['sex']!=0:
                                    bdate_mans.append(year) if data['sex']==2 else bdate_womans.append(year)
                else:
                    closed_accounts +=1

        print('Plotting...')
        bdate_womans = np.array(bdate_womans)
        bdate_mans = np.array(bdate_mans)
        bins = np.arange(min(bdate_womans), max(bdate_womans) + 1, 1)

        fig, ax1 = plt.subplots()
        fig.set_size_inches((16, 9), forward=False)

        plt.hist(bdate_womans, bins=bins, alpha=0.5, color='pink', align='left', stacked=True)
        plt.hist(bdate_mans, bins=bins, alpha=0.5, color='blue', align='left')


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

        plt.title(f'Возрастно-половая диаграмма сообщества: {self.target}')
        
        a = mpatches.Patch(color='blue', label=f'Mens = {mens} ({int(100*(mens/(mens+womans)))}%)')
        b = mpatches.Patch(color='pink', label=f'Womans = {womans} ({int(100*(womans/(mens+womans)))}%)')
        c = mpatches.Patch(color='gray', label=f'deleted = {deleted} ({int(100*(deleted/(banned+active+deleted)))}%)')
        d = mpatches.Patch(color='gray', label=f'banned = {banned} ({int(100*(banned/(banned+active+deleted)))}%)')
        e = mpatches.Patch(color='gray', label=f'active = {active} ({int(100*(active/(banned+active+deleted)))}%)')
        f = mpatches.Patch(color='gray', label=f'open_accounts = {open_accounts} ({int(100*(open_accounts/(open_accounts+closed_accounts)))}%)')
        g = mpatches.Patch(color='gray', label=f'closed_accounts = {closed_accounts} ({int(100*(closed_accounts/(open_accounts+closed_accounts)))}%)')
        z = mpatches.Patch(color='gray', label=f'total = {len(members_data)}')

        plt.legend(handles=[a,b,c,d,e,f,g,z], loc='upper left')

        plt.savefig(f'data/{self.target}.png', dpi=420, bbox_inches='tight')
        print(f'Plot save in data/{self.target}.png')
        return None

if __name__=='__main__':
    TARGET = 'sessiyabot'

    login, password, token = json.load(open('secret.json'))
    getter = GetInfo(login, password, token, TARGET)
    getter.get_members_ids()
    getter.get_users_data()
    getter.calculate()
    print('Done')