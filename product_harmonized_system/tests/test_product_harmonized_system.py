from textwrap import shorten

from odoo.addons.base.tests.common import BaseCommon


class TestProductHarmonizedSystem(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_a = cls.env["res.company"].create({"name": "Company A"})
        cls.country = cls.env.ref("base.us")
        cls.HS1 = cls.env["hs.code"].create(
            {
                "local_code": "12345678",
                "description": "Test Description",
                "company_id": cls.company_a.id,
            }
        )

        cls.category = cls.env["product.category"].create(
            {
                "name": "Parent Category",
                "hs_code_id": cls.HS1.id,
            }
        )

        cls.child_category = cls.env["product.category"].create(
            {
                "name": "Child Category",
                "parent_id": cls.category.id,
            }
        )

        cls.product_tmpl = cls.env["product.template"].create(
            {
                "name": "Test Product Template",
                "categ_id": cls.child_category.id,
                "hs_code_id": cls.HS1.id,
                "origin_country_id": cls.country.id,
            }
        )

        cls.Product = cls.product_tmpl.product_variant_id

    def test_local_code_and_counts(self):
        """Test local_code space stripping and product/category counts."""
        hs = self.env["hs.code"].create(
            {
                "local_code": "12 34 56 99",
                "company_id": self.company_a.id,
            }
        )
        self.assertEqual(hs.local_code, "12345699", "local code not stripped correctly")
        hs.write({"local_code": "  9 9 9 9 9 9  "})
        self.assertEqual(
            hs.local_code, "999999", "local code not updated/stripped correctly"
        )
        # Test product/category counts
        self.assertEqual(
            self.HS1.product_tmpl_count, 1, "product template count mismatch"
        )
        self.assertEqual(
            self.HS1.product_categ_count, 1, "product category count mismatch"
        )

    def test_recursive_hs_lookup(self):
        """Test HS code lookup recursively through category and product hierarchy."""
        category_hs = self.child_category.get_hs_code_recursively()
        self.assertEqual(category_hs, self.HS1, "Recursive HS failed for category")
        product_hs = self.Product.get_hs_code_recursively()
        self.assertEqual(product_hs, self.HS1, "Recursive HS failed for product")

    def test_recursive_no_hs(self):
        """Ensure recursive HS lookup returns False when no HS code is set."""
        # Category with no HS code
        category = self.env["product.category"].create({"name": "No HS"})
        self.assertFalse(
            category.get_hs_code_recursively(), "Expected False for category with no HS"
        )

        # Product with no HS code
        prod = self.env["product.product"].create({"name": "No HS Prod"})
        self.assertFalse(
            prod.get_hs_code_recursively(), "Expected False for product with no HS"
        )

    def test_display_name_computation_and_truncation(self):
        """Verify that display_name is correctly computed and truncated."""
        long_desc = "D" * 200
        self.HS1.write(
            {
                "description": long_desc,
            }
        )
        expected = shorten(self.HS1.local_code + " " + long_desc, 55)
        self.assertEqual(
            self.HS1.display_name,
            expected,
            "display_name computation/truncation failed",
        )

    def test_default_company_id_is_false(self):
        """Verify that the default company_id is False if not specified."""
        hs = self.env["hs.code"].create({"local_code": "88888888"})
        self.assertFalse(hs.company_id, "Default company_id should be False")
