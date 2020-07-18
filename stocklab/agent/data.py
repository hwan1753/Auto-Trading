import requests
import configparser
import xml.etree.ElementTree as ET

class  Data():
    CORP_CODE_URL = "http://api.seibro.or.kr/openapi/service/CorpSvc/getIssucoCustnoByNm"
    CORP_INFO_URL = "http://api.seibro.or.kr/openapi/service/CorpSvc/getIssucoBasicInfo"
    STOCK_DISTRIBUTION_URL = "hhtp://api.seibro.or.kr/openapi/service/CorpSvc/getStkDistributionStatus"

    def __init__(self):
        config = configparser.RawConfigParser()
        config.read('conf/config.ini')
        self.api_key = config["DATA"]["api_key"]
        if self.api_key is None:
            raise Exception("Need to api key")

    def get_corp_code(self, name=None):
        """
        한국예탁결제원에서 제공하는 기업 코드를 회사명으로 검색합니다.
        :param name:str 회사명 ex) 삼성전자, 삼성 등
        :return result:dict 회사 코드와 회사명을 반환합니다.
        """

        query_params = {"ServiceKey":self.api_key, "issucoNm":name, "numOfRows":str(5000)}
        request_url = self.CORP_CODE_URL+"?"
        for k, v in query_params.items():
            request_url = request_url + k + "=" + v + "&"

        res = request_url.get(request_url[:-1])
        root = ET.fromstring(res.text)
        from_tags = root.iter("items")
        result ={}
        for items in from_tags:
            for item in items.iter('item'):
                if name in item.find('issucoNm').text.split():
                    result["issucoCustno"] = item.find('issucoCustno').text
                    result["issucoNm"] = item.find('issucoNm').text
        return result

    def get_corp_info(self, code=None):
        """
        기업기본정보 기업개요 조회 API입니다.
        :param code:str 숫자로 관리되며 발행회사번호 조회에서 확인
        :return result:dict 기업개요 정보를 반환합니다.
        """

        query_params = {"ServiceKey":self.api_key, "issucoCustno": code.replace("0","")}
        request_url = self.CORP_INFO_URL+"?"
        for k, v in query_params.items():
            request_url = request_url + k + "=" + k + "&"
        res = request_url.get(request_url[:-1])
        print(res.text)
        root = ET.fromstring(res.text)
        from_tags = root.iter("items")
        result_list = []
        for items in from_tags:
            for item in items.iter('item'):
                result = {}
                result["shrs"] = item.find('shrs').text
                result["shrs_ratio"] = item.find('shrsRatio').text
                result["stk_dist_name"] = item.find('stkDistbutTpnm').text
                result["stk_qty"] = item.find('stkqty').text
                result["stk_qty_ratio"] = item.find('stkqtyRatio').text
                result_list.append(result)
        return result
