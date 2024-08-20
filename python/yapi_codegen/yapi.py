import requests
from .base import ApiBase


class YApi(ApiBase):
    def login(self, email: str, password: str) -> dict:
        url = "/api/user/login"
        payload = {"email": email, "password": password}
        return self.post(url, payload)

    def get_interface_list(self, project_id, page=1, limit=10) -> list[dict]:
        """
        [{
            "edit_uid": 0,
            "status": "done",
            "api_opened": false,
            "tag": [],
            "_id": 203480,
            "title": "检查手机号是否已经注册",
            "catid": 34148,
            "path": "/foochow",
            "project_id": 405,
            "method": "POST",
            "uid": 141,
            "add_time": 1724120995
        }],
        """
        url = f"/api/interface/list?page={page}&limit={limit}&project_id={project_id}"
        return self.get(url)["list"]
    
    def get_interface_detail(self, interface_id) -> dict:
        """
        {
            "query_path": {
                "path": "/mirage",
                "params": []
            },
            "edit_uid": 0,
            "status": "done",
            "type": "static",
            "req_body_is_json_schema": true,
            "res_body_is_json_schema": true,
            "api_opened": false,
            "index": 0,
            "tag": [],
            "_id": 203507,
            "req_body_type": "json",
            "res_body_type": "json",
            "req_body_other": "{\n  \"type\": \"object\",\n  \"required\": [\n    \"vitellus(o_mobile)\"\n  ],\n  \"title\": \"LoginReqVO\",\n  \"description\": \"LoginReqVO :LoginReqVO\",\n  \"properties\": {\n    \"vitellus(o_mobile)\": {\n      \"type\": \"string\",\n      \"description\": \"手机号\",\n      \"mock\": {\n        \"mock\": \"@string\"\n      }\n    },\n    \"password\": {\n      \"type\": \"string\",\n      \"description\": \"登录密码(密码登录时必填)\",\n      \"mock\": {\n        \"mock\": \"@string\"\n      }\n    },\n    \"ithun(o_token)\": {\n      \"type\": \"string\",\n      \"description\": \"ithun(o_token)(自动登录时用)\",\n      \"mock\": {\n        \"mock\": \"@string\"\n      }\n    },\n    \"metasome(o_userGid)\": {\n      \"type\": \"number\",\n      \"description\": \"metasome(o_userGid)(自动登录时用)\",\n      \"mock\": {\n        \"mock\": \"@Long\"\n      }\n    },\n    \"erect(o_mobileSn)\": {\n      \"type\": \"string\",\n      \"description\": \"登录设备号\",\n      \"mock\": {\n        \"mock\": \"@string\"\n      }\n    },\n    \"oscular(o_bizChannel)\": {\n      \"type\": \"string\",\n      \"description\": \"马甲渠道\",\n      \"mock\": {\n        \"mock\": \"@string\"\n      }\n    },\n    \"exhibit(o_bizLine)\": {\n      \"type\": \"string\",\n      \"description\": \"业务线\",\n      \"mock\": {\n        \"mock\": \"@string\"\n      }\n    },\n    \"oc\": {\n      \"type\": \"number\",\n      \"description\": \"是否需要otp校验\",\n      \"mock\": {\n        \"mock\": \"@Long\"\n      }\n    },\n    \"seiko(o_verCode)\": {\n      \"type\": \"string\",\n      \"description\": \"验证码(重置密码设置)\",\n      \"mock\": {\n        \"mock\": \"@string\"\n      }\n    },\n    \"restoral(o_verImageCode)\": {\n      \"type\": \"string\",\n      \"description\": \"图形验证码(重置密码设置)\",\n      \"mock\": {\n        \"mock\": \"@string\"\n      }\n    }\n  }\n}",
            "title": "登录",
            "catid": 34148,
            "path": "/mirage",
            "project_id": 405,
            "req_headers": [
                {
                    "required": "1",
                    "_id": "65b75eccc77dd52d41824c62",
                    "name": "Content-Type",
                    "value": "application/json"
                }
            ],
            "req_query": [],
            "res_body": "{\n  \"type\": \"object\",\n  \"required\": [\n    \"vitellus(o_mobile)\",\n    \"ithun(o_token)\",\n    \"name\",\n    \"metasome(o_userGid)\"\n  ],\n  \"title\": \"LoginRespVO\",\n  \"description\": \"LoginRespVO :LoginRespVO\",\n  \"properties\": {\n    \"vitellus(o_mobile)\": {\n      \"type\": \"string\",\n      \"description\": \"手机号\",\n      \"mock\": {\n        \"mock\": \"@string\"\n      }\n    },\n    \"ithun(o_token)\": {\n      \"type\": \"string\",\n      \"description\": \"ithun(o_token)\",\n      \"mock\": {\n        \"mock\": \"@string\"\n      }\n    },\n    \"name\": {\n      \"type\": \"string\",\n      \"description\": \"用户姓名\",\n      \"mock\": {\n        \"mock\": \"@string\"\n      }\n    },\n    \"metasome(o_userGid)\": {\n      \"type\": \"number\",\n      \"description\": \"用户Gid\",\n      \"mock\": {\n        \"mock\": \"@Long\"\n      }\n    },\n    \"underway(o_registerTime)\": {\n      \"type\": \"number\",\n      \"description\": \"注册时间\",\n      \"mock\": {\n        \"mock\": \"@Long\"\n      }\n    }\n  }\n}",
            "method": "POST",
            "req_body_form": [],
            "req_params": [],
            "desc": " <pre><code>  /**\n     * 登录\n     *\n     * @return {@link RegisterRespVO}\n     * @param: [RegisterReqVO]\n     */\n    @PostMapping(\"/login\")\n    @DecoderMethod\n    public LoginRespVO login(@RequestBody @Valid @DecodeArg LoginReqVO loginReqVO)</code></pre>",
            "uid": 141,
            "add_time": 1724120995,
            "up_time": 1724120995,
            "__v": 0,
            "username": "Jayme"
        }
        """
        url = f"/api/interface/get?id={interface_id}"
        return self.get(url)