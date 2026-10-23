import io
import json
import logging
import os
import re
import urllib.parse
import urllib.request
import uuid
from typing import Dict, Any, Optional
from google import genai
from google.genai import types

from .gemini_service import get_gemini_client
from .minio_service import upload_bytes

logger = logging.getLogger(__name__)

STYLE_PROMPTS = {
    'DOCUMENTARY': (
        "Authentic historical photograph, cinematic archival documentary still, "
        "National Geographic style, 8k realistic details, authentic lighting, 16:9 widescreen composition."
    ),
    'CARTOON': (
        "Pixar and Disney 3D animation style, cute character render, vibrant color palette, "
        "cinematic volumetric lighting, Octane 3D render, smooth textures, 16:9 widescreen composition."
    ),
    'CINEMATIC': (
        "Cinematic 35mm film still, dramatic movie scene, anamorphic lens, shallow depth of field, "
        "photorealistic, moody theatrical lighting, 8k resolution, 16:9 widescreen composition."
    ),
    'MANGA': (
        "High quality modern Japanese anime and manga panel, dynamic dramatic composition, "
        "crisp ink lineart, vivid cinematic colors, Makoto Shinkai aesthetic, 16:9 widescreen composition."
    ),
}

def enhance_visual_prompt(raw_prompt: str, style: str = 'AUTO', character_dna: str = '') -> str:
    cleaned = raw_prompt.strip()
    style_key = style.upper() if style else 'AUTO'
    
    style_suffix = STYLE_PROMPTS.get(style_key, STYLE_PROMPTS['CINEMATIC'])
    if style_key == 'AUTO':
        # Detect from words
        lower_p = cleaned.lower()
        if any(w in lower_p for w in ['وثائق', 'تاريخ', 'حرب', 'شاهد', 'معركة', 'حقيقة', 'documentary', 'history', 'war']):
            style_suffix = STYLE_PROMPTS['DOCUMENTARY']
        elif any(w in lower_p for w in ['كرتون', 'أطفال', 'أرنب', 'مضحك', 'رسوم', 'cartoon', 'pixar', 'disney', 'cute']):
            style_suffix = STYLE_PROMPTS['CARTOON']
        elif any(w in lower_p for w in ['مانجا', 'أنمي', 'كوميك', 'manga', 'anime', 'comic']):
            style_suffix = STYLE_PROMPTS['MANGA']
        else:
            style_suffix = STYLE_PROMPTS['CINEMATIC']

    dna_part = f" Main character visual traits: {character_dna.strip()}." if character_dna else ""
    return f"{cleaned}.{dna_part} Style: {style_suffix} Highly detailed, no watermarks, masterpiece."

WIKIMEDIA_COOLDOWN_UNTIL = 0.0

def search_wikimedia_archive(query: str) -> Optional[str]:
    """Search Wikimedia Commons for authentic public domain documentary images."""
    global WIKIMEDIA_COOLDOWN_UNTIL
    if time.time() < WIKIMEDIA_COOLDOWN_UNTIL:
        return None

    try:
        # Extract candidate keywords for reliable Wikimedia search
        fillers = {
            'cinematic', 'aerial', 'drone', 'wide', 'shot', 'sweeping', 'over', 'during',
            'the', 'of', 'and', 'in', 'at', '8k', 'photorealistic', 'style', 'high', 'end',
            'texture', 'lighting', 'dramatic', 'close', 'up', 'medium', 'view', 'background',
            'foreground', 'macro', 'historical', 'archival', 'reconstruction', 'documentary',
            'detailed', 'watermarks', 'masterpiece', 'main', 'character', 'traits'
        }
        words = [w for w in re.findall(r'[a-zA-Z]{3,}', query) if w.lower() not in fillers]
        candidate_queries = []
        if len(words) >= 2:
            candidate_queries.append(" ".join(words[:2]))
        if words:
            candidate_queries.append(words[0])

        for candidate in candidate_queries:
            clean_query = re.sub(r'[^\w\s]', ' ', candidate).strip()
            if not clean_query:
                continue
            encoded = urllib.parse.quote(clean_query)
            api_url = (
                f"https://commons.wikimedia.org/w/api.php?action=query&generator=search"
                f"&gsrsearch={encoded}&gsrnamespace=6&gsrlimit=3&prop=imageinfo&iiprop=url|mime"
                f"&format=json"
            )
            req = urllib.request.Request(
                api_url,
                headers={'User-Agent': 'HexMediaStudioBot/1.0 (https://hexmedia.ai; support@hexmedia.ai)'}
            )
            try:
                with urllib.request.urlopen(req, timeout=4) as response:
                    data = json.loads(response.read().decode('utf-8'))
                    pages = data.get('query', {}).get('pages', {})
                    for page_id, page_info in pages.items():
                        imageinfo = page_info.get('imageinfo', [])
                        if imageinfo:
                            img_url = imageinfo[0].get('url', '')
                            mime = imageinfo[0].get('mime', '')
                            if mime in ['image/jpeg', 'image/png', 'image/webp'] and img_url:
                                with urllib.request.urlopen(urllib.request.Request(img_url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=6) as img_resp:
                                    img_bytes = img_resp.read()
                                    obj_name = f"archives/wiki_{uuid.uuid4().hex[:10]}.jpg"
                                    uploaded = upload_bytes(img_bytes, obj_name, "image/jpeg")
                                    logger.info(f"✅ Found Wikimedia archive image for '{candidate}': {uploaded}")
                                    return uploaded
            except urllib.error.HTTPError as he:
                if he.code == 429:
                    logger.warning("Wikimedia API 429 Too Many Requests received. Enabling 10-minute cooldown and falling back directly to Gemini AI image generation.")
                    WIKIMEDIA_COOLDOWN_UNTIL = time.time() + 600
                    return None
                continue
    except Exception as e:
        logger.warning(f"Wikimedia search notice for '{query[:40]}': {e}")
    return None

def generate_ai_image(prompt: str, scene_id: str) -> Optional[str]:
    """Generate 16:9 cinematic image via Google Gemini Developer API (gemini-3.1-flash-lite-image / gemini-2.5-flash-image)."""
    client, config = get_gemini_client()
    if not client:
        logger.warning("No Gemini Client available for image generation")
        return None

    models_to_try = ['gemini-3.1-flash-lite-image', 'gemini-2.5-flash-image']
    for model_name in models_to_try:
        try:
            logger.info(f"Generating image with {model_name} for scene {scene_id}...")
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE"],
                    image_config=types.ImageConfig(aspect_ratio="16:9")
                )
            )
            if response and response.parts:
                for part in response.parts:
                    if part.inline_data and part.inline_data.data:
                        obj_name = f"visuals/scene_{scene_id}_{uuid.uuid4().hex[:8]}.jpg"
                        minio_url = upload_bytes(part.inline_data.data, obj_name, "image/jpeg")
                        logger.info(f"✅ Image generated successfully with {model_name}: {minio_url}")
                        return minio_url
        except Exception as e:
            logger.warning(f"Model {model_name} failed: {e}")
            continue

    return None

