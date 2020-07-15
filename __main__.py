import time
import json
import os

from vk_api import VkApi
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np


class GetInfo:
    def __init__(self, login, password, target, type = 'group_members', normed = False):
        self.vk = VkApi(login, password)
        self.vk.auth()

        self.target = target
        self.type = type
        self.normed = normed

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
        self.avg_mens = 0
        self.avg_womans = 0


    def get_members_ids(self):
        offset = 0
        if not os.path.exists(str(self.target)):
            os.makedirs(str(self.target))

        try:
            if self.type == 'group_members':
                self.count_of_members = self.vk.method('groups.getMembers', {'group_id':self.target, 'count':1})['count']
                start_time = time.time()
                while len(self.members)<self.count_of_members:
                    _persent = int(100*len(self.members)/self.count_of_members)
                    _mem = f'{len(self.members)}/{self.count_of_members}'
                    _time = "%.1f" % (time.time()-start_time)
                    _time_left = "%.1f" % (self.count_of_members*(time.time()-start_time)/(len(self.members)+1)-(time.time()-start_time))
                    print(f'Geting ids... {_persent}% ({_mem})\t time: {_time} \t left: {_time_left}')
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

            print('Get ids done. Saving...')
        except Exception as err:
            print(f'Exception: {str(err)}')

        with open(f'{self.target}/{self.target}_ids.json', 'w') as outfile:
            json.dump(self.members, outfile)
        print('Ids saved.')
        return None

    def get_users_data(self):
        print('Ids loading...')
        members_ids = json.load(open(f'{self.target}/{self.target}_ids.json'))
        print('Ids loaded. Start getting data...')

        try:
            offset = 0
            members_data = []
            start_time = time.time()
            while offset < len(members_ids):

                members = members_ids[offset:offset+1000]
                members_str = ','.join(map(str, members))
                members_data += self.vk.method('users.get', {'user_ids':members_str, 'fields':'bdate, sex'})
                offset += 1000

                _persent = int(100*len(members_data)/len(members_ids))
                _mem = f'{len(members_data)}/{len(members_ids)}'
                _time = "%.1f" % (time.time()-start_time)
                _time_left = "%.1f" % (len(members_ids)*(time.time()-start_time)/(len(members_data))-(time.time()-start_time))
                print(f'Geting data... {_persent}% ({_mem})\t time: {_time} \t left: {_time_left}')

            print('Get users data done. Saving...')
        except Exception as err:
            print(f'Exception: {str(err)}')

        with open(f'{self.target}/{self.target}_data.json', 'w') as outfile:
            json.dump(members_data, outfile)
        print('Users data saved.')
        return None

    def calculate(self):
        print('Users data loading...')
        members_data = json.load(open(f'{self.target}/{self.target}_data.json'))
        self.count_of_members = len(members_data)
        print('Users data loaded.')

        print('Calculate...')
        for data in members_data:
            if 'deactivated' in data:
                if data['deactivated']=='deleted':self.deleted+=1
                else: self.banned+=1
                continue

            self.active += 1
            if data['is_closed']: self.closed_accounts +=1
            else: self.open_accounts +=1
            
            if data['sex']==1: self.womans += 1
            elif data['sex']==2: self.mens += 1
            else: self.no_sex +=1   

            if (('bdate' in data) and (len(data['bdate'].split('.'))==3)): # Если дата указана и содержит год рожения
                year = int((data['bdate'].split('.'))[2])
                if year>1960: # Хвост графика из фейковых дат рождения нас не интересует
                    if data['sex']==1: self.bdate_womans.append(year)
                    elif data['sex']==2: self.bdate_mans.append(year)
                        
        print('Calculate done.')
        return None

    def make_plot(self):
        print('Plotting...')
        bdate_mans = np.array(self.bdate_mans)
        bdate_womans = np.array(self.bdate_womans)
        self.avg_mens = np.average(bdate_mans)
        self.avg_womans = np.average(bdate_womans)
        bins = np.arange(min(min(bdate_womans),min(bdate_mans)), max(max(bdate_womans),max(bdate_mans))+1, 1)

        fig, ax1 = plt.subplots()
        fig.set_size_inches((16, 9), forward=False)

        if self.normed: # Нормируется соотношение полов, основываясь на общем соотношении, независимо от числа открытых женских аккаунтов
            norm_koeff = (self.mens/self.womans)/(len(bdate_mans)/len(bdate_womans))
            bincount_m = np.bincount(bdate_mans)[1961:]*norm_koeff
            bincount_w = np.bincount(bdate_womans)[1961:]

        else:
            bincount_m = np.bincount(bdate_mans)[1961:]
            bincount_w = np.bincount(bdate_womans)[1961:]
            if len(bincount_m)<len(bincount_w):
                n = len(bincount_w)-len(bincount_m)
                bincount_m = np.pad(bincount_m, [(0,n)], mode='constant')
            else:
                n = len(bincount_m)-len(bincount_w)
                bincount_w = np.pad(bincount_w, [(0,n)], mode='constant')

        try:
            width = 0.4
            ax1.bar(bins- width/2, bincount_w, width, label = 'W', color = ['violet'])
            ax1.bar(bins+ width/2, bincount_m, width, label = 'M', color = ['slateblue'])
        except:
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

        try:
            if self.type == 'group_members':
                group_info = self.vk.method('groups.getById', {'group_ids':self.target})
                plt.title(f'''"{group_info[0]["name"]}" - Возрастно-половая диаграмма''')
            else:
                user_info = self.vk.method('users.get', {'user_ids':self.target})[0]
                first_name, last_name = user_info['first_name'], user_info['last_name']
                plt.title(f'Возрастно-половая диаграмма друзей: {first_name} {last_name}')
        except:
            plt.title(f'Возрастно-половая диаграмма: {self.target}')
        
        a = mpatches.Patch(color='slateblue', label=f'Мужчин: {self.mens} ({int(100*(self.mens/(self.mens+self.womans)))}%)')
        b = mpatches.Patch(color='violet', label=f'Женщин: {self.womans} ({int(100*(self.womans/(self.mens+self.womans)))}%)')

        c = mpatches.Patch(color='white', label ='')
        d = mpatches.Patch(color='gray', label=f'Активных: {self.active} ({int(100*(self.active/(self.banned+self.active+self.deleted)))}%)')
        e = mpatches.Patch(color='gray', label=f'Активных закрытых: {self.closed_accounts} ({int(100*(self.closed_accounts/(self.open_accounts+self.closed_accounts)))}%)')
        f = mpatches.Patch(color='gray', label=f'Активных открытых: {self.open_accounts} ({int(100*(self.open_accounts/(self.open_accounts+self.closed_accounts)))}%)')
        g = mpatches.Patch(color='gray', label=f'Удалённых: {self.deleted} ({int(100*(self.deleted/(self.banned+self.active+self.deleted)))}%)')
        h = mpatches.Patch(color='gray', label=f'Заблокированных: {self.banned} ({int(100*(self.banned/(self.banned+self.active+self.deleted)))}%)')
        i = mpatches.Patch(color='gray', label=f'Всего: {self.count_of_members}')

        j = mpatches.Patch(color='white', label ='')
        k = mpatches.Patch(color='gray', label=f'Указан год и пол: {len(bdate_womans)+len(bdate_mans)} ({int(100*((len(bdate_womans)+len(bdate_mans))/self.count_of_members))}%)')
        l = mpatches.Patch(color='gray', label=f'из них: М: {len(bdate_mans)} ({int(100*(len(bdate_mans)/(len(bdate_womans)+len(bdate_mans))))}%) Ж: {len(bdate_womans)} ({int(100*(len(bdate_womans)/(len(bdate_womans)+len(bdate_mans))))}%)')
        m = mpatches.Patch(color='gray', label =f'Нормировка графика по полу: {self.normed}')
        n = mpatches.Patch(color='gray', label =f'Ср. возраст мужчин: {2020-int(self.avg_mens)}')
        o = mpatches.Patch(color='gray', label =f'Ср. возраст женщин: {2020-int(self.avg_womans)}')


        plt.legend(handles=[a,b,c,d,e,f,g,h,i,j,k,l,m,n,o], loc='upper left')

        plt.savefig(f'{self.target}/{self.target}.png', dpi=320, bbox_inches='tight')
        print(f'Plot save in {self.target}/{self.target}.png')
        return None

if __name__=='__main__':

    TARGET = 'miraprinse'

    login, password = json.load(open('secret.json'))
    getter = GetInfo(login, password, TARGET, type = 'user_friends', normed = False) # or type = 'group_members'/'user_friends'
    getter.get_members_ids()
    getter.get_users_data()
    getter.calculate()
    getter.make_plot()
    print('Program ended.')
