import time
import json
import os
import requests
import urllib
import imutils

from vk_api import VkApi
import numpy as np
import cv2

# Загружает аватары друзей из вк
def load_avatars():
    login, password = json.load(open('secret.json'))
    vk = VkApi(login, password)
    vk.auth()

    target = 'annndruha'

    members = []
    try:
        id = int(target.replace('id',''))
    except:
        id = vk.method('users.get', {'user_ids':target})[0]['id']

    members = vk.method('friends.get', {'user_id':id})["items"]

    print(len(members))
    #print(members)

    members_str = ','.join(map(str, members))
    members_data = vk.method('users.get', {'user_ids':members_str, 'fields':'photo_400_orig'})


    for data in members_data:
        try:
            url = data['photo_400_orig']
            id = data['id']
            filename = f'avatars/{id}.jpg'

            response=requests.get(url)
            if response.status_code==200:
              with open(filename,'wb') as imgfile:
                imgfile.write(response.content)
        except:
            pass


# Обрезает их до разрешения первого аватара
def crop(img):
    n, m = img.shape[0], img.shape[1]
    if n<m:
        img = img[:, ((m-n)//2):n+((m-n)//2), : ]
    else:
        img = img[((n-m)//2):m+((n-m)//2), :, : ]
    return img

# усредняет аватары
PATH = 'anime'
imagelist = os.listdir(PATH)
images = []
for i, img_name in enumerate(imagelist):
    img_name = PATH +'/' + img_name
    print(f'Open: {img_name}')
    image = cv2.imread(img_name)
    
    #image = crop(image)
    #cv2.imwrite(img_name,image)
    
    image = imutils.resize(image.copy(), width=256, height= 256) #height= 256
    #if image.shape[1]==258: image=image[:,:256]
    cv2.imwrite(img_name, image)

    images.append(image/len(imagelist))


result = images[0]
for i in range(1,len(images)):
    result += images[i]

cv2.imwrite(PATH+'/_result.png', result)