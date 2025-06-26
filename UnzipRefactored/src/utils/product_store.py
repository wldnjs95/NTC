import os
import json
import src.config.config as config
from src.utils.logging_utils import log_user, log_debug, log_error

APPDATA_FILE = os.path.join(os.getenv('APPDATA'), 'NTC', 'UnzipRefactored', 'ntc_wedding_products.json')

def create_init_appdata():
    """Create the initial appdata directory and file if they do not exist."""
    os.makedirs(os.path.dirname(APPDATA_FILE), exist_ok=True)
    default_products = config.default_product_info
    save_products(default_products)
    log_debug(f"Created initial appdata file at {APPDATA_FILE} with default products.")
    log_debug("default_product_info: " + str(default_products))

def appdata_file_exists():
    """Check if the appdata file exists."""
    return os.path.exists(APPDATA_FILE)

def add_product(product_name, keyword):
    current_products= load_products()
    log_debug(f"Adding product: {product_name} with keyword: {keyword}")
    """Add a new product to the appdata file."""
    if not product_name or not keyword:
        log_user("Product name and keyword cannot be empty.")
        return (False, "Product name and keyword cannot be empty.")
    elif product_name in current_products['product_list']:
        log_user(f"Product {product_name} already exists. Delete it first if you want to replace it.")
        return (False, "Product already exists.")
    else:
        current_products['product_list'][product_name] = keyword
        save_products(current_products)
        log_debug(f"Product {product_name} added successfully.")
        return (True, "Product added successfully.")

def delete_product(product_name):
    current_products = load_products()
    log_debug(f"Deleting product: {product_name}")
    """Delete a product from the appdata file."""
    if product_name in current_products['product_list']:
        del current_products['product_list'][product_name]
        save_products(current_products)
        log_debug(f"Product {product_name} deleted successfully.")
        return (True, "Product deleted successfully.")
    else:
        log_error(f"Program should not reach here")
        log_error(f"Product {product_name} does not exist in the product list.")
        return (False, "Product does not exist.")
    log_user(f"Product {product_name} deleted successfully.")

def load_products():
    log_debug( "Loading products from appdata file." )
    """Load products from the appdata file."""
    if not appdata_file_exists():
        log_debug(f"Appdata file {APPDATA_FILE} does not exist. Creating initial appdata.")
        create_init_appdata()
    
    with open(APPDATA_FILE, 'r', encoding='utf-8') as file:
        try:
            products = json.load(file)
            return products
        except json.JSONDecodeError as e:
            log_debug(f"Error decoding JSON from {APPDATA_FILE}: {e}")
            print(f"Error decoding JSON from {APPDATA_FILE}: {e}")
            return {}
        except Exception as e:
            log_error(f"Unexpected error loading products: {e}")
            print(f"Unexpected error loading products: {e}")
            return {}

def save_products(data:dict):
    log_debug( "Saving products to appdata file." )
    with open(APPDATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    log_debug( "Finished saving products to appdata file." )

def update_recent_product(product_name):
    products = load_products()
    products["recent_product"] = product_name
    save_products(products)
    log_debug(f"Updated recent product to {product_name} in appdata file.")