import json
import os
import sys

from yapi_codegen import YApi

# powershell 设置临时环境变量，或者直接配置到用户环境变量方便下次使用
# $env:YAPI_URL = "https://yapi.lioncash.co/"
# $env:YAPI_EMAIL = "your email"
# $env:YAPI_PASSWORD = "your password"

# 然后执行脚本: python yapi.py 405
# 405 是yapi的projectId或interfaceId
# 如果参数是projectId，会生成项目中所有代码。
# 如果参数是interfaceId，会生成对应interface的代码

if len(sys.argv) < 2:
    print(f'参数"projectId"缺失，例如："python {sys.argv[0]} 001"')
    sys.exit(1)

project_id = sys.argv[1]
yapi_host = os.getenv("YAPI_URL")
user_email = os.getenv("YAPI_EMAIL")
user_password = os.getenv("YAPI_PASSWORD")

if yapi_host is None:
    print("请配置YAPI_URL环境变量")
    sys.exit(1)
if user_email is None or user_password is None:
    print("请配置YAPI_EMAIL和YAPI_PASSWORD环境变量")
    sys.exit(1)

yapi = YApi(yapi_host)
yapi.login(user_email, user_password)
interface_list = yapi.get_interface_list(project_id)
interface = yapi.get_interface_detail(203507)
req_body_other = json.loads(interface["req_body_other"])