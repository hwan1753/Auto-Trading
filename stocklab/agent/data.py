import requests
import configparser
import xml.etree.ElementTree as ET

class  Data():

    CORP_CODE_URL = "http://api.seibro.or.kr/openapi/service/CorpSvc/getIssucoCustnoByNm"
    CORP_INFO_URL = "http://api.seibro.or.kr/openapi/service/CorpSvc/getIssucoBasicInfo"
    STOCK_DISTRIBUTION_URL = "http://api.seibro.or.kr/openapi/service/CorpSvc/getStkDistributionShareholderStatus"

    def __init__(self):
        # ConfigParser()는 특수문자를 읽지 못하므로 여기서는 RawConfigParser()를 사용
        config = configparser.RawConfigParser()
        config.read('C:/Users/john1/Desktop/공부/git/Auto Trading/Auto-Trading/confi/config.ini')
        self.api_key = config["DATA"]["api_key"]
        if self.api_key is None:
            raise Exception("Need to api key")


    def get_corp_code(self, name = None):
        """
        한국예탁결제원에서 제공하는 기업 코드를 회사명으로 검색합니다.
        :param name:str 회사명 ex) 삼성전자, 삼성 등
        :return result:dict 회사 코드와 회사명을 반환합니다.
        """

        # 상세기능을 호출할 때 전달할 매개변수를 정의, 회사명, 돌려받을 결과값이 여러 개일 때 몇개 받을지(numOfRows)
        query_params = {"ServiceKey":self.api_key, "issucoNm":name, "numOfRows":str(5000)}

        # serviceKey값에 인코딩된 값이 있어서 그대로 호출하면 안됨.
        # 그래서 정의한 URL과 query_params를 이용하여 실제 요청할 request_url을 직접 만들어 전달
        request_url = self.CORP_CODE_URL+"?"
        for k, v in query_params.items():
            request_url = request_url + k + "=" + v + "&"
        print(request_url)


        # [:-1]은 마지막 &값 제외. res는 반환값을 저장
        res = requests.get(request_url[:-1])
        
        # res.text 반환된 값의 본문. ET.fromstring 모듈로 XML 파싱
        root = ET.fromstring(res.text)
        # XML에서 items에 있는 item 노드 값을 찾음.
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
            request_url = request_url + k + "=" + v + "&"
            print(k,v)
        res = requests.get(request_url[:-1])
        print(request_url)
        root = ET.fromstring(res.text)
        from_tags = root.iter("item")
        result = {}
        # 결과가 항상 하나 이므로 items를 안하고 item 노드만 파싱.
        for item in from_tags:
            result["apliDt"] = item.find('apliDt').text
            result["bizno"] = item.find('bizno').text
            result["ceoNm"] = item.find('ceoNm').text
            result["engCustNm"] = item.find('engCustNm').text
            result["foundDt"] = item.find('founDt').text
            result["homepAddr"] = item.find('homepAddr').text
            result["pval"] = item.find('pval').text
            result["totalStkcnt"] = item.find('totalStkCnt').text
        return result




    def get_stk_distribution_info(self, code=None, date=None):
        """
        주식분포내역 주주별현황 조회 API입니다.
        :param code:str 숫자로 관리되며 발행회사번호 조회에서 확인
        :param data:str 기준일 8자리로 YYYYMMDD 형식으로 입력합니다. ex) 20181231
        :return result_list:list 주주별 주식보유 현황 정보를 반환합니다.
        """

        query_params = {"ServiceKey":self.api_key, "issucoCustno":code.replace("0",""),"rgtStdDt":date}

        request_url = self.STOCK_DISTRIBUTION_URL+"?"
        for k, v in query_params.items():
            request_url = request_url + k + "=" + v + "&"
        res = requests.get(request_url[:-1])

        print(request_url)
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
        return result_list
