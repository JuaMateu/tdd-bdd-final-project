# Copyright 2016, 2023 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Test cases for Product Model

Test cases can be run with:
    nosetests
    coverage report -m

While debugging just these tests it's convenient to use this:
    nosetests --stop tests/test_models.py:TestProductModel

"""
import os
import logging
import unittest
from decimal import Decimal
from service.models import Product, Category, db, DataValidationError
from service import app
from tests.factories import ProductFactory

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)


######################################################################
#  P R O D U C T   M O D E L   T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestProductModel(unittest.TestCase):
    """Test Cases for Product Model"""

    @classmethod
    def setUpClass(cls):
        """This runs once before the entire test suite"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        Product.init_db(app)

    @classmethod
    def tearDownClass(cls):
        """This runs once after the entire test suite"""
        db.session.close()

    def setUp(self):
        """This runs before each test"""
        db.session.query(Product).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    ######################################################################
    #  T E S T   C A S E S
    ######################################################################

    def test_create_a_product(self):
        """It should Create a product and assert that it exists"""
        product = Product(
            name="Fedora",
            description="A red hat",
            price=12.50,
            available=True,
            category=Category.CLOTHS,
        )
        self.assertEqual(str(product), "<Product Fedora id=[None]>")
        self.assertTrue(product is not None)
        self.assertEqual(product.id, None)
        self.assertEqual(product.name, "Fedora")
        self.assertEqual(product.description, "A red hat")
        self.assertEqual(product.available, True)
        self.assertEqual(product.price, 12.50)
        self.assertEqual(product.category, Category.CLOTHS)

    def test_add_a_product(self):
        """It should Create a product and add it to the database"""
        products = Product.all()
        self.assertEqual(products, [])
        product = ProductFactory()
        product.id = None
        product.create()
        # Assert that it was assigned an id and shows up in the database
        self.assertIsNotNone(product.id)
        products = Product.all()
        self.assertEqual(len(products), 1)
        # Check that it matches the original product
        new_product = products[0]
        self.assertEqual(new_product.name, product.name)
        self.assertEqual(new_product.description, product.description)
        self.assertEqual(Decimal(new_product.price), product.price)
        self.assertEqual(new_product.available, product.available)
        self.assertEqual(new_product.category, product.category)

    #
    # ADD YOUR TEST CASES HERE
    #
    def test_read_a_product(self):
        """It should Read a product"""
        product = ProductFactory()
        # Set the ID of the product object to None and then call the create() method on the product.
        product.id = None
        product.create()
        # Assert that the ID of the product object is not None after calling the create() method.
        self.assertIsNotNone(product.id)
        # Fetch the product back from the system using the product ID and store it in found_product
        found_product = product.find(product.id)
        self.assertEqual(found_product.name, product.name)
        self.assertEqual(found_product.description, product.description)
        self.assertEqual(Decimal(found_product.price), product.price)
        self.assertEqual(found_product.available, product.available)
        self.assertEqual(found_product.category, product.category)

    def test_update_a_product(self):
        """It should Update a Product"""
        product = ProductFactory()
        # Set the ID of the product object to None and then call the create() method on the product.
        product.id = None
        product.create()
        self.assertIsNotNone(product.id)
        # Update the product in the system with the new property values using the update() method.
        product.description = "testing"
        original_id = product.id
        product.update()
        self.assertEqual(product.id, original_id)
        self.assertEqual(product.description, "testing")
        # Fetch all the product back from the system.
        products = Product.all()
        self.assertEqual(len(products), 1)
        # Assert that the fetched product has id same as the original id.
        self.assertEqual(products[0].id, original_id)
        # Assert that the fetched product has the updated description.
        self.assertEqual(products[0].description, "testing")

    def test_update_product_with_no_id(self):
        """It should not update a Product with no ID"""
        product = ProductFactory()
        product.id = None  # Ensure the product has no ID
        product.description = "Invalid update"

        with self.assertRaises(DataValidationError) as context:
            product.update()

        self.assertEqual(str(context.exception), "Update called with empty ID field")

    def test_delete_a_product(self):
        """It should Delete a Product"""
        product = ProductFactory()
        # Call the create() method on the product to save it to the database.
        product.id = None
        product.create()

        self.assertEqual(len(Product.all()), 1)

        product.delete()

        self.assertEqual(len(Product.all()), 0)

    def test_deserialize_invalid_category(self):
        """It should raise an error when category is invalid"""
        product = Product()
        # Pass invalid data where "category" is not a valid enum value
        invalid_data = {
            "name": "Test Product",
            "description": "Test Description",
            "price": "19.99",
            "available": True,
            "category": "INVALID_CATEGORY"  # Invalid category
        }

        with self.assertRaises(DataValidationError) as context:
            product.deserialize(invalid_data)

        # Verify the error message contains "Invalid attribute"
        self.assertTrue("Invalid attribute" in str(context.exception))

    def test_deserialize_invalid_available_type(self):
        """It should raise an error when available is not a boolean"""
        product = Product()
        # Pass invalid data where "available" is not a boolean (e.g., a string)
        invalid_data = {
            "name": "Test Product",
            "description": "Test Description",
            "price": "19.99",
            "available": "yes",  # Invalid type (should be boolean)
            "category": "ELECTRONICS"
        }

        with self.assertRaises(DataValidationError) as context:
            product.deserialize(invalid_data)

        # Verify the error message
        self.assertEqual(
            str(context.exception),
            "Invalid type for boolean [available]: <class 'str'>"
        )

    def test_deserialize_missing_key(self):
        """It should raise an error when a required key is missing"""
        product = Product()
        # Pass data with the 'name' key missing
        invalid_data = {
            "description": "Test Description",
            "price": "19.99",
            "available": True,
            "category": "ELECTRONICS"
        }

        with self.assertRaises(DataValidationError) as context:
            product.deserialize(invalid_data)

        # Verify the error message contains "Invalid product: missing name"
        self.assertEqual(str(context.exception), "Invalid product: missing name")

    def test_deserialize_invalid_type(self):
        """It should raise an error when data is not a dictionary"""
        product = Product()
        # Pass an invalid data type (e.g., a string instead of a dictionary)
        invalid_data = "this is not a dictionary"

        with self.assertRaises(DataValidationError) as context:
            product.deserialize(invalid_data)

        # Verify the error message contains "Invalid product: body of request contained bad or no data"
        self.assertTrue("Invalid product: body of request contained bad or no data" in str(context.exception))

    def test_list_all_products(self):
        """It should List all Products in the database"""
        products = Product.all()

        self.assertEqual(len(products), 0)

        for _ in range(5):
            product = ProductFactory()
            product.create()
        # Fetch all products from the database again using product.all()
        products = Product.all()

        self.assertEqual(len(products), 5)

    def test_find_by_name(self):
        """It should Find a Product by Name"""
        products = ProductFactory.create_batch(5)
        for product in products:
            product.create()
        name = products[0].name
        count = len([product for product in products if product.name == name])
        found = Product.find_by_name(name)
        self.assertEqual(found.count(), count)
        for product in found:
            self.assertEqual(product.name, name)

    def test_find_by_availability(self):
        """It should Find Products by Availability"""
        products = ProductFactory.create_batch(10)
        for product in products:
            product.create()
        available = products[0].available
        count = len([product for product in products if product.available == available])
        found = Product.find_by_availability(available)
        self.assertEqual(found.count(), count)
        for product in found:
            self.assertEqual(product.available, available)

    def test_find_by_category(self):
        """It should Find Products by Category"""
        products = ProductFactory.create_batch(10)
        for product in products:
            product.create()
        category = products[0].category
        count = len([product for product in products if product.category == category])
        found = Product.find_by_category(category)
        self.assertEqual(found.count(), count)
        for product in found:
            self.assertEqual(product.category, category)
