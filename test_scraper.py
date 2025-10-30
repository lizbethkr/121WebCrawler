import unittest
from unittest.mock import Mock, patch
from urllib.parse import urlparse
import os
from scraper import (
    scraper, extract_next_links, is_valid, unique_urls_write,
    confirm_longest_page, longest_page_file, common_words_file,
    subdomains, subdomain_write, tokenize, word_freq, word_count_check,
    VISITED, DO_NOT_ENTER, COMMON_WORDS, SUBDOMAINS, LONGEST_PAGE
)


class TestWebScraper(unittest.TestCase):

    def setUp(self):
        """Reset global state before each test"""
        print(f"\n=== Setting up for test: {self._testMethodName} ===")
        VISITED.clear()
        DO_NOT_ENTER.clear()
        COMMON_WORDS.clear()
        SUBDOMAINS.clear()

        # Reset the LONGEST_PAGE in the scraper module
        import scraper
        scraper.LONGEST_PAGE = ('', 0)

        # Create Report directory if it doesn't exist
        os.makedirs('Report', exist_ok = True)

    def tearDown(self):
        """Clean up after each test"""
        print(f"=== Tearing down test: {self._testMethodName} ===")

    # Test scraper function
    def test_scraper_successful_response(self):
        """Test scraper with successful 200 response"""
        print("Running test_scraper_successful_response")
        mock_resp = Mock()
        mock_resp.status = 200
        mock_resp.raw_response = Mock()
        mock_resp.raw_response.headers = {'Content-Type': 'text/html'}
        mock_resp.raw_response.content = b'<html><a href="https://example.ics.uci.edu/page1">Link</a></html>'

        with patch('scraper.extract_next_links') as mock_extract:
            with patch('scraper.tokenize') as mock_tokenize:
                with patch('scraper.subdomains') as mock_subdomains:
                    with patch('scraper.confirm_longest_page') as mock_confirm:
                        with patch('scraper.word_freq') as mock_word_freq:
                            mock_extract.return_value = ['https://example.ics.uci.edu/page1']
                            mock_tokenize.return_value = ['test', 'words']

                            result = scraper('https://example.ics.uci.edu', mock_resp)

                            self.assertEqual(result, ['https://example.ics.uci.edu/page1'])
                            self.assertIn('https://example.ics.uci.edu', VISITED)

    def test_scraper_non_200_response(self):
        """Test scraper with non-200 response"""
        print("Running test_scraper_non_200_response")
        mock_resp = Mock()
        mock_resp.status = 404
        mock_resp.raw_response = None

        # Mock the file writing functions to avoid directory issues during this test
        with patch('scraper.common_words_file'):
            with patch('scraper.longest_page_file'):
                with patch('scraper.subdomain_write'):
                    with patch('scraper.unique_urls_write'):
                        result = scraper('https://example.ics.uci.edu', mock_resp)

        self.assertEqual(result, [])
        self.assertIn('https://example.ics.uci.edu', DO_NOT_ENTER)

    # Test extract_next_links function
    def test_extract_next_links_success(self):
        """Test successful link extraction"""
        print("Running test_extract_next_links_success")
        mock_resp = Mock()
        mock_resp.status = 200
        mock_resp.raw_response = Mock()
        mock_resp.raw_response.headers = {'Content-Type': 'text/html'}
        mock_resp.raw_response.content = b'<html><a href="/page1">Link1</a><a href="/page2">Link2</a></html>'

        # Mock is_valid to return True and word_count_check to return False
        with patch('scraper.is_valid') as mock_valid:
            with patch('scraper.word_count_check') as mock_word_check:
                mock_valid.return_value = True
                mock_word_check.return_value = False

                links = extract_next_links('https://example.ics.uci.edu', mock_resp)

                print(f"Extracted links: {links}")
                self.assertEqual(len(links), 2)
                self.assertIn('https://example.ics.uci.edu/page1', links)
                self.assertIn('https://example.ics.uci.edu/page2', links)

    def test_extract_next_links_non_html(self):
        """Test extraction with non-HTML content"""
        print("Running test_extract_next_links_non_html")
        mock_resp = Mock()
        mock_resp.status = 200
        mock_resp.raw_response = Mock()
        mock_resp.raw_response.headers = {'Content-Type': 'application/pdf'}

        links = extract_next_links('https://example.ics.uci.edu', mock_resp)

        self.assertEqual(links, [])  # Expect empty LIST, not set
        self.assertIn('https://example.ics.uci.edu', DO_NOT_ENTER)

    # Test is_valid function
    def test_is_valid_good_url(self):
        """Test valid UCI domain URLs"""
        print("Running test_is_valid_good_url")
        valid_urls = [
            'https://ics.uci.edu/page',
            'https://cs.uci.edu/research',
            'https://informatics.uci.edu/about',
            'https://stat.uci.edu/data'
        ]

        for url in valid_urls:
            with self.subTest(url = url):
                print(f"Testing valid URL: {url}")
                result = is_valid(url)
                print(f"Result: {result}")
                self.assertTrue(result, f"URL {url} should be valid")

    def test_is_valid_bad_domains(self):
        """Test invalid domains"""
        print("Running test_is_valid_bad_domains")
        invalid_urls = [
            'https://example.com/page',
            'https://uci.edu/home',
            'https://math.uci.edu/test'  # Not in allowed domains
        ]

        for url in invalid_urls:
            with self.subTest(url = url):
                print(f"Testing invalid domain: {url}")
                result = is_valid(url)
                print(f"Result: {result}")
                self.assertFalse(result, f"URL {url} should be invalid")

    def test_is_valid_file_extensions(self):
        """Test URLs with disallowed file extensions"""
        print("Running test_is_valid_file_extensions")
        invalid_urls = [
            'https://ics.uci.edu/image.jpg',
            'https://cs.uci.edu/document.pdf',
            'https://informatics.uci.edu/script.js',
            'https://stat.uci.edu/style.css'
        ]

        for url in invalid_urls:
            with self.subTest(url = url):
                print(f"Testing file extension: {url}")
                result = is_valid(url)
                print(f"Result: {result}")
                self.assertFalse(result, f"URL {url} should be invalid due to file extension")

    def test_is_valid_trap_keywords(self):
        """Test URLs containing trap keywords"""
        print("Running test_is_valid_trap_keywords")
        trap_urls = [
            'https://ics.uci.edu/calendar',
            'https://cs.uci.edu/event123',
            'https://informatics.uci.edu/?action=view',
            'https://stat.uci.edu/?share=twitter'
        ]

        for url in trap_urls:
            with self.subTest(url = url):
                print(f"Testing trap URL: {url}")
                result = is_valid(url)
                print(f"Result: {result}, DO_NOT_ENTER: {url in DO_NOT_ENTER}")
                self.assertFalse(result, f"URL {url} should be invalid due to trap keyword")
                # Check that the EXACT URL is in DO_NOT_ENTER (not the cleaned version)
                self.assertIn(url, DO_NOT_ENTER, f"URL {url} should be in DO_NOT_ENTER")

    # Test tokenize function
    def test_tokenize_success(self):
        """Test successful token extraction"""
        print("Running test_tokenize_success")
        mock_resp = Mock()
        mock_resp.raw_response = Mock()
        mock_resp.raw_response.content = b'<html>Hello World! This is a test 123. Testing, 1 2 3.</html>'

        tokens = tokenize(mock_resp)

        expected = ['hello', 'world', 'this', 'test', '123', 'testing']
        print(f"Tokens: {tokens}")
        print(f"Expected: {expected}")
        self.assertEqual(tokens, expected)

    def test_tokenize_empty_content(self):
        """Test tokenization with empty content"""
        print("Running test_tokenize_empty_content")
        mock_resp = Mock()
        mock_resp.raw_response = None

        tokens = tokenize(mock_resp)

        self.assertEqual(tokens, [])

    # Test word_freq function
    def test_word_freq_basic(self):
        """Test basic word frequency counting"""
        print("Running test_word_freq_basic")
        tokens = ['test', 'word', 'test', 'another', 'word', 'test']

        word_freq(tokens)

        print(f"COMMON_WORDS: {COMMON_WORDS}")
        self.assertEqual(COMMON_WORDS['test'], 3)
        self.assertEqual(COMMON_WORDS['word'], 2)
        self.assertEqual(COMMON_WORDS['another'], 1)

    def test_word_freq_stop_words(self):
        """Test that stop words are filtered out"""
        print("Running test_word_freq_stop_words")
        tokens = ['the', 'test', 'and', 'another', 'the']

        word_freq(tokens)

        print(f"COMMON_WORDS: {COMMON_WORDS}")
        self.assertNotIn('the', COMMON_WORDS)
        self.assertNotIn('and', COMMON_WORDS)
        self.assertIn('test', COMMON_WORDS)
        self.assertIn('another', COMMON_WORDS)

    # Test confirm_longest_page function
    def test_confirm_longest_page_new_longest(self):
        """Test updating when new longest page is found"""
        print("Running test_confirm_longest_page_new_longest")

        # Import the scraper module to access the actual LONGEST_PAGE
        import scraper

        confirm_longest_page('https://example.com/page1', 100)
        print(f"LONGEST_PAGE after first call: {scraper.LONGEST_PAGE}")  # Access through module
        self.assertEqual(scraper.LONGEST_PAGE,
                         ('https://example.com/page1', 100))  # Check module variable

        confirm_longest_page('https://example.com/page2', 200)
        print(f"LONGEST_PAGE after second call: {scraper.LONGEST_PAGE}")
        self.assertEqual(scraper.LONGEST_PAGE, ('https://example.com/page2', 200))

    def test_confirm_longest_page_shorter(self):
        """Test not updating when page is shorter"""
        print("Running test_confirm_longest_page_shorter")

        # Import the scraper module to access the actual LONGEST_PAGE
        import scraper

        confirm_longest_page('https://example.com/page1', 200)
        print(f"LONGEST_PAGE after first call: {scraper.LONGEST_PAGE}")
        confirm_longest_page('https://example.com/page2', 100)
        print(f"LONGEST_PAGE after second call: {scraper.LONGEST_PAGE}")
        self.assertEqual(scraper.LONGEST_PAGE, ('https://example.com/page1', 200))
    # Test subdomains function
    def test_subdomains_uci_domain(self):
        """Test subdomain extraction for UCI domains"""
        print("Running test_subdomains_uci_domain")
        test_urls = [
            ('https://cs.uci.edu/page', 'cs.uci.edu'),
            ('https://ics.uci.edu/research', 'ics.uci.edu'),
            ('https://sub.domain.ics.uci.edu/test', 'sub.domain.ics.uci.edu')
        ]

        for url, expected_domain in test_urls:
            with self.subTest(url = url):
                print(f"Testing subdomain extraction for: {url}")
                subdomains(url)
                print(f"SUBDOMAINS after processing: {SUBDOMAINS}")
                self.assertIn(expected_domain, SUBDOMAINS)
                self.assertEqual(SUBDOMAINS[expected_domain], 1)

    def test_subdomains_non_uci(self):
        """Test subdomain extraction for non-UCI domains"""
        print("Running test_subdomains_non_uci")
        subdomains('https://example.com/page')
        print(f"SUBDOMAINS after non-UCI URL: {SUBDOMAINS}")
        self.assertEqual(len(SUBDOMAINS), 0)

    def test_subdomains_www_main_page(self):
        """Test that www.uci.edu main page is ignored"""
        print("Running test_subdomains_www_main_page")
        subdomains('https://www.uci.edu/page')
        print(f"SUBDOMAINS after www.uci.edu: {SUBDOMAINS}")
        self.assertEqual(len(SUBDOMAINS), 0)

    # Test word_count_check function
    def test_word_count_check_valid(self):
        """Test valid word count range"""
        print("Running test_word_count_check_valid")
        mock_resp = Mock()
        with patch('scraper.tokenize') as mock_tokenize:
            mock_tokenize.return_value = ['word'] * 500  # 500 words
            result = word_count_check(mock_resp)
            print(f"Word count check result for 500 words: {result}")
            self.assertFalse(result)

    def test_word_count_check_too_short(self):
        """Test too short word count"""
        print("Running test_word_count_check_too_short")
        mock_resp = Mock()
        with patch('scraper.tokenize') as mock_tokenize:
            mock_tokenize.return_value = ['word'] * 49  # 49 words (BELOW threshold)
            result = word_count_check(mock_resp)
            print(f"Word count check result for 49 words: {result}")
            self.assertTrue(result)  # Should return True for too few words

    def test_word_count_check_too_long(self):
        """Test too long word count"""
        print("Running test_word_count_check_too_long")
        mock_resp = Mock()
        with patch('scraper.tokenize') as mock_tokenize:
            mock_tokenize.return_value = ['word'] * 200000  # 200k words
            result = word_count_check(mock_resp)
            print(f"Word count check result for 200k words: {result}")
            self.assertTrue(result)

    # Test file writing functions (basic structure tests)
    def test_unique_urls_write(self):
        """Test unique URLs file writing structure"""
        print("Running test_unique_urls_write")
        VISITED.add('https://example.com/page1')
        VISITED.add('https://example.com/page2')

        # Just test that function runs without error
        try:
            unique_urls_write()
            print("unique_urls_write completed successfully")
        except Exception as e:
            self.fail(f"unique_urls_write raised exception: {e}")

    def test_common_words_file(self):
        """Test common words file writing structure"""
        print("Running test_common_words_file")
        COMMON_WORDS.update({'test': 5, 'example': 3, 'word': 2})

        # Just test that function runs without error
        try:
            common_words_file()
            print("common_words_file completed successfully")
        except Exception as e:
            self.fail(f"common_words_file raised exception: {e}")

    def test_subdomain_write(self):
        """Test subdomain file writing structure"""
        print("Running test_subdomain_write")
        SUBDOMAINS.update({'ics.uci.edu': 5, 'cs.uci.edu': 3})

        # Just test that function runs without error
        try:
            subdomain_write()
            print("subdomain_write completed successfully")
        except Exception as e:
            self.fail(f"subdomain_write raised exception: {e}")

    def test_longest_page_file(self):
        """Test longest page file writing structure"""
        print("Running test_longest_page_file")
        # Use the imported LONGEST_PAGE directly
        global LONGEST_PAGE
        LONGEST_PAGE = ('https://example.com/long', 1500)

        # Just test that function runs without error
        try:
            longest_page_file()
            print("longest_page_file completed successfully")
        except Exception as e:
            self.fail(f"longest_page_file raised exception: {e}")

    # Edge cases
    def test_is_valid_malformed_url(self):
        """Test handling of malformed URLs"""
        print("Running test_is_valid_malformed_url")
        malformed_urls = ['not-a-valid-url', 'http://']

        for url in malformed_urls:
            with self.subTest(url = url):
                print(f"Testing malformed URL: {url}")
                result = is_valid(url)
                print(f"Result: {result}")
                self.assertFalse(result)

    def test_tokenize_special_characters(self):
        """Test tokenization with special characters"""
        print("Running test_tokenize_special_characters")
        mock_resp = Mock()
        mock_resp.raw_response = Mock()
        mock_resp.raw_response.content = b'<html>Email: test@example.com, Phone: (123) 456-7890</html>'

        tokens = tokenize(mock_resp)

        # Should extract alphanumeric tokens of length >= 3
        expected = ['email', 'test', 'example', 'com', 'phone', '123', '456', '7890']
        print(f"Tokens: {tokens}")
        print(f"Expected: {expected}")
        self.assertEqual(tokens, expected)

    def test_word_freq_non_alpha(self):
        """Test word frequency with non-alphabetic tokens"""
        print("Running test_word_freq_non_alpha")
        tokens = ['test123', '456', 'word', 'test123']

        word_freq(tokens)

        print(f"COMMON_WORDS: {COMMON_WORDS}")
        # Only alphabetic words should be counted
        self.assertIn('word', COMMON_WORDS)
        self.assertNotIn('test123', COMMON_WORDS)
        self.assertNotIn('456', COMMON_WORDS)

    def test_tokenize_removes_html_tags(self):
        """Test that tokenize function removes HTML tags and extracts only text content"""
        print("Running test_tokenize_removes_html_tags")

        # Test cases with HTML containing various tags
        test_cases = [
            {
                'name': 'Basic HTML with paragraphs',
                'html': b'<html><body><p>This is a paragraph</p><p>Another paragraph here</p></body></html>',
                'expected_tokens': ['this', 'paragraph', 'another', 'paragraph', 'here']
            },
            {
                'name': 'HTML with script and style tags',
                'html': b'''
                <html>
                <head>
                    <style>body { color: red; }</style>
                    <script>console.log("hello");</script>
                </head>
                <body>
                    <p>Actual content here</p>
                    <div>More real text</div>
                </body>
                </html>
                ''',
                'expected_tokens': ['actual', 'content', 'here', 'more', 'real', 'text']
            },
            {
                'name': 'HTML with mixed content and CSS classes',
                'html': b'''
                <html>
                <body>
                    <div class="header">Welcome to the site</div>
                    <p id="main-content">This is the main content area with important information</p>
                    <span style="color: blue;">Styled text</span>
                </body>
                </html>
                ''',
                'expected_tokens': ['welcome', 'the', 'site', 'this', 'the', 'main', 'content',
                                    'area', 'with', 'important', 'information', 'styled', 'text']
            },
            {
                'name': 'HTML with navigation and footer',
                'html': b'''
                <html>
                <nav>Home About Contact</nav>
                <main>
                    <article>
                        <h1>Article Title</h1>
                        <p>Article content goes here in the main section</p>
                    </article>
                </main>
                <footer>Copyright information</footer>
                </html>
                ''',
                'expected_tokens': ['home', 'about', 'contact', 'article', 'title', 'article',
                                    'content', 'goes', 'here', 'the', 'main', 'section',
                                    'copyright', 'information']
            },
            {
                'name': 'HTML with JavaScript variables and CSS properties',
                'html': b'''
                <html>
                <script>
                    var color = "red";
                    function test() { return true; }
                    let backgroundColor = "#fff";
                </script>
                <style>
                    .container { width: 100%; height: auto; }
                    p { font-size: 16px; margin: 10px; }
                </style>
                <body>
                    <p>Real page content that should be extracted</p>
                    <div>Additional meaningful text</div>
                </body>
                </html>
                ''',
                'expected_tokens': ['real', 'page', 'content', 'that', 'should', 'extracted',
                                    'additional', 'meaningful', 'text']
            },
            {
                'name': 'HTML with forms and inputs',
                'html': b'''
                <html>
                <body>
                    <form action="/submit" method="post">
                        <input type="text" name="username">
                        <input type="password" name="password">
                        <button type="submit">Login to system</button>
                    </form>
                    <p>Form description text</p>
                </body>
                </html>
                ''',
                'expected_tokens': ['login', 'system', 'form', 'description', 'text']
            }
        ]

        # CSS/JS specific keywords that should NEVER appear in content
        # These are programming-specific identifiers, not common English words
        css_js_specific_keywords = [
            'var', 'function', 'return', 'let', 'console', 'log',
            'backgroundColor', 'width', 'height', 'font', 'size', 'margin',
            'action', 'submit', 'method', 'post', 'type', 'name'
        ]

        for test_case in test_cases:
            with self.subTest(test_case = test_case['name']):
                print(f"\nTesting: {test_case['name']}")

                mock_resp = Mock()
                mock_resp.raw_response = Mock()
                mock_resp.raw_response.content = test_case['html']

                tokens = tokenize(mock_resp)

                print(f"Extracted tokens: {tokens}")
                print(f"Expected tokens: {test_case['expected_tokens']}")

                # Check that we got the expected tokens
                self.assertEqual(tokens, test_case['expected_tokens'],
                                 f"Failed for test case: {test_case['name']}")

                # Additional assertion: verify no CSS/JS-specific tokens are present
                for keyword in css_js_specific_keywords:
                    self.assertNotIn(keyword.lower(), tokens,
                                     f"CSS/JS keyword '{keyword}' found in tokens for {test_case['name']}")
    def test_tokenize_preserves_meaningful_content(self):
        """Test that tokenize preserves meaningful academic content"""
        print("Running test_tokenize_preserves_meaningful_content")

        # Simulate academic content that should be preserved
        academic_html = b'''
        <html>
        <head>
            <title>Research in Computer Science</title>
            <style>.title { font-size: 24px; }</style>
            <script>trackPageView();</script>
        </head>
        <body>
            <div class="container">
                <h1>Artificial Intelligence Research</h1>
                <p>The Department of Computer Science conducts cutting-edge research 
                in artificial intelligence, machine learning, and data science. 
                Our faculty members work on innovative projects that advance the 
                field of computer science.</p>

                <section id="research-areas">
                    <h2>Research Areas</h2>
                    <ul>
                        <li>Machine Learning and Data Mining</li>
                        <li>Computer Vision and Pattern Recognition</li>
                        <li>Natural Language Processing</li>
                        <li>Robotics and Autonomous Systems</li>
                    </ul>
                </section>

                <div class="publications">
                    <h3>Recent Publications</h3>
                    <p>Our researchers have published papers in top-tier conferences 
                    including NeurIPS, ICML, and CVPR.</p>
                </div>
            </div>
        </body>
        </html>
        '''

        mock_resp = Mock()
        mock_resp.raw_response = Mock()
        mock_resp.raw_response.content = academic_html

        tokens = tokenize(mock_resp)

        print(f"Academic content tokens: {tokens}")

        # Verify meaningful academic content is preserved
        expected_academic_words = [
            'research', 'computer', 'science', 'artificial', 'intelligence',
            'machine', 'learning', 'data', 'faculty', 'projects', 'field',
            'areas', 'vision', 'pattern', 'recognition', 'natural', 'language',
            'processing', 'robotics', 'autonomous', 'systems', 'publications',
            'recent', 'researchers', 'published', 'papers', 'conferences'
        ]

        for word in expected_academic_words:
            self.assertIn(word, tokens, f"Academic word '{word}' should be preserved")

        # Verify CSS/JS content is removed
        css_js_words = ['title', 'font', 'size', 'trackpageview', 'container', 'class']
        for word in css_js_words:
            self.assertNotIn(word, tokens, f"CSS/JS word '{word}' should be removed")

    def test_tokenize_empty_or_minimal_content(self):
        """Test tokenize with empty or minimal content"""
        print("Running test_tokenize_empty_or_minimal_content")

        test_cases = [
            {
                'name': 'Empty HTML',
                'html': b'<html></html>',
                'expected_tokens': []
            },
            {
                'name': 'Only script tags',
                'html': b'<html><script>var x = 1;</script><script>function y() {}</script></html>',
                'expected_tokens': []
            },
            {
                'name': 'Only style tags',
                'html': b'<html><style>body { margin: 0; }</style><style>p { color: black; }</style></html>',
                'expected_tokens': []
            },
            {
                'name': 'Mixed but very short content',
                'html': b'<html><style>css</style><p>Hi</p><script>js</script></html>',
                'expected_tokens': []  # "Hi" is less than 3 characters, so filtered out
            }
        ]

        for test_case in test_cases:
            with self.subTest(test_case = test_case['name']):
                print(f"Testing: {test_case['name']}")

                mock_resp = Mock()
                mock_resp.raw_response = Mock()
                mock_resp.raw_response.content = test_case['html']

                tokens = tokenize(mock_resp)

                print(f"Tokens: {tokens}")
                print(f"Expected: {test_case['expected_tokens']}")

                self.assertEqual(tokens, test_case['expected_tokens'])


if __name__ == '__main__':
    unittest.main(verbosity = 2)