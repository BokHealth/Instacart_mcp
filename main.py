from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel
from typing import List, Optional
import httpx
import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()
API_KEY_DEV = os.getenv("INSTACART_API_KEY_DEV")
API_KEY = os.getenv("INSTACART_API_KEY")
IS_PROD = os.getenv("IS_PROD", "").lower() == "true"

mcp = FastMCP("instacart-server")

# 定义数据模型
class LineItem(BaseModel):
    name: str
    quantity: Optional[float] = 1
    unit: Optional[str] = "each"
    display_text: Optional[str] = None

class ShoppingListRequest(BaseModel):
    title: str
    line_items: List[LineItem]
    image_url: Optional[str] = None
    instructions: Optional[List[str]] = None
    partner_linkback_url: Optional[str] = None

class Ingredient(BaseModel):
    name: str
    display_text: Optional[str] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None

class RecipeRequest(BaseModel):
    title: str
    ingredients: List[Ingredient]
    image_url: Optional[str] = None
    author: Optional[str] = None
    servings: Optional[int] = None
    cooking_time: Optional[int] = None
    instructions: Optional[List[str]] = None
    partner_linkback_url: Optional[str] = None
    enable_pantry_items: Optional[bool] = False

# 工具接口
@mcp.tool()
async def create_shopping_list(request: ShoppingListRequest) -> str:
    """
        Create a shopping list link that users can open on Instacart to view and purchase items.

        Parameters:
        - title: The title of the shopping list, e.g., "Weekend BBQ Supplies"
        - line_items: A list of items to include in the shopping list, each with name, quantity, and unit (default is "each")
        - 
        - image_url: (Optional) A URL to an image representing the list
        - instructions: (Optional) Additional notes or instructions related to the list
        - partner_linkback_url: (Optional) A URL to redirect users back to your platform after using the Instacart link

        Returns:
        - A URL to the Instacart shopping list that users can click to view and order the items
    """

    data = {
        **request.dict(exclude_none=True),
        "link_type": "shopping_list"
    }
    return await _call_instacart_api(
        endpoint="products/products_link",
        data=data
    )

@mcp.tool()
async def create_recipe(request: RecipeRequest) -> str:
    """
        Create a recipe link with ingredients, instructions, and an image. The link allows users to add all items to their Instacart cart.

        Parameters:
        - title: The recipe title, e.g., "Classic Spaghetti Bolognese"
        - ingredients: A list of ingredients, including name, optional quantity and unit
        - image_url: (Optional) A URL to an image representing the recipe
        - author: (Optional) The name of the recipe author or source
        - servings: (Optional) The number of servings (e.g., 4 for a four-person meal)
        - cooking_time: (Optional) Estimated cooking time in minutes
        - instructions: (Optional) A step-by-step list of how to prepare the recipe
        - partner_linkback_url: (Optional) A URL to redirect users back to your platform
        - enable_pantry_items: (Optional) Whether to include common pantry items automatically (default is False)

        Returns:
        - A URL to the recipe on Instacart, with an option to add all ingredients to cart
    """
    return await _call_instacart_api(
        endpoint="products/recipe",
        data=request.dict(exclude_none=True)
    )


# 统一API调用
async def _call_instacart_api(endpoint: str, data: dict) -> str:
    async with httpx.AsyncClient() as client:
        if IS_PROD:
            response = await client.post(
                f"https://connect.instacart.com/idp/v1/{endpoint}",
                json=data,
                headers={"Authorization": f"Bearer {API_KEY}"},
                timeout=30.0
            )
        else:
            response = await client.post(
                f"https://connect.dev.instacart.tools/idp/v1/{endpoint}",
                json=data,
                headers={"Authorization": f"Bearer {API_KEY_DEV}"},
                timeout=30.0
            )
        response.raise_for_status()
        return response.json()["products_link_url"]
        

if __name__ == "__main__":
    mcp.run("sse")