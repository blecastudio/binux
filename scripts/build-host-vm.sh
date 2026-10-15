#!/usr/bin/env bash
# Validate with the same QEMU sources/options as the APK; no installed firmware.
set -euo pipefail
root=$(cd "$(dirname "$0")/.." && pwd)
python3 "$root/scripts/prepare-vm.py"
work="$root/native/build/vm-host"
mkdir -p "$work"
cd "$work"
"$root/native/build/vm/sources/qemu-9.2.4/configure" --cc=gcc --cxx=g++ \
 --target-list=aarch64-softmmu --without-default-features --enable-system \
 --enable-tcg --enable-slirp --enable-virtfs --enable-attr --enable-fdt=system \
 --disable-guest-agent --disable-tools --disable-docs --disable-werror \
 --disable-download --disable-modules --audio-drv-list= --enable-trace-backends=nop
ninja -j"${BUILD_JOBS:-2}" qemu-system-aarch64
strip qemu-system-aarch64
./qemu-system-aarch64 --version
