from pymongo import MongoClient
from pymongo.cursor import CursorType
import configparser

class MongoDBHandler:

    def __init__(self):
        """
        MongoDBHandler __init__
        config.ini 파일에서 MongoDB 접속 정보를 로딩한다.
        접속 정보를 이용해 MongoDB 접속에 사용할 _client를 생성.
        """
        config = configparser.ConfigParser()
        config.read('C:/Users/john1/Desktop/공부/git/Auto Trading/Auto-Trading/confi/config.ini')
        host = config['MONGODB']['host']
        port = config['MONGODB']['port']

        self._client = MongoClient(host,int(port))

    def insert_item(self, data, db_name=None, collection_name=None):
        """
        MongoDB에 하나의 문서(document)를 입력하기 위한 메서드입니다.
        :param datas:dict: 문서를 받습니다.
        :param db_name:str: MongoDB에서 데이터베이스에 해당하는 이름을 받습니다.
        :param collection_name:str: 데이터베이스에 속하는 컬렉션 이름을 받습니다.
        :return inserted_id:str: 입력 완료된 문서의 ObjectId를 반환합니다.
        :raises Exception:매개변수 db_name과 collection_name이 없으면 예외(Exception)를 발생시킵니다.
        """
        if not isinstance(data, dict):
            raise Exception("data type should be dict")
        if db_name is None or collection_name is None:
            raise Exception("Need to param db_name, collection_name")
        return self._client[db_name][collection_name].insert_one(data).inserted_id

    def insert_items(self,datas, db_name=None, collection_name=None):
        """
        MongoDB에 여러 개의 문서(document)를 입력하기 위한 메서드입니다.
        :param datas:list: 문서의 리스트를 받습니다.
        :param db_name:str: MongoDB에서 데이터베이스에 해당하는 이름을 받습니다.
        :param collection_name:str: 데이터베이스에 속하는 컬렉션 이름을 받습니다.
        :return inserted_ids: 입력 완료된 문서의 Object Id list를 반환합니다.
        :raises Exception: 매개변수 db_name과 collection_name이 없으면 예외(Exception)를 발생시킵니다.
        """
        if not isinstance(datas,list):
            raise Exception("datas type should be list")
        if db_name is None or collection_name is None:
            raise Exception("Need to param db_name, collection_name")
        return self._client[db_name][collection_name].insert_many(datas).inserted_ids

    def find_items(self, condition=None, db_name=None, collection_name=None):
        """
        MongoDB에 하나의 문서(document)를 검색하기 위한 메서드입니다.
        :param condition:dict: 검색 조건을 딕셔너리 형태로 받습니다.
        :param db_name:str MongoDB에서 데이터베이스에 해당하는 이름을 받습니다.
        :param collection_name:str: 데이터베이스에 속하는 컬렉션 이름을 받습니다.
        :return document:dict: 검색된 문서가 있으면 문서의 내용을 반환합니다.
        :raises Exception: 매개변수 db_name과 collection_name이 없으면 예외(Exception)를 발생시킵니다.
        """
        if condition is None or not isinstance(condition, dict):
            condition = {}
        if db_name is None or collection_name is None:
            raise Exception("Need to param db_name, collection_name")
        return self._client[db_name][collection_name].find_one(condition)


    def find_item(self, condition=None, db_name=None, collection_name=None):
        """
        MongoDB에 여러 개의 문서(document)를 검색하기 위한 메서드입니다.
        :param condition:dict: 검색 조건을 딕셔너리 형태로 받습니다.
        :param db_name:str: MongoDB에서 데이터베이스에 해당하는 이름을 받습니다.
        :param collection_name:str: 데이터베이스에 속하는 컬렉션 이름을 받습니다.
        :return Cursor: 커서를 반환합니다.
        :raises Exception: 매개변수 db_name과 collection_name이 없으면 예외(Exception)를 발생시킵니다.
        """
        if condition is None or not isinstance(condition,dict):
            condition = {}
        if db_name is None or collection_name is None:
            raise Exception("Need to param db_name, collection_name")
        return self._client[db_name][collection_name].find(condition, no_cursor_timeout=True,cursor_type=CursorType.EXHAUST)

    def delete_items(self, condition=None, db_name=None, collection_name=None):

    def update_items(self, condition=None, update_value=None, db_name=None, collection_name=None):

    def update_item(self, condition=None, update_value=None, db_name=None, collection_name=None):

    def aggregate(self,pipeline=None, db_name=None, collection_name=None):

    def text_search(self, text=None, db_name=None, collection_name=None):