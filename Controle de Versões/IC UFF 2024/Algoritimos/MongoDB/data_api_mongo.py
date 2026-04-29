import requests
import json

url = "https://sa-east-1.aws.data.mongodb-api.com/app/data-ijtvt/endpoint/data/v1/action/findOne"
key = "3kCu1JZw0j0YcBMwjp44CWLPLZXwdMY6N1ZXRsF337MaTDhqI37DK5PZ9nJuyqPu"

payload = json.dumps(
    {
        "collection": "relatorio_records",
        "database": "Relatorio_OS_DB",
        "dataSource": "Cluster",
        "projection": {"_id": 1},
    }
)
headers = {
    "Content-Type": "application/json",
    "Access-Control-Request-Headers": "*",
    "api-key": "3kCu1JZw0j0YcBMwjp44CWLPLZXwdMY6N1ZXRsF337MaTDhqI37DK5PZ9nJuyqPu",
}

response = requests.request("POST", url, headers=headers, data=payload)

print(response.text)
