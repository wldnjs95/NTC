
# src/core/product_management.py
from src.utils.product_store import load_products, update_recent_product, delete_product, save_products

def get_product_list():
    return load_products().get('product_list', {})

def add_product(name, keyword):
    product_data = load_products()
    product_list = product_data.get('product_list', {})
    if name in product_list:
        return False, f"Product already exists: {name}"
    product_list[name] = {"product_name": name, "must_include": keyword}
    product_data["product_list"] = product_list
    save_products(product_data)
    return True, f"{name} has been added."

def remove_product(name):
    return delete_product(name)
