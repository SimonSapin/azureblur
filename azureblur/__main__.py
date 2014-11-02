# coding: utf8
import os
import array
from azureblur import AlphaBoxBlur


def sample(filename):
    import cairocffi

    background_color = (1, 1, 1)
    font_family = 'Chancery URW'
    font_size = 100
    text_color = (0, .5, 1)
    shadow_color = (.5, .5, .5)
    shadow_offset_x = 5
    shadow_offset_y = 5
    shadow_blur_radius = (5, 5)
    shadow_spread_radius = (0, 0)

    surface = cairocffi.ImageSurface(cairocffi.FORMAT_RGB24, 410, 100)
    context = cairocffi.Context(surface)

    context.set_source_rgb(*background_color)
    context.paint()

    context.select_font_face(font_family)
    context.set_font_size(font_size)
    context.set_source_rgb(*text_color)
    context.move_to(10, 80)  # Left of the text’s baseline
    context.show_text('Azure ')

    blurred_text = 'blur'

    # (x, y, width, height) rectangle just big enough for the shadowed text,
    # positioned with the left of the text’s baseline at coordinates (0, 0).
    blurred_text_rect = context.text_extents(blurred_text)[:4]

    blur = AlphaBoxBlur.from_radiuses(
        blurred_text_rect, shadow_spread_radius, shadow_blur_radius)

    # blurred_text_rect inflated to leave space for spread and blur.
    mask_x, mask_y, mask_width, mask_height = blur.get_rect()

    mask_data = array.array('B', b'\x00' * blur.get_surface_allocation_size())

    mask_surface = cairocffi.ImageSurface(
        cairocffi.FORMAT_A8,  # Single channel, one byte per pixel.
        mask_width, mask_height, mask_data, blur.get_stride())
    mask_context = cairocffi.Context(mask_surface)
    mask_context.move_to(-mask_x, -mask_y)  # Left of the text’s baseline
    mask_context.select_font_face(font_family)
    mask_context.set_font_size(font_size)
    mask_context.show_text(blurred_text)

    blur.blur_array(mask_data)

    # Position after showing 'Azure ': right of its baseline.
    current_x, current_y = context.get_current_point()

    context.set_source_rgb(*shadow_color)
    context.mask_surface(
        mask_surface,
        current_x + shadow_offset_x + mask_x,
        current_y + shadow_offset_x + mask_y)

    context.set_source_rgb(*text_color)
    context.show_text(blurred_text)
    surface.write_to_png(filename)


if __name__ == '__main__':
    sample(
        os.path.join(os.path.dirname(os.path.dirname(__file__)),
        'sample.png'))
