import configparser
import win32com.client
import pythoncom
from datetime import datetime
import time

class XASession:
    # 로그인 상태를 확인하기 위한 클래스 변수
    login_state = 0

    def OnLogin(self, code, msg):
        """
        로그인 시도 후 호출되는 이벤트
        code가 0000이면 로그인 성공
        """
        if code == "0000":
            print(code, msg)
            XASession.login_state = 1
        else:
            print(code, msg)


    def OnDisconnect(self):
        """
        서버와 연결이 끊어지면 발생하는 이벤트.
        """
        print("Session disconnected")
        XASession.login_state = 0


class EBest:

    # xing API TR호출 제약조건
    QUERY_LIMIT_10MIN = 200
    LIMIT_SECONDS = 600 # 10min

    def __init__(self, mode=None):
        """
        config.ini 파일을 로드해 사용자, 서버 정보 저장
        지금 유효기간 3개월 모의투자(갱신해야함)
        query_cnt는 10분당 200개의 TR 수행을 관리하기 위한 리스트
        TR은 xingAPI로 서버에서 받는 데이터
        xa_session_client는 XASession 객체
        :param mode:str - 모의서버는 DEMO 실서버는 PROD로 구분
        """

        if mode not in ["PROD", "DEMO"]:
            raise Exception("Need to run_mode(PROD or DEMO)")

        run_mode = "EBEST_"+mode
        config = configparser.ConfigParser()
        config.read('C:/Users/john1/Desktop/공부/git/Auto Trading/Auto-Trading/confi/config.ini')
        self.user = config[run_mode]['user']
        self.passwd = config[run_mode]['password']
        self.cert_passwd = config[run_mode]['cert_passwd']
        self.host = config[run_mode]['host']
        self.port = config[run_mode]['port']
        self.account = config[run_mode]['account']

        self.xa_session_client = win32com.client.DispatchWithEvents("XA_Session.XASession",XASession)

        # 현재 리스트 갯수
        self.query_cnt = []



    def login(self):
        self.xa_session_client.ConnectServer(self.host, self.port)
        self.xa_session_client.Login(self.user, self.passwd, self.cert_passwd, 0, 0)
        while XASession.login_state == 0:
            pythoncom.PumpWaitingMessages()

    def logout(self):
        #result = self.xa_session_client.Logout()
        #if result:
        XASession.login_state =0
        self.xa_session_client.DisconnectServer()

    def _excute_query(self, res, in_block_name, out_block_name, *out_fields, **set_fields):
        """
        TR 코드를 실행하기 위한 메서드
        :param res:str 리소스 이름(TR)
        :param in_block_name:str 인 블록 이름
        :param out_block_name:str 아웃 블록 이름
        :param out_params:list 출력 필드 리스트
        :param in_farams:dict 인 블록에 설정할 필드 딕셔너리
        :return result:list 결과를 list에 담아 반환
        """

        time.sleep(1)
        print("current query cnt:", len(self.query_cnt))
        print(res, in_block_name, out_block_name)

        # query_cnt(리스트 갯수)가 QUERY_LIMIT_10MIN(200개)를 넘으면 1초간 프로세스 정지
        while len(self.query_cnt) >= EBest.QUERY_LIMIT_10MIN:
            time.sleep(1)
            print("waiting for execute query... current query cht:", len(self.query_cnt))

            # 1초가 지나면 query_cnt 리스트의 각 값과 현재 시각의 차이를 계산한 다음 filter를 이요해 LLIMIT_SECONDS(600개)를 넘지않는 요소들만 리스트에 담음.
            self.query_cnt = list(filter(lambda x: (datetime.today() - x).total_seconds() < EBest.LIMIT_SECONDS, self.query_cnt))

        xa_query = win32com.client.DispatchWithEvents("XA_DataSet.XAQuery", XAQuery)
        # 리소스 파일을 불러옴
        xa_query.LoadFromResFile(XAQuery.RES_PATH + res + ".res")
        # in_block_name 설정
        for key, value in set_fields.items():
            xa_query.SetFieldData(in_block_name, key, 0, value)

        # TR을 요청
        errorCode = xa_query.Request(0)

        # 요청 후 대기  OnReceiveData 메소드 실행 -> tr_run_state 값 1로 변경
        waiting_cnt = 0
        while xa_query.tr_run_state == 0:
            waiting_cnt += 1
            # Waiting 계속 출력하면 느려지므로 100,000번에 한번씩 출력
            if waiting_cnt % 100000 == 0:
                print("Waiting....", self.xa_session_client.GetLastError())
            pythoncom.PumpWaitingMessages()

        # 결과 블록
        result = []
        # 결과가 몇 개인지 확인 GetBlockCount : 블록이 Occurs라면 Occurs의 개수
        count = xa_query.GetBlockCount(out_block_name)

        for i in range(count):
            item = {}
            for field in out_fields:
                # GetFieldData( TR의 블록명, 블록의 필드명, 블록의 Occurs Index)
                value = xa_query.GetFieldData(out_block_name, field, i)
                item[value] = value
            result.append(item)

        # 제약시간 체크 + query_cnt에 현재시각 추가
        XAQuery.tr_run_state = 0
        self.query_cnt.append(datetime.today())

        # 영문 필드명을 한글 필드명으로 변환
        for item in result:
            for field in list(item.keys()):
                if getattr(Field, res, None):
                    res_field = getattr(Field, res, None)
                    if out_block_name in res_field:
                        field_hname = res_field[out_block_name]
                        if field in field_hname:
                            item[field_hname[field]] = item[field]
                            item.pop(field)

        return result

    def get_code_list(self,market=None):
        """
        TR: t8436 코스피, 코스닥의 종목 리스트를 가져온다
        :param market:str 전체(0), 코스피(1), 코스닥(2)
        :return result:list 시장별 종목 리스트
        """

        if market != "ALL" and market != "KOSPI" and market != "KOSDAQ":
            raise Exception("Need to market param(ALL, KOSPI, KOSDAQ)")

        market_code = {"ALL": "0", "KOSPI": "1", "KOSDAQ": "2"}
        in_params = {"gubun":market_code[market]}
        out_params =['hname', 'shcode', 'expcode', 'etfgubun', 'memedan', 'gubun', 'spac_gubun']
        result = self._excute_query("t8436","t8436InBlock","t8436OutBlock",*out_params,**in_params)
        return result

    def get_stock_price_by_code(self,code=None,cnt="1"):
        """
        TR: t1305 현재 날짜를 기준으로 cnt 만큼 전일의 데이터를 가져온다
        :param code:str 종목코드
        :param cnt:str 이전 데이터 조회 범위(일단위)
        :return result:list 종목의 최근 가격 정보
        """

        in_params = {"shcode":code, "dwmcode":"1","date":"","idx":"","cnt":cnt}
        out_params = ['date', 'open', 'high', 'low', 'close', 'sign', 'change', 'diff',
                      'vloume', 'diff_vol', 'chdegree', 'value', 'ppvolume', 'o_sign', 'o_change', 'o_diff',
                      'h_sign', 'h_change', 'h_diff', 'l_sign', 'l_change', 'l_diff', 'marketcap']

        result = self._excute_query("t1305","t1305InBlock", "t1305OutBlock1",*out_params, **in_params)
        for item in result:
            item["code"] = code
        return result

    def get_credit_trend_by_code(self,code=None,date=None):
        """
        TR: t1921 신용거래 동향
        :param code:str 종목코드
        :param date:str 날짜 ex)20200713
        """

        in_params = {"gubun":"0","shcode":code, "date":date, "idx":"0"}
        out_params = ["mmdate","close","sign", "jchange", "diff", "nvolume",
                      "svolume", "jvolume", "price", "change", "gyrate", "jkrate", "shcode"]

        result = self._excute_query("t1921","t1921InBlock","t1921OutBlock1",*out_params,**in_params)

        for item in result:
            item["code"] = code
        return result

    def get_agent_trend_by_code(self, code=None, fromdt=None, todt=None):
        """
        TR: t1717 외인 기관별 종목별 동향
        :param code:str 종목코드
        :param fromdt:str 조회 시작 날짜
        :param todt:str 조회 종료 날짜
        :return result:list 시장별 종목 리스트
        """
        in_params = {"gubun":"0", "fromdt":fromdt, "todt":todt, "shcode":code}
        out_params = ["date", "close", "sign", "change", "diff", "volume", "tjj0000_vol",
                      "tjj0001_vol","tjj0002_vol","tjj0003_vol","tjj0004_vol", "tjj0005_vol", "tjj0006_vol",
                      "tjj0007_vol","tjj0008_vol","tjj0009_vol","tjj0010_vol","tjj0011_vol","tjj0018_vol",
                      "tjj0016_vol","tjj0017_vol","tjj0001_dan","tjj0002_dan","tjj0003_dan","tjj0004_dan",
                      "tjj0005_dan","tjj0006_dan","tjj0007_dan","tjj0008_dan","tjj0009_dan","tjj0010_dan",
                      "tjj0011_dan","tjj0018_dan","tjj0016_dan","tjj0017"]
        result = self._excute_query("t1717","t1717InBlock","t1717OutBlock",*out_params,**in_params)

        for item in result:
            item["code"]=code
        return result

    def get_short_trend_by_code(self, code=None, sdate=None, edate=None):
        """
        TR: t1927 공매도일별추이
        :param code:str 종목코드
        :param sdate:str 시작일짜
        :param edate:str 종료날짜
        :return result:list 시장 별 종목 리스트
        """
        in_params = {"date":sdate, "sdate":sdate,"edate":edate,"shcode":code}
        out_params = ["date", "price", "sign", "change", "diff", "volume", "value",
                      "gm_vo", "gm_va", "gm_per", "gm_avg", "gm_vo_sum"]

        result = self._excute_query("t1927", "t1927InBlock", "t1927OutBlock1", *out_params, **in_params)

        for item in result:
            item["code"] = code
        return result

