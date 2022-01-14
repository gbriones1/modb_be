import json
import os
import importlib
from copy import copy

from fastapi.testclient import TestClient

os.environ['ENVIRONMENT'] = 'testing'
os.remove('test.sqlite3')

from main.server import app
from main.settings import settings

class TestAPI():

    @classmethod
    def get_token(cls) -> str:
        if not hasattr(cls, "token"):
            with TestClient(app) as client:
                response = client.post("/token", data={
                    "username": settings.admin_username,
                    "password": settings.admin_password
                })
                assert response.status_code == 200
                cls.token = response.json().get("access_token")
        return cls.token

    @classmethod
    def fill_seed(cls, name: str) -> dict:
        result = {}
        seed = importlib.import_module(f'tests.data.{name}')
        with TestClient(app) as client:
            token = cls.get_token()
            for endpoint in seed.endpoints:
                result[endpoint] = []
                # print(endpoint)
                for data in getattr(seed, f"{endpoint}s", []):
                    # print(data)
                    response = client.post(f"/{endpoint}", json=data, headers={
                        "Authorization": f"Bearer {token}",
                    })
                    # print(response.text)
                    assert response.status_code == 200
                    result[endpoint].append(response.json())
        return result


class TestHome():

    def setup_method(self):
        pass

    def teardown_method(self):
        pass

    def test_healthcheck(self):
        with TestClient(app) as client:
            response = client.get("/")
            assert response.status_code == 200


class TestWorkBuy(TestAPI):

    @classmethod
    def setup_class(cls):
        cls.token = cls.get_token()
        cls.preloaded_data = cls.fill_seed("seed1")
        cls.workbuy1 = {
            "customer": cls.preloaded_data["customer"][0]["id"],
            "organization": cls.preloaded_data["organization"][0]["id"],
            "orders": [
                {
                    "provider": cls.preloaded_data["provider"][0]["id"],
                    "taxpayer": cls.preloaded_data["taxpayer"][0]["id"],
                    "claimant": cls.preloaded_data["employee"][0]["id"],
                    "order_unregisteredproducts": [
                        {
                            "code": "X01",
                            "description": "Desc1",
                            "amount": 3
                        }, {
                            "code": "X02",
                            "description": "Desc2",
                            "amount": 6
                        }
                    ]
                }
            ]
        }
        cls.workbuy2 = {
            "customer": cls.preloaded_data["customer"][1]["id"],
            "organization": cls.preloaded_data["organization"][1]["id"],
            "orders": [
                {
                    "provider": cls.preloaded_data["provider"][1]["id"],
                    "taxpayer": cls.preloaded_data["taxpayer"][1]["id"],
                    "claimant": cls.preloaded_data["employee"][1]["id"],
                    "order_unregisteredproducts": [
                        {
                            "code": "Y01",
                            "description": "Desc3",
                            "amount": 2,
                            "price": 50.5
                        }, {
                            "code": "Y02",
                            "description": "Desc4",
                            "amount": 5
                        }
                    ]
                }
            ]
        }

    @classmethod
    def teardown_class(cls):
        pass

    def test_workbuy_success(self):
        with TestClient(app) as client:
            print(self.workbuy1)
            response = client.post("/workbuy", json=self.workbuy1, headers={
                "Authorization": f"Bearer {self.token}",
            })
            print(response.text)
            assert response.status_code == 200
            result = response.json()
            workbuy1_id = result["id"]
            update_data = copy(self.workbuy2)
            update_data["orders"][0]["id"] = result["orders"][0]["id"]
            print(self.workbuy2)
            response = client.put(f"/workbuy/{workbuy1_id}", json=update_data, headers={
                "Authorization": f"Bearer {self.token}",
            })
            print(response.text)
            assert response.status_code == 200
            response = client.get(f"/workbuy/{workbuy1_id}", headers={
                "Authorization": f"Bearer {self.token}",
            })
            assert response.status_code == 200
            result = response.json()
            assert result["id"] == workbuy1_id
            assert result["orders"][0]["id"] == update_data["orders"][0]["id"]
            assert result["orders"][0]["order_unregisteredproducts"][0]["code"] == update_data["orders"][0]["order_unregisteredproducts"][0]["code"]
            assert result["orders"][0]["order_unregisteredproducts"][0]["description"] == update_data["orders"][0]["order_unregisteredproducts"][0]["description"]
            assert result["orders"][0]["order_unregisteredproducts"][0]["amount"] == update_data["orders"][0]["order_unregisteredproducts"][0]["amount"]
            assert result["orders"][0]["order_unregisteredproducts"][0]["price"] == update_data["orders"][0]["order_unregisteredproducts"][0]["price"]
            assert result["orders"][0]["order_unregisteredproducts"][1]["code"] == update_data["orders"][0]["order_unregisteredproducts"][1]["code"]
            assert result["orders"][0]["order_unregisteredproducts"][1]["description"] == update_data["orders"][0]["order_unregisteredproducts"][1]["description"]
            assert result["orders"][0]["order_unregisteredproducts"][1]["amount"] == update_data["orders"][0]["order_unregisteredproducts"][1]["amount"]
            assert result["orders"][0]["order_unregisteredproducts"][1]["price"] is None
            