def generate_fallback_cinematic_card(prompt: str, scene_id: str, style: str = 'CINEMATIC') -> str:
    """Generate an elegant, high-contrast dark visual SVG poster card if all remote generation is unavailable."""
    clean_p = prompt[:120].replace('"', "'")
    palette = {
        'DOCUMENTARY': ('#131a1c', '#2c3e50', '#d4af37', 'DOCUMENTARY ARCHIVE'),
        'CARTOON': ('#1e142e', '#4a154b', '#e2ff44', '3D ANIMATION'),
        'MANGA': ('#0d0e15', '#1e2238', '#ffffff', 'MANGA PANEL'),
        'CINEMATIC': ('#0c0d12', '#1a1c24', '#e2ff44', 'CINEMATIC SCENE'),
    }
    bg1, bg2, accent, badge = palette.get(style.upper(), palette['CINEMATIC'])
    
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1920 1080" width="1920" height="1080">
      <defs>
        <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="{bg1}" />
          <stop offset="100%" stop-color="{bg2}" />
        </linearGradient>
        <radialGradient id="glow" cx="50%" cy="50%" r="60%">
          <stop offset="0%" stop-color="{accent}" stop-opacity="0.18" />
          <stop offset="100%" stop-color="{accent}" stop-opacity="0" />
        </radialGradient>
      </defs>
      <rect width="1920" height="1080" fill="url(#grad)" />
      <rect width="1920" height="1080" fill="url(#glow)" />
      <rect x="60" y="60" width="1800" height="960" fill="none" stroke="{accent}" stroke-width="2" stroke-opacity="0.25" rx="32" />
      <g transform="translate(120, 140)">
        <rect width="260" height="48" rx="24" fill="{accent}" fill-opacity="0.15" stroke="{accent}" stroke-opacity="0.5" stroke-width="1.5" />
        <text x="130" y="32" fill="{accent}" font-family="monospace" font-size="20" font-weight="bold" text-anchor="middle" letter-spacing="3">{badge}</text>
      </g>
      <text x="120" y="520" fill="#FFFFFF" font-family="system-ui, sans-serif" font-size="52" font-weight="600" width="1600">{clean_p}</text>
      <text x="120" y="960" fill="#71717A" font-family="monospace" font-size="24">HEXMEDIA STUDIO • 16:9 ULTRA HD</text>
    </svg>"""
    obj_name = f"visuals/fallback_{scene_id}_{uuid.uuid4().hex[:6]}.svg"
    return upload_bytes(svg.encode('utf-8'), obj_name, "image/svg+xml")

def produce_scene_visual(
    scene_id: str, 
    raw_prompt: str, 
    visual_style: str = 'AUTO', 
    character_dna: str = '',
    force_archive: bool = False
) -> Dict[str, Any]:
    """
    Main entry point: Coordinates between Archive Web Search and Imagen 3 AI Generation.
    """
    enhanced = enhance_visual_prompt(raw_prompt, visual_style, character_dna)
    style_key = visual_style.upper() if visual_style else 'AUTO'
    
    # 1. If Documentary mode or force_archive, try historical/archive search first
    if force_archive or style_key == 'DOCUMENTARY':
        archive_url = search_wikimedia_archive(raw_prompt)
        if archive_url:
            return {
                "image_url": archive_url,
                "media_type": "ARCHIVE_WEB",
                "visual_prompt": enhanced,
                "motion_type": "zoom_in"
            }

    # 2. Try Google Imagen 3 / Gemini Generation
    ai_img_url = generate_ai_image(enhanced, scene_id)
    if ai_img_url:
        return {
            "image_url": ai_img_url,
            "media_type": "AI_IMAGE",
            "visual_prompt": enhanced,
            "motion_type": "zoom_in"
        }

    # 3. If Documentary and AI generation failed, try archive as fallback
    if style_key != 'DOCUMENTARY':
        archive_url = search_wikimedia_archive(raw_prompt)
        if archive_url:
            return {
                "image_url": archive_url,
                "media_type": "ARCHIVE_WEB",
                "visual_prompt": enhanced,
                "motion_type": "pan_left"
            }

    # 4. Fallback procedural visual card
    fallback_url = generate_fallback_cinematic_card(raw_prompt, scene_id, style_key)
    return {
        "image_url": fallback_url,
        "media_type": "AI_IMAGE",
        "visual_prompt": enhanced,
        "motion_type": "static"
    }
