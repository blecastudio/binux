# Open-source notices and changes

binux source is distributed under GPL-3.0-only. Source archives and licenses must accompany releases.

* Termux app terminal-emulator and terminal-view: v0.118.0, commit `6e2689f55295fa444be8ac8592c527c2c5ef3253`; https://github.com/termux/termux-app. Upstream LICENSE.md is preserved as TERMUX-LICENSE.md. GPLv3-only with documented Apache-2.0 exceptions; source headers are preserved. binux does not use Termux's package repository or application bootstrap.
* binux modifications to TerminalSession.java: public ParcelFileDescriptor duplication and separately owned input/output streams replace hidden FileDescriptor reflection. Changes to termux.c close the PTY on failed initialization and abort on failed chdir. Gradle files use the binux SDK/NDK versions and 16 KiB linker alignment. Other emulator/view code is preserved.
* GNU Bash 5.2.37: source archive `bash-5.2.37.tar.xz`, GPLv3-or-later, packaged as an ARM64 PIE in the APK. Archive downloaded over HTTPS from https://deb.debian.org/debian/pool/main/b/bash/bash_5.2.37.orig.tar.xz. SHA-256 `370704c9c859f4060b7df19055e43bb9b5fa09d887699cf6ba87885c5485d36a`. The checksum pins the downloaded source; it is not a publisher signature claim. Full source is included, with cross-build options in scripts/build-android-bash.sh. The build relaxes Clang's implicit-declaration error for the old bundled termcap source; inspect compiler logs and test the result on a device before release.
* xterm.js 5.5.0, addon-fit 0.10.0, addon-search 0.15.0: MIT. Corresponding full npm source archives are included in this directory. Copies of their MIT licenses are in windows/assets. Assets are local and never loaded from a CDN. package-lock.json records registry integrity values.
* AndroidX/Compose/Room/DataStore: Apache-2.0. Kotlin: Apache-2.0. PRoot is an optional external dependency under GPL-2.0-or-later; no Android PRoot executable is distributed by this version. Debian, Ubuntu and XFCE licenses apply separately to packages installed by their package managers.
* Microsoft WebView2 SDK/Runtime has Microsoft's license terms. Runtime is a user-installed prerequisite; review the NuGet package license before redistribution. Google Chrome is proprietary and is not included or redistributed.

Release a corresponding source archive, this notice, LICENSE, build scripts and third-party sources for every binary. Preserve per-file copyright headers. binux does not claim that third-party authors endorse BlecaStudio.

## Binux Desktop:X11 0.1.0

* Termux:X11 app/renderer/server build recipes: commit `6d627520b4717cdea1ed1530e6d063be7537cc8b` (2025-11-30), https://github.com/termux/termux-x11, GPLv3-or-later (use GPLv3 for this combined distribution). `android/desktop-x11/UPSTREAM-LICENSE` preserves its license. Upstream source headers and bundled Termux shared/extra-key source notices are retained.
* Binux changes: own Java/AIDL/JNI package `studio.bleca.binux.x11`, actual X server in a separate foreground Service, public Binder connection instead of app_process/hidden ActivityManager shell loader, same-signature read-only credential Provider, loopback TCP binding with mandatory Xauthority cookie, toolbar recovery button, Korean resources, original user-supplied logos, target35 and 16 KiB linker alignment. Termux preload and hardcoded runtime paths are removed from native startup. Inherited automatic accessibility activation is hidden and WRITE_SECURE_SETTINGS is not requested.
* X.Org Xserver 21.1.16, Pixman 0.44.0, libXfont 2.0.6, X11 client/authentication/transport/protocol/XKB sources, libtirpc, libepoxy, bzip2, xkb-data 2.42: corresponding complete source/data archives, origin URLs, pinned commits where available, and SHA-256 values are in `third_party/x11/`. Their individual COPYRIGHT/COPYING/LICENSE notices are inside the archives. X.Org/Pixman components primarily use MIT/X11 licenses; libtirpc uses BSD-style notices; bzip2 uses its preserved license; libepoxy uses MIT. Sources obtained from Debian over HTTPS replace inaccessible upstream submodule hosts; reviewed patches are adapted to exactly those versions. Do not remove third-party source archives from binary distributions' corresponding source.
* `scripts/prepare-x11.py` reconstructs verified sources. GNU gcc, bison, m4, patch and dpkg-deb are build tools, not included Android runtime executables. Google Chrome, XFCE and Linux distribution packages are not included in either APK.
* `branding/binux.png` and `branding/binux-desktop-x11.png` are supplied by the project owner for Binux branding. They are kept unchanged and not represented as third-party open-source artwork. The application source license does not grant unrelated use of BlecaStudio branding.

## binux 1.0.0 VM/SSH additions

* Standalone QEMU 9.2.4 and its full static dependencies: see `vm/README.md`, complete source archives and `vm/sources.json`. Preserve QEMU's GPLv2 license separately from the Android GPLv3 UI. Corresponding guest distribution sources and exact package/source versions are included with runtime image releases.
* mwiede JSch 0.2.26 (BSD-3-Clause) and net.i2p EdDSA 0.3.0 (CC0): complete source JARs, Maven origin URLs and SHA-256 hashes are in `ssh/`. Their per-file copyright/license headers are retained. These provide actual SSH public-key authentication and host-key verification, not an unauthenticated remote shell.
* X11 settings modifications remove protected-method reflection, preserve fragment categories after recreation and unregister observers. AndroidX public preference APIs are used instead.
* Optional desktop PCM playback uses Android's AudioTrack over an authenticated SSH channel. It does not disable the Linux browser sandbox or expose PulseAudio on the physical LAN.

Copies of VM dependency and SSH license texts are in `third_party/legal/` and
bundled in APK assets alongside this notice and the project license. Windows
publish output includes the project license/notice and the xterm component licenses.
