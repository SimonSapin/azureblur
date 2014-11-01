import os
import array
from azureblur import AlphaBoxBlur


def sample(filename):
    import cairocffi

    surface = cairocffi.ImageSurface(cairocffi.FORMAT_RGB24, 410, 100)
    context = cairocffi.Context(surface)
    context.set_source_rgb(1, 1, 1)
    context.paint()
    context.select_font_face('Chancery URW')
    context.set_font_size(100)
    context.set_source_rgb(0, .5, 1)
    context.move_to(10, 80)
    context.show_text('Azure ')

    blur = AlphaBoxBlur.from_radiuses(
        context.text_extents('blur')[:4], (0, 0), (5, 5))
    mask_data = array.array('B', b'\x00' * blur.get_surface_allocation_size())
    mask_x, mask_y, width, height = blur.get_rect()
    mask_surface = cairocffi.ImageSurface(
        cairocffi.FORMAT_A8, width, height, mask_data, blur.get_stride())
    mask_context = cairocffi.Context(mask_surface)
    mask_context.move_to(-mask_x, -mask_y)
    mask_context.select_font_face('Chancery URW')
    mask_context.set_font_size(100)
    mask_context.show_text('blur')
    blur.blur_array(mask_data)

    x, y = context.get_current_point()
    context.set_source_rgb(.5, .5, .5)
    context.mask_surface(mask_surface, x + 5 + mask_x, y + 5 + mask_y)

    context.set_source_rgb(0, .5, 1)
    context.show_text('blur')
    surface.write_to_png(filename)


if __name__ == '__main__':
    sample(
        os.path.join(os.path.dirname(os.path.dirname(__file__)),
        'sample.png'))
