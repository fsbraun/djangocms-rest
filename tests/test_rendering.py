from cms.api import create_page
from cms.test_utils.testcases import CMSTestCase
from django.urls import reverse


class RESTTestCase(CMSTestCase):
    prefix = "http://testserver"


class AliasAPITestCase(RESTTestCase):
    def setUp(self):
        super().setUp()
        # Create a test page with multiple language versions
        self.page = create_page(
            "test page",
            template="INHERIT",
            language="en",
            published=True
        )
        # Create language versions
        self.page.create_translation('de', title='Testseite')
        self.page.create_translation('fr', title='page de test')
        
    def test_alias_list(self):
        """Test that the alias list endpoint returns correct data"""
        url = reverse("cms-alias-list", kwargs={"language": "en"})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify structure of returned data
        self.assertTrue(isinstance(data, list))
        if len(data) > 0:
            alias = data[0]
            self.assertIn('url', alias)
            self.assertIn('redirect_to', alias)
            self.assertIn('language', alias)
            self.assertIn('is_active', alias)
            
    def test_alias_language_filter(self):
        """Test that aliases are correctly filtered by language"""
        url = reverse("cms-alias-list", kwargs={"language": "de"})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify all returned aliases are for German language
        for alias in data:
            self.assertEqual(alias['language'], 'de')
            
    def test_invalid_language(self):
        """Test that invalid language code returns 404"""
        url = reverse("cms-alias-list", kwargs={"language": "invalid"})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)


class RenderingTestCase(RESTTestCase):
    def _create_pages(self, page_list, parent=None):
        new_pages =  [create_page(
            f"page {i}",
            language="en",
            template="INHERIT",
            parent=parent
        ) for i in range(page_list if isinstance(page_list, int) else len(page_list))]
        if isinstance(page_list, list):
            for i, page in enumerate(new_pages):
                self._create_pages(page_list[i], page)
        else:
            self.pages = new_pages

    def setUp(self):
        self._create_pages([2, (3, 1), 2])

    def test_rendering_languages(self):
        from cms.utils.conf import get_cms_setting

        languages = get_cms_setting("LANGUAGES")[1]
        check_items = (
            "code", "name", "public", "redirect_on_fallback", "fallbacks",
            "hide_untranslated"
        )
        result = self.client.get(reverse("cms-language-list"))
        self.assertEqual(result.status_code, 200)
        data = {item["code"]: item for item in result.json()}

        for lang_config in languages:
            lang = lang_config["code"]
            for item in check_items:
                self.assertEqual(lang_config[item], data[lang][item])
            self.assertEqual(data[lang]["pages"], self.prefix + reverse("cms-page-list", args=[lang]))
