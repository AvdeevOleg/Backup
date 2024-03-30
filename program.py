import os
import json
import requests
from tqdm import tqdm

class VkDownloader:
    def __init__(self, user_id, vk_token):
        self.user_id = user_id
        self.vk_token = vk_token

    def get_photos(self, offset=0, count=5):
        url = 'https://api.vk.com/method/photos.get'
        params = {
            'owner_id': self.user_id,
            'album_id': 'profile',
            'access_token': self.vk_token,
            'v': '5.131',
            'extended': '1',
            'photo_sizes': '1',
            'count': count,
            'offset': offset
        }
        res = requests.get(url=url, params=params)
        return res.json()

    def download_photos(self):
        data = self.get_photos()
        photos = []
        try:
            items = data['response']['items']
        except KeyError:
            print('Ошибка при получении фотографий:', data)
            return photos

        if not os.path.exists('images_vk'):
            os.makedirs('images_vk')
        for photo in items:
            sizes = photo.get('sizes')
            if not sizes:
                print(f'Фото {photo["likes"]["count"]} не содержит информации о размерах')
                continue
            max_size_photo = max(sizes, key=lambda x: x['height'] * x['width'])
            photo_url = max_size_photo['url']
            file_name = f"{photo['likes']['count']}.jpg"
            with open(f'images_vk/{file_name}', 'wb') as file:
                img = requests.get(photo_url)
                file.write(img.content)
            photos.append({'file_name': file_name, 'size': max_size_photo['type']})
        return photos

class YaUploader:
    def __init__(self, ya_token, folder_name):
        self.ya_token = ya_token
        self.folder_name = folder_name

    def create_folder(self):
        url = f'https://cloud-api.yandex.net/v1/disk/resources'
        headers = {'Authorization': f'OAuth {self.ya_token}'}
        params = {'path': self.folder_name}
        response = requests.put(url=url, headers=headers, params=params)
        if response.status_code == 201:
            print(f'Папка "{self.folder_name}" успешно создана на Яндекс.Диске')
        elif response.status_code == 409:
            print(f'Папка "{self.folder_name}" уже существует на Яндекс.Диске')
        else:
            print('Ошибка при создании папки:', response.text)

    def upload_photos(self, photos):
        url = f'https://cloud-api.yandex.net/v1/disk/resources/upload'
        headers = {'Authorization': f'OAuth {self.ya_token}'}
        for photo in tqdm(photos, desc='Uploading photos', unit='photo'):
            file_path = f'images_vk/{photo["file_name"]}'
            params = {'path': f'{self.folder_name}/{photo["file_name"]}', 'overwrite': 'true'}
            with open(file_path, 'rb') as file:
                response = requests.get(url=url, headers=headers, params=params)
                href = response.json().get('href')
                requests.put(href, data=file)

def main():
    user_id = input('Введите ID пользователя VK: ')
    vk_token = input('Введите токен доступа VK: ')
    ya_token = input('Введите токен Яндекс.Диска: ')
    folder_name = input('Введите имя папки на Яндекс.Диске для сохранения фотографий: ')

    vk_downloader = VkDownloader(user_id, vk_token)
    photos = vk_downloader.download_photos()

    if not photos:
        print('Не удалось загрузить фотографии, завершение программы')
        return

    ya_uploader = YaUploader(ya_token, folder_name)
    ya_uploader.create_folder()
    ya_uploader.upload_photos(photos)

    with open("photos.json", "w") as file:
        json.dump(photos, file, indent=4)

if __name__ == '__main__':
    main()
