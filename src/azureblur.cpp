#include "mozilla/gfx/Blur.h"

using namespace mozilla::gfx;

extern "C" {
    int azureblur_new() {
        Rect rect;
        AlphaBoxBlur blur = AlphaBoxBlur(nullptr, rect, 1, 1);
        return 42;
    }
}
