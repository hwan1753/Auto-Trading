import win32com.client

# COM 객체를 불러오는 메서드 win32com.client.Dispatch
client = win32com.client.Dispatch("XA_Session.XASession") # XA_Session 객체를 사용.

# ConnectServer 메서드는 서버 주소와 포트를 매개변수로 전달.   True면 서버에 정상적 접속
print(client.ConnectServer("demo.ebestec.co.kr",20001))     # 모의투자 서버 주소는 demo.ebestec.co.kr  vhxmqjsghsms 20001