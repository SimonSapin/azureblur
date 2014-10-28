#include "Blur.h"

using namespace mozilla::gfx;

extern "C" {
    #include "azureblur.h"

    AlphaBoxBlur* azureblur_new_from_radiuses(
        // Non-nullable
        const azureblur_rect* rect,
        const azureblur_intsize* spread_radius,
        const azureblur_intsize* blur_radius,
        // Nullable
        const azureblur_rect* dirty_rect,
        const azureblur_rect* skip_rect
    ) {
        Rect r(rect->x, rect->y, rect->width, rect->height);
        IntSize spread(spread_radius->width, spread_radius->height);
        IntSize blur(blur_radius->width, blur_radius->height);
        Rect* dirty = nullptr;
        if (dirty_rect) {
            Rect dirty_(dirty_rect->x, dirty_rect->y,
                        dirty_rect->width, dirty_rect->height);
            dirty = &dirty_;
        }
        Rect* skip = nullptr;
        if (skip_rect) {
            Rect skip_(skip_rect->x, skip_rect->y,
                       skip_rect->width, skip_rect->height);
            skip = &skip_;
        }
        return new AlphaBoxBlur(r, spread, blur, dirty, skip);
    }

    AlphaBoxBlur* azureblur_new_from_sigma(
        const azureblur_rect* rect,  // Non-nullable
        int32_t stride,
        float sigma_x,
        float sigma_y
    ) {
        Rect r(rect->x, rect->y, rect->width, rect->height);
        return new AlphaBoxBlur(r, stride, sigma_x, sigma_y);
    }

    void azureblur_delete(AlphaBoxBlur* blur) {
        delete blur;
    }

    azureblur_intsize azureblur_get_size(AlphaBoxBlur* blur) {
        IntSize size = blur->GetSize();
        return { size.width, size.height };
    }

    int32_t azureblur_get_stride(AlphaBoxBlur* blur) {
        return blur->GetStride();
    }

    azureblur_intrect azureblur_get_rect(AlphaBoxBlur* blur) {
        IntRect r = blur->GetRect();
        return { r.x, r.y, r.width, r.height };
    }

    size_t azureblur_get_surface_allocation_size(const AlphaBoxBlur* blur) {
        return blur->GetSurfaceAllocationSize();
    }

    void azureblur_blur(AlphaBoxBlur* blur, uint8_t* data) {
        blur->Blur(data);
    }

    azureblur_intsize azureblur_calculate_blur_radius(float x, float y) {
        IntSize size = AlphaBoxBlur::CalculateBlurRadius({ x, y });
        return { size.width, size.height };
    }
}
