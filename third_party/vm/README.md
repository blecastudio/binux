# APK-managed Linux VM engine sources

`sources.json` lists actual origin URLs and SHA-256 values for every source archive.
QEMU 9.2.4 is built as a standalone ARM64 Android PIE named `libbinux_vm.so`.
It is executed from Android's package-managed native library directory. It is
not linked into the GPLv3 Android UI. QEMU's GPLv2 license and all source headers
remain in its complete source archive. Guest kernels/disks are data interpreted
by the emulator; downloaded guest executables are not executed by Android.

GLib 2.84.4: LGPL-2.1-or-later; PCRE2 10.45: BSD-style license; libffi 3.4.8:
MIT; libslirp 4.8.0: BSD-style license; libfdt 1.7.2: BSD-2-Clause (its dual
license permits this choice). Full sources, notices and build recipes accompany
the standalone emulator. Keycodemapdb/SoftFloat/TestFloat pinned upstream source
archives are included; their individual notices remain in each archive.

The Bionic stat macro patch is adapted from termux-packages commit
627a811d9fcacb67ae9e94718a6b33d3c01e6148 (`0003-fix-time_nsec-defs.patch`).
The shared-memory build patch checks for a real `shm_open` function rather than
compiling an unsupported backend on Android. The libffi configure edit sets
AArch64's symbol prefix explicitly for libtool 2.5 compatibility. No SELinux,
Android target-SDK, linker, execute-permission or privileged system policy bypass
is part of the build. TCG uses separate writable/executable JIT mappings.

Build on Linux with JDK21, Android NDK r27c, gcc/make, CMake, pkg-config,
autoconf/automake/libtool, bison/flex/m4, Python3.12, Meson1.6.1 and Ninja:

```
export ANDROID_NDK_HOME="$ANDROID_HOME/ndk/27.2.12479018"
python3 -m pip install meson==1.6.1 ninja==1.11.1.1
bash scripts/build-android-vm.sh
```

API31+ is required to launch the engine. The native Bash terminal still supports
API26+. Android ARM64 device execution, JIT compatibility and OEM background
policies require device tests; a successful NDK build is not that evidence.

The Android DNS patch forwards virtual DNS to a loopback UDP/TCP broker using the public Android DnsResolver API, preserving Private DNS/VPN selection. It does not install or select a public DNS server. A virtio RNG device supplies real host-kernel entropy to the guest.
