import requests
import json
import re
from database import Hotel, City
from typing import List, Dict, Optional
from datetime import datetime


class RapidAPIRequests:
    """
    Класс для работы с RAPID API. Инициализируется токеном от rapidapi. Содержит методы,
    возвращающие данные по городам, отелям и список фотографий
    """

    def __init__(self, key: str) -> None:
        self.rapid_api_key = key

    def get_cities(self, city_name: str) -> str or List[City]:
        """
        :param city_name:
        :return: Список строк таблицы City
        """
        url = "https://hotels4.p.rapidapi.com/locations/search"

        querystring = {"query": city_name, "locale": "ru_RU"}

        headers = {
            'x-rapidapi-host': "hotels4.p.rapidapi.com",
            'x-rapidapi-key': self.rapid_api_key
        }

        try:
            response = requests.request("GET", url,
                                        headers=headers,
                                        params=querystring,
                                        timeout=15
                                        )
            print(response.status_code)
            if response.status_code != 200:
                return 'Ошибка ответа от сервера'
            cities_response = json.loads(response.text)["suggestions"][0]["entities"]
            # with open('City_info.json', 'w', encoding='utf-8') as file:
            #     json.dump(cities_response, file, indent=4, ensure_ascii=False)
            city_list = []
            for dict_city in cities_response:
                city = City.get_or_create(id=dict_city["destinationId"])[0]

                city.name = re.sub(r'<[^<]+?>', '', dict_city["caption"])
                city.save()
                city_list.append(city)
            for city in city_list:  # вывод результата в консоль для проверки работы
                print(city.name)
            return city_list

        except requests.exceptions.ReadTimeout as error:
            print(error, 'Время ожидания вышло')
            return 'Вышло время ожидания ответа от сервера, попробуйте снова'

    def get_hotels(self,
                   city_id: int,
                   hotels_amount: int,
                   check_in: datetime.date,
                   check_out: datetime.date,
                   sort: str,
                   distance: float or None = None,
                   max_price: int or None = None) -> str or List[Hotel]:
        """
        :param city_id: id города
        :param hotels_amount: количество отелей
        :param check_in: дата заезда
        :param check_out: дата выезда
        :param sort: метод сортировки отелей
        :param distance: Максимальная дистанция до центра
        :param max_price: Максимальная цена
        :return: Список строк таблицы Hotels или строка с текстом об ошибке
        """
        url = "https://hotels4.p.rapidapi.com/properties/list"
        print(check_in)
        querystring = {"destinationId": city_id,
                       "pageNumber": "1",
                       "pageSize": 25,
                       "checkIn": check_in,
                       "checkOut": check_out,
                       "adults1": "1",
                       "sortOrder": sort,
                       "locale": "ru_RU",
                       "currency": "RUB"
                       }
        if distance and max_price:
            querystring["priceMax"] = max_price
            querystring["landmarkIds"] = "Центр города"

        headers = {
            'x-rapidapi-host': "hotels4.p.rapidapi.com",
            'x-rapidapi-key': self.rapid_api_key
        }
        try:
            response = requests.request("GET", url,
                                        headers=headers,
                                        params=querystring,
                                        timeout=15
                                        )
            site_response = json.loads(response.text)

            print(response.status_code)

            if response.status_code != 200:
                return 'Ошибка ответа от сервера'

            # with open('hotels_info.json', 'w', encoding='utf-8') as file:
            #     json.dump(site_response, file, indent=4, ensure_ascii=False)
            if distance:
                hotels = self.__hotels_print(site_response,
                                             hotels_amount=hotels_amount,
                                             distance=distance,
                                             max_price=max_price
                                             )
            else:
                hotels = self.__hotels_print(site_response, hotels_amount=hotels_amount)
            return hotels

        except requests.exceptions.ReadTimeout as error:
            print(error, 'Время ожидания вышло')
            return 'Вышло время ожидания ответа от сервера, попробуйте снова'

    def get_photos(self, hotel_id: int, photos_count: int) -> str or List[str]:
        """
        :param hotel_id: id отеля
        :param photos_count: Количество фотографий
        :return: Список ссылок на фотографии отеля
        """
        url = "https://hotels4.p.rapidapi.com/properties/get-hotel-photos"

        querystring = {"id": hotel_id}

        headers = {
            'x-rapidapi-host': "hotels4.p.rapidapi.com",
            'x-rapidapi-key': self.rapid_api_key
        }

        try:
            response = requests.request("GET", url,
                                        headers=headers,
                                        params=querystring,
                                        timeout=15
                                        )
            print(response.status_code)
            if response.status_code != 200:
                return 'Ошибка ответа от сервера'
            response_json = json.loads(response.text)
            photos = self.__get_photo_url(response_json, photos_count)
            # with open('hotel_photos.json', 'w', encoding='utf-8') as file:
            #     json.dump(response_json, file, indent=4, ensure_ascii=False)
            return photos

        except requests.exceptions.ReadTimeout as error:
            print(error, 'Время ожидания вышло')
            return 'Вышло время ожидания ответа от сервера, попробуйте снова'

    @classmethod
    def __write_hotel_data(cls, dict_hotel: Dict) -> Hotel:
        """
        :param dict_hotel: Словарь из запроса отелей с одним отелем
        :return: Строка таблицы Hotel
        """
        hotel = Hotel.get_or_create(id=dict_hotel["id"])[0]
        hotel.name = dict_hotel.get("name", '--')
        hotel.address = dict_hotel.get("address", {}).get("locality", '--') + ', ' \
                        + dict_hotel.get("address", {}).get("streetAddress", '--')
        hotel.distance = dict_hotel.get("landmarks", [])[0].get("distance", '--')
        hotel.price = dict_hotel.get("ratePlan", {}).get("price", {}).get("current", '--')
        hotel.url = "https://ru.hotels.com/ho{}/".format(dict_hotel["id"])
        hotel.save()
        return hotel

    @classmethod
    def __hotels_print(cls,
                       site_results: Dict,
                       hotels_amount: int,
                       distance: Optional[float] = None,
                       max_price: Optional[float] = None) -> List[Hotel]:
        """
        :param site_results: Словарь из запроса отелей
        :param hotels_amount: Количество отелей
        :param distance: Максимальная дистанция до центра
        :param max_price: Максимальная цена
        :return: список строк таблицы Hotels
        """
        hotels_list = []
        if not distance:
            for dict_hotel in site_results["data"]["body"]["searchResults"]["results"]:
                hotels_list.append(cls.__write_hotel_data(dict_hotel))
                hotels_amount -= 1
                if hotels_amount == 0:
                    break

        else:
            for dict_hotel in site_results["data"]["body"]["searchResults"]["results"]:
                try:
                    hotel_distance = re.search(r'\b\d+[.,]\d+\b',
                                               dict_hotel.get(
                                                   "landmarks", [])[0].get(
                                                   "distance", '--')).group()
                    hotel_distance = re.sub(r',', '.', hotel_distance)
                    hotel_price = re.search(r'\b\d+[.,]\d+\b',
                                            dict_hotel.get(
                                                "ratePlan", {}).get(
                                                "price", {}).get(
                                                "current", '--')).group()
                    hotel_price = re.sub(r',', '', hotel_price)
                    if float(distance) >= float(hotel_distance) and \
                            float(max_price) >= float(hotel_price):
                        hotels_list.append(cls.__write_hotel_data(dict_hotel))
                        hotels_amount -= 1
                        if hotels_amount == 0:
                            break
                except Exception as e:
                    print(e, 'errors in json')

        return hotels_list

    @classmethod
    def __get_photo_url(cls, json_dict: Dict, count: int, size: str = 'y') -> List[str]:
        """
        :param json_dict: словарь из запроса фотографий
        :param count: количество фото
        :param size: размер фото
        :return: список ссылок на фотографии
        """
        photos_list = []
        for photo in json_dict["hotelImages"]:
            photos_list.append(re.sub(r'{size}', size, photo["baseUrl"]))
            count -= 1
            if count <= 0:
                break
        return photos_list
