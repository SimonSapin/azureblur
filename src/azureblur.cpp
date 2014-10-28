#include "Blur.h"

using namespace mozilla::gfx;

extern "C" {
    int azureblur_new(void) {
        Rect rect;
        AlphaBoxBlur blur = AlphaBoxBlur(rect, 1, 1, 1);
        return 42;
    }
}
