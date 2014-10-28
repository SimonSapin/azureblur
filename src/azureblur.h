struct azureblur_rect {
    float x;
    float y;
    float width;
    float height;
};

struct azureblur_intrect {
    int32_t x;
    int32_t y;
    int32_t width;
    int32_t height;
};

struct azureblur_intsize {
    int32_t width;
    int32_t height;
};

AlphaBoxBlur* azureblur_new_from_radiuses(
    // Non-nullable
    const struct azureblur_rect* rect,
    const struct azureblur_intsize* spread_radius,
    const struct azureblur_intsize* blur_radius,
    // Nullable
    const struct azureblur_rect* dirty_rect,
    const struct azureblur_rect* skip_rect
);

AlphaBoxBlur* azureblur_new_from_sigma(
    const struct azureblur_rect* rect,  // Non-nullable
    int32_t stride,
    float sigma_x,
    float sigma_y
);

void azureblur_delete(AlphaBoxBlur*);

struct azureblur_intsize azureblur_get_size(AlphaBoxBlur*);

int32_t azureblur_get_stride(AlphaBoxBlur*);

struct azureblur_intrect azureblur_get_rect(AlphaBoxBlur*);

// FIXME: GetDirtyRect return Rect*. Is it safe to cast to azureblur_rect* ?

size_t azureblur_get_surface_allocation_size(const AlphaBoxBlur*);

void azureblur_blur(AlphaBoxBlur*, uint8_t* data);

struct azureblur_intsize azureblur_calculate_blur_radius(float x, float y);
