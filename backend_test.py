import requests
import sys
import json
from datetime import datetime

class EcommerceAPITester:
    def __init__(self, base_url="https://tier3-commerce.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_user_email = f"test_user_{datetime.now().strftime('%H%M%S')}@example.com"
        self.test_user_password = "TestPass123!"
        self.test_user_name = "Test User"

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, params=params)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    if isinstance(response_data, list):
                        print(f"   Response: List with {len(response_data)} items")
                    elif isinstance(response_data, dict):
                        print(f"   Response keys: {list(response_data.keys())}")
                except:
                    print(f"   Response: {response.text[:100]}...")
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text}")

            return success, response.json() if response.text else {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_products_endpoint(self):
        """Test products endpoint"""
        success, response = self.run_test(
            "Get All Products",
            "GET",
            "products",
            200
        )
        
        if success and isinstance(response, list):
            print(f"   Found {len(response)} products")
            if len(response) > 0:
                product = response[0]
                print(f"   Sample product: {product.get('name', 'Unknown')} - ${product.get('price', 0)}")
                return response[0].get('id')  # Return first product ID for cart testing
        return None

    def test_categories_endpoint(self):
        """Test categories endpoint"""
        success, response = self.run_test(
            "Get Categories",
            "GET",
            "categories",
            200
        )
        
        if success and isinstance(response, list):
            print(f"   Found {len(response)} categories")
            for category in response:
                print(f"   - {category.get('category', 'Unknown')}: {category.get('count', 0)} products")
        return success

    def test_product_search(self):
        """Test product search functionality"""
        success, response = self.run_test(
            "Search Products",
            "GET",
            "products",
            200,
            params={"search": "headphones"}
        )
        
        if success and isinstance(response, list):
            print(f"   Search results: {len(response)} products")
        return success

    def test_product_category_filter(self):
        """Test product category filtering"""
        success, response = self.run_test(
            "Filter Products by Category",
            "GET",
            "products",
            200,
            params={"category": "Electronics"}
        )
        
        if success and isinstance(response, list):
            print(f"   Electronics category: {len(response)} products")
        return success

    def test_user_registration(self):
        """Test user registration"""
        success, response = self.run_test(
            "User Registration",
            "POST",
            "auth/register",
            200,
            data={
                "email": self.test_user_email,
                "password": self.test_user_password,
                "full_name": self.test_user_name
            }
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            print(f"   Registration successful, token received")
            return True
        return False

    def test_user_profile(self):
        """Test getting user profile"""
        if not self.token:
            print("❌ No token available for profile test")
            return False
            
        success, response = self.run_test(
            "Get User Profile",
            "GET",
            "auth/me",
            200
        )
        
        if success and 'id' in response:
            self.user_id = response['id']
            print(f"   User profile: {response.get('full_name', 'Unknown')} ({response.get('email', 'Unknown')})")
            return True
        return False

    def test_user_login(self):
        """Test user login with existing credentials"""
        # Clear token first to test login
        self.token = None
        
        success, response = self.run_test(
            "User Login",
            "POST",
            "auth/login",
            200,
            data={
                "email": self.test_user_email,
                "password": self.test_user_password
            }
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            print(f"   Login successful, token received")
            return True
        return False

    def test_cart_operations(self, product_id):
        """Test cart CRUD operations"""
        if not self.token or not product_id:
            print("❌ No token or product ID available for cart tests")
            return False

        # Test adding to cart
        success, response = self.run_test(
            "Add Item to Cart",
            "POST",
            "cart",
            200,
            data={
                "product_id": product_id,
                "quantity": 2
            }
        )
        
        if not success:
            return False

        # Test getting cart
        success, cart_response = self.run_test(
            "Get Cart Items",
            "GET",
            "cart",
            200
        )
        
        if success and isinstance(cart_response, list) and len(cart_response) > 0:
            cart_item = cart_response[0]
            cart_item_id = cart_item.get('id')
            print(f"   Cart item: {cart_item.get('quantity', 0)}x {cart_item.get('product', {}).get('name', 'Unknown')}")
            
            # Test updating cart item
            success, response = self.run_test(
                "Update Cart Item",
                "PUT",
                f"cart/{cart_item_id}",
                200,
                params={"quantity": 3}
            )
            
            if success:
                # Test removing from cart
                success, response = self.run_test(
                    "Remove Cart Item",
                    "DELETE",
                    f"cart/{cart_item_id}",
                    200
                )
                return success
        
        return False

    def test_invalid_endpoints(self):
        """Test error handling for invalid requests"""
        # Test invalid product ID
        success, response = self.run_test(
            "Get Invalid Product",
            "GET",
            "products/invalid-id",
            404
        )
        
        # Test unauthorized cart access
        temp_token = self.token
        self.token = None
        success2, response2 = self.run_test(
            "Unauthorized Cart Access",
            "GET",
            "cart",
            401
        )
        self.token = temp_token
        
        return success and success2

def main():
    print("🚀 Starting E-commerce API Tests")
    print("=" * 50)
    
    tester = EcommerceAPITester()
    
    # Test public endpoints first
    print("\n📦 Testing Product Endpoints...")
    product_id = tester.test_products_endpoint()
    tester.test_categories_endpoint()
    tester.test_product_search()
    tester.test_product_category_filter()
    
    # Test authentication flow
    print("\n🔐 Testing Authentication...")
    if not tester.test_user_registration():
        print("❌ Registration failed, stopping tests")
        return 1
    
    if not tester.test_user_profile():
        print("❌ Profile fetch failed")
        return 1
    
    if not tester.test_user_login():
        print("❌ Login failed")
        return 1
    
    # Test cart operations (requires authentication)
    print("\n🛒 Testing Cart Operations...")
    if product_id:
        tester.test_cart_operations(product_id)
    else:
        print("❌ No product ID available for cart testing")
    
    # Test error handling
    print("\n⚠️ Testing Error Handling...")
    tester.test_invalid_endpoints()
    
    # Print final results
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {tester.tests_passed}/{tester.tests_run} tests passed")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed!")
        return 0
    else:
        print(f"❌ {tester.tests_run - tester.tests_passed} tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())