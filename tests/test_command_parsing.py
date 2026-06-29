from plugins.image_generation import extract_image_prompt
from plugins.video_generation import extract_video_prompt


def test_extract_image_prompt_accepts_draw_prefix():
    assert extract_image_prompt("画个赛博猫") == "赛博猫"
    assert extract_image_prompt("画一个月亮") == "月亮"
    assert extract_image_prompt("生成图片 山水") == "山水"


def test_extract_video_prompt_accepts_requested_prefix():
    assert extract_video_prompt("生成视频星空航行") == "星空航行"
    assert extract_video_prompt("做视频 城市延时") == "城市延时"
