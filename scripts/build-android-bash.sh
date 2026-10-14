#!/usr/bin/env bash
set -euo pipefail
project_dir="$(cd "$(dirname "$0")/.." && pwd)"
ndk_dir="${ANDROID_NDK_HOME:?Set ANDROID_NDK_HOME to Android NDK r27c}"
archive="$project_dir/third_party/bash-5.2.37.tar.xz"
expected=370704c9c859f4060b7df19055e43bb9b5fa09d887699cf6ba87885c5485d36a
if [ ! -f "$archive" ]; then
 curl --proto '=https' --tlsv1.2 -fL https://deb.debian.org/debian/pool/main/b/bash/bash_5.2.37.orig.tar.xz -o "$archive"
fi
printf '%s  %s\n' "$expected" "$archive" | sha256sum -c -
build_dir="$project_dir/native/build/bash-arm64"
mkdir -p "$build_dir"
tar -xf "$archive" -C "$build_dir"
cd "$build_dir/bash-5.2.37"
toolchain="$ndk_dir/toolchains/llvm/prebuilt/linux-x86_64/bin"
export CC="$toolchain/aarch64-linux-android26-clang"
export AR="$toolchain/llvm-ar" RANLIB="$toolchain/llvm-ranlib"
export CFLAGS='-O2 -fPIE -D__ANDROID__ -Wno-error=implicit-function-declaration -Wno-deprecated-non-prototype'
export LDFLAGS='-pie -Wl,-z,max-page-size=16384'
export bash_cv_dev_fd=standard bash_cv_dev_stdin=present bash_cv_dev_stdout=present bash_cv_dev_stderr=present
export bash_cv_getcwd_malloc=yes bash_cv_func_sigsetjmp=present bash_cv_job_control_missing=present
./configure --host=aarch64-linux-android --without-bash-malloc --disable-nls --disable-net-redirections --without-installed-readline > configure-binux.log 2>&1
make -j"${BUILD_JOBS:-4}" > make-binux.log 2>&1 || { tail -60 make-binux.log; exit 1; }
out="$project_dir/android/app/src/main/jniLibs/arm64-v8a"
mkdir -p "$out"
cp bash "$out/libbinux_bash.so"
"$toolchain/llvm-strip" "$out/libbinux_bash.so"
"$toolchain/llvm-readelf" -h -l "$out/libbinux_bash.so"
printf 'Bash ARM64 packaged at %s\n' "$out/libbinux_bash.so"
