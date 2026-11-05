"""
Tests for HexMedia Light Theme and Theme Switching (Zero FOUC, Contrast, Toggle).
"""
import re
from django.test import TestCase, Client
from django.urls import reverse


class ThemeToggleAndTokensTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        with open("backend/templates/chat/index.html", "r", encoding="utf-8") as f:
            self.html_content = f.read()

    def test_zero_fouc_script_exists_in_head(self):
        """Zero-FOUC script should be in <head> checking localStorage for saved theme."""
        head_match = re.search(r"<head>(.*?)</head>", self.html_content, re.DOTALL)
        self.assertIsNotNone(head_match, "<head> section missing")
        head_content = head_match.group(1)
        self.assertIn("localStorage.getItem('hexmedia_theme')", head_content)
        self.assertIn("document.documentElement.classList.remove('dark')", head_content)
        self.assertIn("document.documentElement.classList.add('dark')", head_content)

    def test_css_variables_light_and_dark_tokens(self):
        """CSS variables must contain both light (:root) and dark (html.dark) tokens."""
        # Light mode tokens
        self.assertIn("--color-obsidian: #faf8f5;", self.html_content)
        self.assertIn("--color-surface: #ffffff;", self.html_content)
        self.assertIn("--color-surfaceHover: #f3f0ea;", self.html_content)
        self.assertIn("--color-borderSubtle: #e6e2d8;", self.html_content)
        self.assertIn("--color-light: #292524;", self.html_content)
        self.assertIn("--color-muted: #78716c;", self.html_content)
        self.assertIn("--color-limeAccent: #65a30d;", self.html_content)

        # Light mode RGB space-separated tokens for Tailwind opacity
        self.assertIn("--color-obsidian-rgb: 250 248 245;", self.html_content)
        self.assertIn("--color-surface-rgb: 255 255 255;", self.html_content)
        self.assertIn("--color-surfaceHover-rgb: 243 240 234;", self.html_content)
        self.assertIn("--color-borderSubtle-rgb: 230 226 216;", self.html_content)
        self.assertIn("--color-light-rgb: 41 37 36;", self.html_content)
        self.assertIn("--color-muted-rgb: 120 113 108;", self.html_content)
        self.assertIn("--color-limeAccent-rgb: 101 163 13;", self.html_content)

        # Dark mode tokens
        self.assertIn("--color-obsidian: #08080a;", self.html_content)
        self.assertIn("--color-surface: #0e0e12;", self.html_content)
        self.assertIn("--color-surfaceHover: #14141a;", self.html_content)
        self.assertIn("--color-borderSubtle: #1c1c22;", self.html_content)
        self.assertIn("--color-light: #f4f4f6;", self.html_content)
        self.assertIn("--color-muted: #71717a;", self.html_content)
        self.assertIn("--color-limeAccent: #e2ff44;", self.html_content)

    def test_tailwind_config_uses_rgb_alpha_variables(self):
        """Tailwind config should use rgb(var(--color-*-rgb) / <alpha-value>) for full opacity support."""
        self.assertIn("darkMode: 'class'", self.html_content)
        self.assertIn("obsidian: 'rgb(var(--color-obsidian-rgb) / <alpha-value>)'", self.html_content)
        self.assertIn("surface: 'rgb(var(--color-surface-rgb) / <alpha-value>)'", self.html_content)
        self.assertIn("limeAccent: 'rgb(var(--color-limeAccent-rgb) / <alpha-value>)'", self.html_content)
        self.assertIn("light: 'rgb(var(--color-light-rgb) / <alpha-value>)'", self.html_content)

    def test_theme_toggle_button_and_icons_exist(self):
        """Theme toggle button should exist in the header with Sun and Moon SVGs."""
        self.assertIn('id="themeToggleBtn"', self.html_content)
        self.assertIn('onclick="toggleTheme()"', self.html_content)
        self.assertIn('id="themeIconSun"', self.html_content)
        self.assertIn('id="themeIconMoon"', self.html_content)

    def test_theme_functions_defined_in_javascript(self):
        """toggleTheme and syncThemeToggleUI should be declared in JavaScript."""
        self.assertIn("function toggleTheme()", self.html_content)
        self.assertIn("function syncThemeToggleUI()", self.html_content)
        self.assertIn("syncThemeToggleUI();", self.html_content)
        self.assertIn("localStorage.setItem('hexmedia_theme'", self.html_content)

    def test_no_hardcoded_dark_colors_in_modals(self):
        """Modals and menus should not have hardcoded dark backgrounds or text-white."""
        # Check that modals don't use raw dark hex backgrounds
        self.assertNotIn('bg-[#0c0c10]', self.html_content)
        self.assertNotIn('border-[#1f1f2a]', self.html_content)
        self.assertNotIn('border-[#232330]', self.html_content)

    def test_theme_toggle_smooth_transition_and_animation(self):
        """Theme toggle button and icons must support smooth rotate/scale morphing transitions."""
        self.assertIn("overflow-hidden", self.html_content)
        self.assertIn("transition-all duration-300 transform", self.html_content)
        self.assertIn("scale-100", self.html_content)
        self.assertIn("scale-0", self.html_content)
        self.assertIn("rotate-90", self.html_content)

    def test_no_unreadable_zinc_classes_in_chat_and_modals(self):
        """Transcript and modal secondary text must use theme-adaptive text-muted, not low-contrast zinc."""
        # Transcript preview in chat must not use washed-out text-zinc-300
        self.assertNotIn("text-zinc-300 italic", self.html_content)
        # Voice casting modal description must use text-muted, not low-contrast text-zinc-400
        self.assertNotIn("text-zinc-400 mt-0.5", self.html_content)
        self.assertIn('class="text-[10px] text-muted mt-0.5">${v.description}</p>', self.html_content)
        # Thread list empty state must not use hardcoded text-zinc-600
        self.assertNotIn("text-zinc-600 px-3 py-4", self.html_content)

    def test_template_renders_successfully_via_view(self):
        """Chat view should render index.html with 200 OK."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")
        self.assertIn("themeToggleBtn", content)
        self.assertIn("themeIconSun", content)
        self.assertIn("themeIconMoon", content)