class Field:
    t1101 = {
        "t11010utBlock":{
            "hname":"한글명",
            "price":"현재가",
            "sign":"전일대비구분",
            "change":"전일대비",
            "diff":"등락율",
            "volume":"누적거래량",
            "jnilclose": "전일종가",
            "offerho1": "매도호가1",
            "bidho1":"매수호가1",
            "offerrem1": "매도호가수량1",
            "bidrem1":"매수호가수량1",
            "preoffercha1":"직전매도대비수량1",
            "prebidcha1":"직전매수대비수량1",
            "offerho2": "매도호가2",
            "bidho2":"매수호가2",
            "offerrem2": "매도호가수량2",
            "bidrem2":"매수호가수량2",
            "preoffercha2":"직전매도대비수량2",
            "prebidcha2":"직전매수대비수량2",
            "offerho2": "매도호가3",
            "bidho3":"매수호가3",
            "offerrem3": "매도호가수량3",
            "bidrem3":"매수호가수량3",
            "preoffercha3":"직전매도대비수량3",
            "prebidcha3":"직전매수대비수량3",
            "offerho4": "매도호가4",
            "bidho4":"매수호가4",
            "offerrem4": "매도호가수량4",
            "bidrem4":"매수호가수량4",
            "preoffercha4":"직전매도대비수량4",
            "prebidcha4":"직전매수대비수량4",
            "offerho5": "매도호가5",
            "bidho5":"매수호가5",
            "offerrem5": "매도호가수량5",
            "bidrem5":"매수호가수량5",
            "preoffercha5":"직전매도대비수량5",
            "prebidcha5":"직전매수대비수량5",
            "offerho6": "매도호가6",
            "bidho6":"매수호가6",
            "offerrem6": "매도호가수량6",
            "bidrem6":"매수호가수량6",
            "preoffercha6":"직전매도대비수량6",
            "prebidcha6":"직전매수대비수량6",
            "offerho7": "매도호가7",
            "bidho7": "매수호가7",
            "offerrem7": "매도호가수량7",
            "bidrem7": "매수호가수량7",
            "preoffercha7": "직전매도대비수량7",
            "prebidcha7": "직전매수대비수량7",
            "offerho8": "매도호가8",
            "bidho8":"매수호가8",
            "offerrem8": "매도호가수량8",
            "bidrem8":"매수호가수량8",
            "preoffercha8":"직전매도대비수량8",
            "prebidcha8":"직전매수대비수량8",
            "offerho9": "매도호가9",
            "bidho9":"매수호가9",
            "offerrem9": "매도호가수량9",
            "bidrem9":"매수호가수량9",
            "preoffercha9":"직전매도대비수량9",
            "prebidcha9":"직전매수대비수량9",
            "offerho10": "매도호가10",
            "bidho10":"매수호가10",
            "offerrem10": "매도호가수량10",
            "bidrem10":"매수호가수량10",
            "preoffercha10":"직전매도대비수량10",
            "prebidcha10":"직전매수대비수량10",
            "offer":"매도호가수량합",
            "bid": "매수호가수량합",
            "preoffercha":"직전매도대비수량합",
            "prebidcha":"직전매수대비수량합",
            "hotime":"수신시간",
            "yeprice":"예상체결가격",
            "yevolume":"예상체결수량",
            "yesign":"예상체결전일구분",
            "yechange":"예상체결전일대비",
            "yediff":"예상체결등락율",
            "tmoffer":"시간외매도잔량",
            "tmbid":"시간외매수잔량",
            "ho_status":"동시구분",
            "shcode":"단축코드",
            "uplmtprice":"상한가",
            "dnlmtprice":"하한가",
            "open":"시가",
            "high":"고가",
            "low":"저가"
        }
    }

    t8436 = {
        "t8436OutBlock":{
            "hname":"종목명",
            "shcode":"단축코드",
            "expcode":"확장코드",
            "etfgubun":"ETF구분(1: ETF2:ETN)",
            "uplmtprice":"상한가",
            "dnlmtprice":"하한가",
            "jnilclose":"전일가",
            "memedan":"주문수량단위",
            "recprice":"기준가",
            "gubun":"구분(1: 코스피2:코스닥)",
            "bu12gubun":"증권그룹",
            "spac_gubun":"기업인수목적회사여부(Y / N)",
            "filler":"filler(미사용)"
        }
    }

    t1305 = {
        "t1305OutBlock":{
            "date":"날짜",
            "open":"시가",
            "high":"고가",
            "low":"저가",
            "close":"종가",
            "sign":"전일대비구분",
            "change":"전일대비",
            "diff":"등락율",
            "volume":"누저거래량",
            "diff_vol":"거래증가율",
            "chdegree":"체결강도",
            "sojinrate":"소진율",
            "changerate":"회전율",
            "fpvolume":"외인순매수",
            "covolume":"기관순매수",
            "shcode":"종목코드",
            "value":"누적거래대금(단위:백만)",
            "ppvolume":"개인순매수",
            "o_sign":"시가대비구분",
            "o_chagne":"시가대비",
            "o_diff":"시가기준등락율",
            "h_sign":"고가대비구분",
            "h_change":"고가대비",
            "h_diff":"고가기준등락율",
            "l_sign":"저가대비구분",
            "l_change":"저가대비",
            "l_diff":"저가기준등락율",
            "marketcap":"시가총액(단위:백만)"
        }
    }

    t1921 = {
        "t1921OutBlock":{
            "mmdate": "날짜",
            "close":"종가",
            "sign":"전일대비구분",
            "jchange":"전일대비",
            "diff":"등락율",
            "nvolume":"신규",
            "svolume":"상환",
            "jvolume":"잔고",
            "price":"금액",
            "chagne":"대비",
            "gyrate":"공여율",
            "jkrate":"잔고율",
            "shcode":"종목코드"
        }
    }

    t1717 = {
        "t1717OutBlock":{
            "date":"일자",
            "close": "종가",
            "sign": "전일대비구분",
            "change": "전일대비",
            "diff": "등락율",
            "volume":"누적거래량",
            "tjj000_vol":"사모펀드(순매수량)",
            "tjj0001_vol":"증권(순매수량)",
            "tjj0002_vol":"보험(순매수량)",
            "tjj0003_vol":"투신(순매수량)",
            "tjj0004_vol":"은행(순매수량)",
            "tjj0005_vol":"종금(순매수량)",
            "tjj0006_vol":"기금(순매수량)",
            "tjj0007_vol":"기타법인(순매수량)",
            "tjj0008_vol":"개인(순매수량)",
            "tjj0009_vol":"등록외국인(순매수량)",
            "tjj0010_vol":"미등록외국인(순매수량)",
            "tjj0011_vol":"국가외(순매수량)",
            "tjj0018_vol":"기관(순매수량)",
            "tjj0016_vol":"외인계(순매수량)(등록+미등록)",
            "tjj0017_vol":"기타계(순매수량)(기타+국가)",
            "tjj0000_dan":"사모펀드(단가)",
            "tjj0001_dan":"증권(단가)",
            "tjj0002_dan": "보험(단가)",
            "tjj0003_dan": "투신(단가)",
            "tjj0004_dan": "은행(단가)",
            "tjj0005_dan": "종금(단가)",
            "tjj0006_dan": "기금(단가)",
            "tjj0007_dan": "기타법인(단가)",
            "tjj0008_dan": "개인(단가)",
            "tjj0009_dan": "등록외국인(단가)",
            "tjj00010_dan": "미등록외국인(단가)",
            "tjj00011_dan": "국가외(단가)",
            "tjj00018_dan": "기관(단가)",
            "tjj00016_dan": "외인계(단가)(등록+미등록)",
            "tjj00017_dan": "기타계(단가)(기타+국가)",
        }
    }

    t1927 = {
        "t1927OutBlock":{
            "date":"일자",
            "price":"현재가",
            "sign":"전일대비구분",
            "change":"전일대비",
            "diff":"등락율",
            "volume":"거래량",
            "value":"거래대금",
            "gm_vo":"공매도수량",
            "gm_va":"공매도대금",
            "gm_per":"공매도거래비중",
            "gm_avg":"평균공매도단가",
            "gm_vo_sum":"누적공매도수량"
        }
    }





class XAQuery:
    # xingAPI에서 TR을 내려받은 폴더
    RES_PATH = "C:/eBEST/xingAPI/Res/"
    # OnReceiveData에서 Data를 받으면 1로 바뀜
    tr_run_state = 0

    # 데이터가 수신되면 tr_run_state를 1로 설정
    def OnReceiveData(self, code):
        print("OnReceiveData", code)
        XAQuery.tr_run_state = 1

    # 요청한 API에 대해 메시지를 수신했을 때 발생하는 이벤트
    def OnReceiveMessage(self, error, code, message):
        print("OnreceiveMessage", error, code, message)


