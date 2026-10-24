# Graph Report - hexmedia  (2026-10-24)

## Corpus Check
- 158 files · ~234,573 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 54 file(s) not represented in the graph (top: .csv 53, (none) 1)

## Summary
- 1848 nodes · 3235 edges · 114 communities (86 shown, 28 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 239 edges (avg confidence: 0.88)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- UI UX Pro Max Quality Tests
- Shadcn Component Add CLI
- BM25 UX Search Engine
- CIP Core & Brief Engine
- CIP Deliverable HTML Renderer
- Design Tokens Primitive Palette
- Semantic Color Tokens
- Component Surface Tokens
- Slide Layout & Search
- HexMedia Backend API Endpoints
- Chat Studio Web Templates
- Frontend React Vite Package
- Design Tokens Spacing Scale
- Brand Token Sync Tests
- HTML Design Token Validator
- UI UX Design System Core
- Desktop & Native Stack Freshness
- Gemini & Inngest Async Tasks
- LangGraph Story Director Engine
- Presentation Slide Generator
- Design System Generator
- Social Banner Sizes & Styles
- Component Specifications & Specs
- Dark Mode & Palette Selector
- UX Design System Formatter
- Django AI Studio Admin
- Tailwind Config Unit Tests
- Slide Presentation Templates
- Stock Background Fetcher
- Remotion Film Render Pipeline
- MinIO Storage & Audio Services
- HexMedia Django Studio Models
- Corporate Identity Program Design
- CIP Mockup Generator
- CIP Knowledge Search CLI
- Typography & Size Tokens
- UI UX Palette Resolvers
- Catalog Refresh & Cache Tests
- Frontend TypeScript Configuration
- Banner Design & Export Flow
- Brand Identity & Guidelines
- Brand Typography & Scale
- Social Media Banner Specs
- Tailwind Styling Utilities
- UI UX Reasoning Contracts
- UI UX Data Contracts Tests
- Web Stack Freshness Tests
- Continuous Audio Pipeline
- Sound Effects & TTS Engine
- Tailwind Responsive Breakpoints
- Docker Compose Infrastructure
- Logo Design & Prompting
- Tailwind Border Radius Tokens
- Brand Guidelines Starter Kit
- Typography Design Specifications
- Brand Colors & Palettes
- Presentation Copywriting Formulas
- CIP Prompt Engineering
- Font Pairing Recommendations
- UI Component Design Rules
- UI UX Search Evaluation
- Script Extraction & Splitter
- Brand Voice Framework
- Visual Identity Guidelines
- Brand Asset Organization
- Desktop Stack Benchmark Tests
- Brand Approval Checklist
- Token Embedding Engine
- Design Token Validator
- Animation Duration Tokens
- Brand Consistency Checklist
- Brand Context Injector
- Logo Design Principles
- Slide Copywriting Frameworks
- UI Style Taxonomy Tests
- UI Styling Library Core
- Brand Token Synchronizer
- Design Token Generator CLI
- Font Size Semantic Tokens
- Shadcn Accessibility Guidelines
- UI UX Application Rules
- CIP Deliverables Reference
- Relevance Gate & Threshold Tests
- Canvas Design System Principles
- Shadcn Component Display Specs
- Tailwind Apply Directives
- Tailwind Arbitrary Values
- Slide Deck Generator References
- Small Font Size Tokens
- BM25 Tokenizer Unit Tests
- Data Contract Splitter Tests
- Shadcn Theming & CSS Variables
- Tailwind Container Queries
- Large Font Size Tokens
- BM25 Algorithm Core Tests
- Relevance Metric Math Tests
- AI Audio Drama Engine Readme
- UI Styling Python Requirements
- Design Tokens Starter Manifest
- Default Component Variant Tokens
- Medium Token Variant Defaults
- Token Reset & None Variants
- Test Fixture Validation
- HexMedia Django App Config

## God Nodes (most connected - your core abstractions)
1. `TailwindConfigGenerator` - 58 edges
2. `BookProject` - 38 edges
3. `TestTailwindConfigGenerator` - 35 edges
4. `DesignSystemGenerator` - 35 edges
5. `ShadcnInstaller` - 34 edges
6. `TestShadcnInstaller` - 26 edges
7. `upload_bytes()` - 25 edges
8. `Scene` - 18 edges
9. `continuous_generation_worker()` - 18 edges
10. `generate_voice_audio()` - 17 edges

## Surprising Connections (you probably didn't know these)
- `Starter Brand Color Palette` --semantically_similar_to--> `Color System Hierarchy`  [INFERRED] [semantically similar]
  .agents/skills/brand/templates/brand-guidelines-starter.md → .agents/skills/brand/references/color-palette-management.md
- `Professional App UI Rules and Pre-Delivery Checklist` --semantically_similar_to--> `shadcn/ui Accessibility Patterns Reference`  [INFERRED] [semantically similar]
  .agents/skills/ui-ux-pro-max/SKILL.md → .agents/skills/ui-styling/references/shadcn-accessibility.md
- `DesignCombo Studio Deep Linking (Port 5173)` --conceptually_related_to--> `Frontend Index HTML Entrypoint`  [INFERRED]
  backend/templates/chat/index.html → frontend/index.html
- `CharacterInline` --uses--> `Character`  [INFERRED]
  backend/ai_studio/admin.py → backend/ai_studio/models.py
- `Step 3: Design & Generate Options` --references--> `Color System Hierarchy`  [INFERRED]
  .agents/skills/banner-design/SKILL.md → .agents/skills/brand/references/color-palette-management.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Brand Package Generation Pipeline** — agents_skills_design_skill_complete_brand_package, agents_skills_design_references_logo_design_ai_generation_pipeline, agents_skills_design_references_cip_design_mockup_generation_pipeline, agents_skills_design_references_slides_presentation_workflow [EXTRACTED 1.00]
- **Strategic Presentation Creation Framework** — agents_skills_design_references_slides_presentation_workflow, agents_skills_design_references_slides_strategies_yc_seed_deck_structure, agents_skills_design_references_slides_layout_patterns_layout_decision_flow, agents_skills_design_references_slides_copywriting_formulas_slide_emotion_mapping, agents_skills_design_references_slides_html_template_responsive_deck_container [EXTRACTED 1.00]
- **Visual Asset Art Direction and Export System** — agents_skills_design_references_banner_sizes_and_styles_22_art_direction_styles, agents_skills_design_references_social_photos_design_8step_orchestration, agents_skills_design_references_social_photos_design_screenshot_export_pipeline, agents_skills_design_references_icon_design_svg_generation_pipeline [INFERRED 0.85]

## Communities (114 total, 28 thin omitted)

### Community 0 - "UI UX Pro Max Quality Tests"
Cohesion: 0.06
Nodes (43): read_rows(), TestAccessibilityGuidance, TestChartsTypographyAndIcons, TestCurrentReactGuidance, TestSemanticColors, TestGeneratedCatalogContract, _catalog_date(), _check_app_interface_contract() (+35 more)

### Community 1 - "Shadcn Component Add CLI"
Cohesion: 0.05
Nodes (3): main(), ShadcnInstaller, TestShadcnInstaller

### Community 2 - "BM25 UX Search Engine"
Cohesion: 0.06
Nodes (31): BM25, _contains_phrase(), detect_domain(), _domain_keywords(), _exact_match_diagnostic(), _exact_row_identity(), _exact_stack_identifier(), _file_signature() (+23 more)

### Community 3 - "CIP Core & Brief Engine"
Cohesion: 0.06
Nodes (20): BM25, detect_domain(), get_cip_brief(), _load_csv(), search(), search_all(), _search_csv(), BM25 (+12 more)

### Community 4 - "CIP Deliverable HTML Renderer"
Cohesion: 0.06
Nodes (18): generate_html(), get_deliverable_info(), get_image_base64(), main(), apply_color(), apply_viewbox_size(), extract_svgs(), generate_batch() (+10 more)

### Community 5 - "Design Tokens Primitive Palette"
Cohesion: 0.05
Nodes (53): $type, $value, $type, $value, $type, $value, $type, $value (+45 more)

### Community 6 - "Semantic Color Tokens"
Cohesion: 0.04
Nodes (46): $type, $value, background, destructive, destructive-foreground, foreground, muted, muted-foreground (+38 more)

### Community 7 - "Component Surface Tokens"
Cohesion: 0.06
Nodes (45): $type, $value, $type, $value, bg, fg, font-size, hover-bg (+37 more)

### Community 8 - "Slide Layout & Search"
Cohesion: 0.08
Nodes (17): format_context(), format_result(), main(), BM25, calculate_pattern_break(), detect_domain(), get_background_config(), get_color_for_emotion() (+9 more)

### Community 9 - "HexMedia Backend API Endpoints"
Cohesion: 0.10
Nodes (32): approve_casting_endpoint(), CharacterVoiceUpdate, chat_endpoint(), ChatRequest, ChatResponse, ConfigResponse, execute_chapter_endpoint(), ExecuteChapterRequest (+24 more)

### Community 10 - "Chat Studio Web Templates"
Cohesion: 0.06
Nodes (36): Chat & Story Generation API Client (/api/chat), Audio Master Export API Client (/api/projects/{id}/export), Full Film Video Rendering API Client (/api/projects/{id}/render-film), Scene Visual & Voice Regeneration API Client (/api/scenes/), Book Ingestion & Parsing API Client (/api/upload-book), Audio Waveform & Sequential Playback Engine, DesignCombo Studio Deep Linking (Port 5173), Floating Action Dock & Multi-tool Selector (+28 more)

### Community 11 - "Frontend React Vite Package"
Cohesion: 0.07
Nodes (31): dependencies, lucide-react, react, react-dom, devDependencies, @types/react, @types/react-dom, typescript (+23 more)

### Community 12 - "Design Tokens Spacing Scale"
Cohesion: 0.06
Nodes (34): $type, $value, $type, $value, $type, $value, $type, $value (+26 more)

### Community 13 - "Brand Token Sync Tests"
Cohesion: 0.13
Nodes (5): test_sync_parses_bundled_starter_template(), main(), _run(), test_flags_hardcoded_hex_sharing_line_with_token(), test_token_only_line_reports_no_violation()

### Community 14 - "HTML Design Token Validator"
Cohesion: 0.13
Nodes (12): get_context(), is_allowed_exception(), is_allowed_rgba(), is_inside_block(), load_css_variables(), main(), print_result(), print_summary() (+4 more)

### Community 15 - "UI UX Design System Core"
Cohesion: 0.10
Nodes (11): ansi_ljust(), _detect_page_type(), format_ascii_box(), format_master_md(), format_page_override_md(), _generate_intelligent_overrides(), hex_to_ansi(), persist_design_system() (+3 more)

### Community 16 - "Desktop & Native Stack Freshness"
Cohesion: 0.09
Nodes (4): read_rows(), read_rows(), TestTextLayoutDataContracts, TestTextLayoutRetrieval

### Community 17 - "Gemini & Inngest Async Tasks"
Cohesion: 0.13
Nodes (13): generate_full_audio_drama(), analyze_book_text(), break_into_scenes(), extract_chapters_from_book(), extract_text_from_gemini_response(), generate_voice_audio(), get_active_config(), get_gemini_client() (+5 more)

### Community 18 - "LangGraph Story Director Engine"
Cohesion: 0.16
Nodes (17): Character, Meta, parse_duration_from_prompt(), AudioDramaState, build_audio_drama_graph(), route_action(), chat_node(), execute_chapter_node() (+9 more)

### Community 19 - "Presentation Slide Generator"
Cohesion: 0.13
Nodes (11): _e(), generate_chart_slide(), generate_cta_slide(), generate_deck(), generate_metrics_slide(), generate_problem_slide(), generate_solution_slide(), generate_testimonial_slide() (+3 more)

### Community 21 - "Social Banner Sizes & Styles"
Cohesion: 0.12
Nodes (21): CTA Action Principles, Display Ads (GDN) Sizes Specification, Banner Sizes & Art Direction Styles Reference, Pinterest Research Queries, Print Banner Sizes Specification, Banner Safe Area Guidelines, Social Media Banner Sizes Specification, 22 Art Direction Styles Catalog (+13 more)

### Community 22 - "Component Specifications & Specs"
Cohesion: 0.11
Nodes (21): Alert Component Specification, Badge Component Specification, Card Component Specification, Dialog Component Specification, Component Specifications, Input Component Specification, Table Component Specification, Alert Component Tokens (+13 more)

### Community 23 - "Dark Mode & Palette Selector"
Cohesion: 0.14
Nodes (6): _filter_anti_patterns_for_mode(), _query_wants_dark(), _resolve_color_mode(), _style_is_dark_primary(), TestAntiPatternGating, TestModeResolution

### Community 24 - "UX Design System Formatter"
Cohesion: 0.10
Nodes (5): format_markdown(), generate_design_system(), format_output(), TestDiagnosticsContracts, TestPersistence

### Community 25 - "Django AI Studio Admin"
Cohesion: 0.13
Nodes (15): AIConfigurationAdmin, BookProjectAdmin, ChapterAdmin, ChapterInline, CharacterAdmin, CharacterInline, ChatMessageAdmin, SceneAdmin (+7 more)

### Community 27 - "Slide Presentation Templates"
Cohesion: 0.12
Nodes (19): Slides Create Reference Document, Slide Creation Invocation Task, Slide CSS Animation Classes, 16:9 Aspect Ratio Slide Deck Architecture, Chart.js Integration in HTML Slides, Slide Design Token CSS Variables, HTML Slide Template Reference, Slide Navigation and Progress Tracking (+11 more)

### Community 28 - "Stock Background Fetcher"
Cohesion: 0.16
Nodes (9): generate_css_for_background(), get_background_image(), get_curated_images(), get_overlay_css(), get_pexels_search_url(), load_backgrounds_config(), load_brand_colors(), main() (+1 more)

### Community 29 - "Remotion Film Render Pipeline"
Cohesion: 0.16
Nodes (7): render_film_endpoint(), TimelineState, Meta, build_remotion_payload(), get_redis_client(), render_film_locally(), render_or_queue_project()

### Community 30 - "MinIO Storage & Audio Services"
Cohesion: 0.20
Nodes (9): ensure_bucket_exists(), get_s3_client(), upload_bytes(), upload_file_path(), enhance_visual_prompt(), generate_ai_image(), generate_fallback_cinematic_card(), produce_scene_visual() (+1 more)

### Community 31 - "HexMedia Django Studio Models"
Cohesion: 0.15
Nodes (5): AIConfiguration, Meta, ChatMessage, Meta, chat_home_view()

### Community 32 - "Corporate Identity Program Design"
Cohesion: 0.14
Nodes (16): CIP Design Reference, CIP BM25 Search Engine, Corporate Identity Program Architecture, CIP HTML Presentation Engine, CIP Mockup Generation Pipeline, AI Logo Generation Pipeline, Design Skill, Built-in Banner Design Workflow (+8 more)

### Community 33 - "CIP Mockup Generator"
Cohesion: 0.19
Nodes (7): build_cip_prompt(), check_logo_required(), generate_cip_set(), generate_with_nano_banana(), load_env(), load_logo_image(), main()

### Community 34 - "CIP Knowledge Search CLI"
Cohesion: 0.15
Nodes (5): format_brief(), format_results(), main(), format_output(), generate_design_brief()

### Community 35 - "Typography & Size Tokens"
Cohesion: 0.12
Nodes (16): $type, $value, $type, $value, $type, $value, $type, $value (+8 more)

### Community 37 - "UI UX Palette Resolvers"
Cohesion: 0.18
Nodes (4): _palette_is_dark(), _relative_luminance(), TestEndToEndCoherence, TestLuminance

### Community 39 - "Frontend TypeScript Configuration"
Cohesion: 0.13
Nodes (14): compilerOptions, allowImportingTsExtensions, isolatedModules, jsx, lib, module, moduleResolution, noEmit (+6 more)

### Community 40 - "Banner Design & Export Flow"
Cohesion: 0.15
Nodes (14): Step 4: Export Banners to Images, Asset Accessibility Checklist, Asset Archival Workflow, Content Quality & Copy Review Checklist, Asset Approval Checklist, Legal & Intellectual Property Checklist, Reviewer Sign-off & Final Approval Process, Technical & Platform Specifications Checklist (+6 more)

### Community 41 - "Brand Identity & Guidelines"
Cohesion: 0.14
Nodes (14): Brand Guidelines Template, Brand Guidelines Document Structure, Extractable Brand Fields, Logo Approval Process, Co-branding Guidelines, Logo Color & Background Rules, Logo Usage Rules, Logo Variants Specification (+6 more)

### Community 42 - "Brand Typography & Scale"
Cohesion: 0.18
Nodes (14): Major Third Type Scale System, Starter Brand Typography, Border Radius Scale, Primitive Tokens, Motion & Duration Tokens, Elevation Shadows Scale, 4px Base Unit Spacing Scale, Primitive Typography Scale (+6 more)

### Community 43 - "Social Media Banner Specs"
Cohesion: 0.16
Nodes (14): Banner Sizes and Styles Reference, 22 Art Direction Styles, CTA Design Principles, Print Banner Specifications, Banner Safe Zone Rules, Social Media Banner Dimensions, 3-Zone Visual Hierarchy Rule, Web & Display Ad Dimensions (+6 more)

### Community 45 - "UI UX Reasoning Contracts"
Cohesion: 0.21
Nodes (5): apply_decision_rules(), _object_without_duplicates(), parse_decision_rules(), _validate_action(), _check_reasoning_contract()

### Community 46 - "UI UX Data Contracts Tests"
Cohesion: 0.19
Nodes (3): read_rows(), TestLandingAndStackContract, TestReasoningContract

### Community 48 - "Continuous Audio Pipeline"
Cohesion: 0.22
Nodes (7): resume_continuous_endpoint(), continuous_generation_worker(), ensure_worker_running(), find_matching_character(), resume_continuous_generation(), start_continuous_generation(), call_gemini_chat()

### Community 49 - "Sound Effects & TTS Engine"
Cohesion: 0.15
Nodes (6): Migration, Migration, Migration, Migration, Migration, Migration

### Community 50 - "Tailwind Responsive Breakpoints"
Cohesion: 0.19
Nodes (13): HTML Slide Template, Chart.js Presentation Integration, Slide Transition & CSS Animations, Keyboard & Touch Slide Navigation, 16:9 Responsive Slide Deck Architecture, Token Architecture, Component Design Tokens, Dark Mode Token Overrides (+5 more)

### Community 52 - "Logo Design & Prompting"
Cohesion: 0.22
Nodes (4): _contrast_ratio(), _derive_dark_palette(), _select_palette_for_mode(), TestPaletteSelection

### Community 55 - "Typography Design Specifications"
Cohesion: 0.20
Nodes (12): Color System Hierarchy, Button Component Specification, Button Component Tokens, Primitive Color Scales, Semantic Color Tokens, State Priority Hierarchy, Component Classes via @layer components, CSS Variables Setup in @layer base (+4 more)

### Community 56 - "Brand Colors & Palettes"
Cohesion: 0.17
Nodes (12): Voice Consistency Audit, Core Statements Definitions, Messaging Framework, Messaging Framework Hierarchy, Message Architecture & Pitches, Message Testing Framework, Voice Development Process, Brand Voice Framework (+4 more)

### Community 57 - "Presentation Copywriting Formulas"
Cohesion: 0.27
Nodes (9): calculateCompliance(), colorDistance(), displayPalette(), extractHexColors(), findNearestBrandColor(), generateImageMagickCommand(), hexToRgb(), main() (+1 more)

### Community 58 - "CIP Prompt Engineering"
Cohesion: 0.32
Nodes (11): checkManifest(), formatBytes(), formatOutput(), main(), parseFilename(), RULES, suggestFilename(), validateAsset() (+3 more)

### Community 59 - "Font Pairing Recommendations"
Cohesion: 0.17
Nodes (12): CIP Style Guide, Bold Dynamic Style, CIP Color Psychology, Corporate Minimal Style, Luxury Premium Style, Modern Tech Style, Warm Organic Style, Logo Color Psychology (+4 more)

### Community 60 - "UI Component Design Rules"
Cohesion: 0.17
Nodes (12): Slides Knowledge Base Index, Slide Layout Patterns Reference, 25 Slide Layout Catalog, Slide Component Card Variants, Slide Responsive Grid Structures, Slide Layout Decision Flow, Presentation Design Workflow, Strategic Slides Module (+4 more)

### Community 61 - "UI UX Search Evaluation"
Cohesion: 0.22
Nodes (11): Brand Color Presets, Brand Update Workflow Reference, 5-Step Brand Update Workflow, Brand Sync Workflow, Brand Skill, Brand Update Subcommand, Component Spec Pattern, Design System Skill (+3 more)

### Community 62 - "Script Extraction & Splitter"
Cohesion: 0.18
Nodes (11): CIP Mockup Prompt Engineering, CIP Base Prompt Formula, Deliverable-Specific Modifiers, Photorealistic Lighting Modifiers, CIP Negative Prompting, CIP Style Modifiers, Logo Prompt Engineering, Logo Core Prompt Formula (+3 more)

### Community 63 - "Brand Voice Framework"
Cohesion: 0.18
Nodes (11): Design Routing Guide, Design Domain Routing Engine, Multi-Skill Workflow Orchestration, Design Skill Dependency Pipeline, Task-Based Selection Matrix, Icon Design Reference, 12 Icon Category Matrix, 15 Icon Style Taxonomy (+3 more)

### Community 67 - "Brand Approval Checklist"
Cohesion: 0.20
Nodes (10): Visual Elements Compliance Checklist, Color Extraction via K-means, Brand Color Compliance Validation, WCAG 2.1 Color Contrast Requirements, Color Palette Management Guide, Logo Clear Space Specification, Typography CSS Variables System, Typography Specifications (+2 more)

### Community 68 - "Token Embedding Engine"
Cohesion: 0.20
Nodes (6): args, minimal, MINIMAL_TOKENS, projectRoot, tokensPath, wrapStyle

### Community 69 - "Design Token Validator"
Cohesion: 0.31
Nodes (9): extensions, formatReport(), getFiles(), main(), parseArgs(), patterns, scanFile(), shouldSkip() (+1 more)

### Community 70 - "Animation Duration Tokens"
Cohesion: 0.20
Nodes (10): fast, normal, slow, $type, $value, $type, $value, duration (+2 more)

### Community 72 - "Brand Consistency Checklist"
Cohesion: 0.22
Nodes (9): Brand Audit Frequency Schedule, Cross-Channel Brand Audit, Brand Consistency Checklist, Visual Consistency Audit, Brand Font Stack Structure, Core Visual Identity Elements, Visual Identity Basics, Visual Guidelines Template Structure (+1 more)

### Community 73 - "Brand Context Injector"
Cohesion: 0.42
Nodes (8): extractColorsFromTable(), extractCoreAttributes(), extractHexColors(), extractImageStyle(), extractTypography(), extractVoice(), generatePromptAddition(), main()

### Community 74 - "Logo Design Principles"
Cohesion: 0.22
Nodes (9): Logo Design Reference, 55+ Logo Style Taxonomy, Logo Design Brief Generator, HTML Gallery Preview Integration, Logo Style Guide, Aesthetic Logo Categories, 7 Core Logo Types, Logo Scalability Checklist (+1 more)

### Community 75 - "Slide Copywriting Frameworks"
Cohesion: 0.28
Nodes (9): Slides Copywriting Formulas Reference, Slide Headline Patterns, Persuasive Presentation Formulas, Formula-to-Emotion Mapping, Presentation Emotion Arc Engineering, Copywriting Formulas Reference, Slide Headline Patterns Framework, Slide Copywriting Framework (+1 more)

### Community 77 - "UI Styling Library Core"
Cohesion: 0.25
Nodes (8): Apache License 2.0 Document, Apache 2.0 License Terms and Conditions, UI Styling CLI Automation Scripts, UI Styling Ten Best Practices, Canvas Visual Design Architecture Layer, UI Styling Skill Specification, shadcn/ui Component Architecture Layer, Tailwind CSS Utility Styling Layer

### Community 78 - "Brand Token Synchronizer"
Cohesion: 0.39
Nodes (5): adjustBrightness(), extractColorsFromMarkdown(), generateColorScale(), main(), updateDesignTokens()

### Community 79 - "Design Token Generator CLI"
Cohesion: 0.50
Nodes (7): flattenTokens(), generateCSS(), generateTailwind(), main(), parseArgs(), resolveReference(), toCssVarName()

### Community 80 - "Font Size Semantic Tokens"
Cohesion: 0.29
Nodes (8): xl, $type, $value, radius, full, xl, $type, $value

### Community 84 - "Shadcn Accessibility Guidelines"
Cohesion: 0.29
Nodes (7): WCAG AA and AAA Color Contrast Standards, shadcn/ui Accessibility Patterns Reference, Accessible Form Validation and Descriptions, Keyboard Navigation and Focus Trap Management, Radix UI WAI-ARIA Primitives Foundation, Prefers-Reduced-Motion Responsive Adaptation, Screen Reader Support, ARIA Labels, and Live Regions

### Community 85 - "UI UX Application Rules"
Cohesion: 0.29
Nodes (7): Professional App UI Rules and Pre-Delivery Checklist, Design Dials Tuning (Variance, Motion, Density), Automated Design System Generation, UI/UX Pro Max Skill Specification, Specialized UI Search Domains, Master Plus Overrides Design Persistence Pattern, Intent-Driven Query Contract

### Community 86 - "CIP Deliverables Reference"
Cohesion: 0.29
Nodes (7): CIP Deliverable Guide, Corporate Apparel & Uniforms, Core Identity Deliverables, Digital Brand Assets, Office Environment & Signage, Corporate Stationery Suite, Fleet & Vehicle Branding

### Community 89 - "Canvas Design System Principles"
Cohesion: 0.33
Nodes (6): Visual Communication Core Principles, Canvas Design System Reference Guide, Canvas Aesthetic Design Movements, Multi-Page Coffee Table Book Design Systems, Museum-Quality Visual Standards and Verification, Two-Phase Canvas Design Workflow

### Community 90 - "Shadcn Component Display Specs"
Cohesion: 0.33
Nodes (6): shadcn Data Display Components Catalog, shadcn/ui Component Catalog Reference, shadcn Feedback and Status Components Catalog, shadcn Form and Input Components Catalog, shadcn Layout and Navigation Components Catalog, shadcn Overlays, Dialogs, and Drawers Catalog

### Community 91 - "Tailwind Apply Directives"
Cohesion: 0.33
Nodes (6): Tailwind @apply Directive Extraction Pattern, Tailwind Custom Utilities and Custom Variants, Tailwind CSS Customization Reference, CSS Layer Organization (@layer base, components, utilities), Tailwind Official and Custom Plugins, Tailwind v4 @theme Directive Architecture

### Community 92 - "Tailwind Arbitrary Values"
Cohesion: 0.33
Nodes (6): Tailwind Arbitrary Value Syntax, Tailwind Color Scale, Gradients, and Opacity Modifiers, Tailwind CSS Utility Classes Reference, Tailwind Flexbox and Grid Layout Utilities, Tailwind Spacing Scale System, Tailwind Typography Utilities

### Community 93 - "Slide Deck Generator References"
Cohesion: 0.33
Nodes (6): Slides Create Invocation Bridge, Slides Delegation Bridge, Slides Skill, Slides Subcommand Router, Slides Knowledge Base Architecture, Standalone Slides Presentation Skill

### Community 94 - "Small Font Size Tokens"
Cohesion: 0.47
Nodes (6): sm, shadow, sm, sm, $type, $value

### Community 96 - "Data Contract Splitter Tests"
Cohesion: 0.47
Nodes (3): split_values(), style_identities(), TestStyleIdentityContract

### Community 97 - "Shadcn Theming & CSS Variables"
Cohesion: 0.40
Nodes (5): shadcn/ui HSL CSS Variable System, CVA Component Variant Customization, Next.js and next-themes Dark Mode Setup, shadcn/ui Theming and Customization Reference, Tailwind Config Theme Mapping

### Community 98 - "Tailwind Container Queries"
Cohesion: 0.40
Nodes (5): CSS Container Queries in Tailwind (@container), Tailwind CSS Responsive Design Reference, Max-Width and Range Responsive Queries, Mobile-First Breakpoint Architecture, Responsive Layout Patterns (Sidebar, Grid, Hero)

### Community 99 - "Large Font Size Tokens"
Cohesion: 0.60
Nodes (5): lg, $type, $value, lg, lg

### Community 102 - "AI Audio Drama Engine Readme"
Cohesion: 0.40
Nodes (5): Gemini 3.8 Flash and LangGraph Dramatization Pipeline, HexMedia Audio Drama Studio Platform, DesignCombo Multi-Track Montage Timeline, HexMedia Project README, HexMedia Microservices VPS Infrastructure

### Community 103 - "UI Styling Python Requirements"
Cohesion: 0.50
Nodes (4): UI Styling Scripts Requirements Document, UI Styling Python Standard Library and Node Environment, UI Styling Tests Requirements Document, Pytest Test Suite Dependencies

### Community 104 - "Design Tokens Starter Manifest"
Cohesion: 0.50
Nodes (3): dark, primitive, $schema

### Community 105 - "Default Component Variant Tokens"
Cohesion: 0.67
Nodes (4): $type, $value, default, default

### Community 106 - "Medium Token Variant Defaults"
Cohesion: 0.67
Nodes (4): $type, $value, md, md

### Community 107 - "Token Reset & None Variants"
Cohesion: 0.67
Nodes (4): $type, $value, none, none

## Knowledge Gaps
- **220 isolated node(s):** `@types/react`, `@types/react-dom`, `typescript`, `Step 1: Gather Requirements`, `Step 5: Present Options & Iterate` (+215 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 822 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **28 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `TailwindConfigGenerator` connect `Tailwind Styling Utilities` to `Visual Identity Guidelines`, `Tailwind Configuration Builder`, `Tailwind Generator Scripts`, `Brand Token Sync Tests`, `Tailwind Config Generator Logic`, `Tailwind CSS Output Rules`, `Tailwind Property Generator`, `Docker Compose Infrastructure`, `Tailwind Configuration Evaluator`, `Tailwind Config Unit Tests`?**
  _High betweenness centrality (0.052) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `TailwindConfigGenerator` (e.g. with `TestGeneratedConfigIsValidJs` and `TestTailwindConfigGenerator`) actually correct?**
  _`TailwindConfigGenerator` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `@types/react`, `@types/react-dom`, `typescript` to the rest of the system?**
  _220 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `UI UX Pro Max Quality Tests` be split into smaller, more focused modules?**
  _Cohesion score 0.06398390342052314 - nodes in this community are weakly interconnected._
- **Why does `ShadcnInstaller` connect `Shadcn Component Add CLI` to `Brand Token Sync Tests`?**
  _High betweenness centrality (0.019) - this node is a cross-community bridge._
- **Are the 27 inferred relationships involving `BookProject` (e.g. with `approve_casting_endpoint()` and `chat_endpoint()`) actually correct?**
  _`BookProject` has 27 INFERRED edges - model-reasoned connections that need verification._
- **Should `Shadcn Component Add CLI` be split into smaller, more focused modules?**
  _Cohesion score 0.053555750658472345 - nodes in this community are weakly interconnected._