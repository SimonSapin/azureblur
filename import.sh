#!/bin/bash
# Usage: import.sh path/to/moz2d
# http://hg.mozilla.org/users/bschouten_mozilla.com/moz2d/

for filename in $(echo "
    Blur.cpp
    Blur.h
    Rect.h
    BaseRect.h
    mozilla/Assertions.h
    mozilla/Attributes.h
    mozilla/Compiler.h
    mozilla/Likely.h
    mozilla/MacroArgs.h
    mozilla/TypeTraits.h
    mozilla/Types.h
    mozilla/FloatingPoint.h
    mozilla/Casting.h
    mozilla/MathAlgorithms.h
    BaseMargin.h
    Types.h
    mozilla/NullPtr.h
    mozilla/TypedEnum.h
    mozilla/TypedEnumInternal.h
    Point.h
    Coord.h
    BaseCoord.h
    BasePoint.h
    mozilla/ToString.h
    BasePoint3D.h
    BasePoint4D.h
    BaseSize.h
    Tools.h
    mozilla/CheckedInt.h
    mozilla/IntegerTypeTraits.h
    mozilla/Constants.h
    mozilla/Util.h
    mozilla/Alignment.h
    2D.h
    DataSurfaceHelpers.h
    Matrix.h
    UserData.h
    GenericRefCounted.h
    mozilla/RefPtr.h
    mozilla/Atomics.h
    mozilla/RefCountType.h
    mozilla/DebugOnly.h
    DataSurfaceHelpers.cpp
    Logging.h
")
do
    mkdir -p $(dirname moz2d/$filename)
    cp $1/$filename moz2d/$filename
done
