#!/usr/bin/env bash
# Build the APK-managed VM engine. Guest programs execute in its virtual kernel.
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
ndk="${ANDROID_NDK_HOME:?Set ANDROID_NDK_HOME}"
tool="$ndk/toolchains/llvm/prebuilt/linux-x86_64/bin"
work="$root/native/build/vm"
prefix="$work/install"
src="$work/sources"
mkdir -p "$prefix/lib/pkgconfig" "$src" "$work/ffi" "$work/pcre" "$work/glib" "$work/slirp" "$work/dtc" "$work/qemu"
python3 "$root/scripts/prepare-vm.py"
export CC="$tool/aarch64-linux-android31-clang" CXX="$tool/aarch64-linux-android31-clang++" AR="$tool/llvm-ar" RANLIB="$tool/llvm-ranlib" STRIP="$tool/llvm-strip"
export CFLAGS='-O2 -fPIC' CXXFLAGS='-O2 -fPIC' LDFLAGS='-Wl,-z,max-page-size=16384'
export NM="$tool/llvm-nm" READELF="$tool/llvm-readelf"
export PKG_CONFIG=pkg-config
export PKG_CONFIG_LIBDIR="$prefix/lib/pkgconfig" PKG_CONFIG_PATH="$prefix/lib/pkgconfig"
cat > "$work/android.ini" <<CROSS
[binaries]
c = '$CC'
cpp = '$CXX'
ar = '$AR'
strip = '$STRIP'
pkg-config = 'pkg-config'
[properties]
needs_exe_wrapper = true
[host_machine]
system = 'android'
cpu_family = 'aarch64'
cpu = 'aarch64'
endian = 'little'
[built-in options]
c_args = ['-O2', '-fPIC']
cpp_args = ['-O2', '-fPIC']
c_link_args = ['-Wl,-z,max-page-size=16384']
cpp_link_args = ['-Wl,-z,max-page-size=16384']
CROSS
cat > "$prefix/lib/pkgconfig/zlib.pc" <<PC
prefix=$prefix
Name: zlib
Description: Android system zlib
Version: 1.2.13
Libs: -lz
PC
if [[ ! -f "$prefix/lib/libffi.a" ]]; then
 if [[ ! -x "$src/libffi-3.4.8/configure" ]];then (cd "$src/libffi-3.4.8"; autoreconf --force --install);fi
 (cd "$work/ffi"; "$src/libffi-3.4.8/configure" --host=aarch64-linux-android --prefix="$prefix" --libdir="$prefix/lib" --disable-shared --enable-static --disable-docs; make -j"${BUILD_JOBS:-4}";make install)
fi
if [[ ! -f "$prefix/lib/libpcre2-8.a" ]]; then
 cmake -S "$src/pcre2-10.45" -B "$work/pcre" -DCMAKE_TOOLCHAIN_FILE="$ndk/build/cmake/android.toolchain.cmake" -DANDROID_ABI=arm64-v8a -DANDROID_PLATFORM=android-31 -DCMAKE_INSTALL_PREFIX="$prefix" -DCMAKE_INSTALL_LIBDIR=lib -DBUILD_SHARED_LIBS=OFF -DPCRE2_BUILD_TESTS=OFF -DPCRE2_BUILD_PCRE2GREP=OFF
 cmake --build "$work/pcre" -j"${BUILD_JOBS:-4}";cmake --install "$work/pcre"
fi
if [[ ! -f "$prefix/lib/libglib-2.0.a" ]]; then
 meson setup "$work/glib" "$src/glib-2.84.4" --cross-file "$work/android.ini" --prefix "$prefix" --libdir lib --default-library static -Dtests=false -Dinstalled_tests=false -Ddocumentation=false -Dman-pages=disabled -Dintrospection=disabled -Dnls=disabled -Dlibmount=disabled -Dselinux=disabled -Dlibelf=disabled
 meson compile -C "$work/glib" -j"${BUILD_JOBS:-4}";meson install -C "$work/glib"
fi
if [[ ! -f "$prefix/lib/libslirp.a" || "$src/libslirp-v4.8.0/src/socket.c" -nt "$prefix/lib/libslirp.a" ]]; then
 meson setup "$work/slirp" "$src/libslirp-v4.8.0" --cross-file "$work/android.ini" --prefix "$prefix" --libdir lib --default-library static
 meson compile -C "$work/slirp" -j"${BUILD_JOBS:-4}";meson install -C "$work/slirp"
fi
if [[ ! -f "$prefix/lib/libfdt.a" ]]; then
 make -C "$src/dtc-1.7.2" -j"${BUILD_JOBS:-4}" CC="$CC" AR="$AR" PREFIX="$prefix" CFLAGS="-O2 -fPIC -Wno-unknown-warning-option" NO_PYTHON=1 NO_YAML=1 libfdt/libfdt.a
 cp "$src/dtc-1.7.2/libfdt/libfdt.a" "$prefix/lib/"
 mkdir -p "$prefix/include";cp "$src/dtc-1.7.2/libfdt/"{fdt.h,libfdt.h,libfdt_env.h} "$prefix/include/"
 cat > "$prefix/lib/pkgconfig/libfdt.pc" <<PC
prefix=$prefix
Name: libfdt
Description: Flattened device tree library
Version: 1.7.2
Libs: -L$prefix/lib -lfdt
Cflags: -I$prefix/include
PC
fi
cd "$work/qemu"
"$src/qemu-9.2.4/configure" --cc="$CC" --cxx="$CXX" --host-cc=gcc --cross-prefix="$tool/aarch64-linux-android-" --prefix="$prefix" --target-list=aarch64-softmmu --without-default-features --enable-system --enable-tcg --enable-slirp --enable-virtfs --enable-attr --enable-fdt=system --disable-guest-agent --disable-tools --disable-docs --disable-werror --disable-download --extra-cflags="-I$prefix/include -fPIE" --extra-ldflags="-L$prefix/lib -pie -Wl,-z,max-page-size=16384" --audio-drv-list= --enable-trace-backends=nop
ninja -j"${BUILD_JOBS:-4}" qemu-system-aarch64
out="$root/android/app/src/main/jniLibs/arm64-v8a"
mkdir -p "$out"
cp qemu-system-aarch64 "$out/libbinux_vm.so"
"$STRIP" "$out/libbinux_vm.so"
"$tool/llvm-readelf" -d -l "$out/libbinux_vm.so"
