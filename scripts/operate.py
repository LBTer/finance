import httpx
import asyncio

async def operate():
    with httpx.AsyncClient() as client:
        # 用户登录
        response = await client.post("/auth/login", data={
            "username": "user@example.com",
            "password": "password123"
        })
        token = response.json()["access_token"]

        # 创建销售记录
        sales_record = await client.post(
            "/sales",
            json={
                "order_number": "ORD001",
                "product_name": "产品A",
                "quantity": 2,
                "unit_price": 99.99
            },
            headers={"Authorization": f"Bearer {token}"}
        )

        # 获取销售记录列表（带分页和搜索）
        records = await client.get(
            "/sales",
            params={"skip": 0, "limit": 10, "search": "产品A"},
            headers={"Authorization": f"Bearer {token}"}
        )

if __name__ == "__main__":
    asyncio.run(operate())