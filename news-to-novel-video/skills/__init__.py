# skills module
from skills.scrape_news import scrape_toutiao_news
from skills.remove_pii import remove_pii
from skills.rewrite_novel import rewrite_as_novel
from skills.split_scenes import split_into_scenes
from skills.generate_audio import generate_audio
from skills.optimize_prompt import optimize_image_prompt
from skills.generate_images import generate_images
from skills.compose_video import compose_video
from skills.post_process import post_process_video
from skills.style_consistency import ensure_style_consistency